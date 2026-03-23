"""
TestRail Mock Service - Main FastAPI Application

Key design decisions:
  • URL rewriting middleware maps real TestRail URL pattern
      GET  https://host/index.php?/api/v2/get_case/42
    to the internal FastAPI path
      GET  /index.php/api/v2/get_case/42
    so that route handlers can use ordinary path parameters.

  • Authentication: accepts HTTP Basic Auth (email:api_key) OR Bearer token.
    Set MOCK_AUTH_REQUIRED=true to enforce (any non-empty creds accepted).
"""

from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, Request, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uvicorn

from storage import get_database
from routes import api_router, MOCK_EMAIL, MOCK_API_KEY, _EXPECTED_BASIC
from models import (
    Project, Section, Template, TestCase, TestResult, TestRun, RunEntry,
    STATUS_NAMES, TYPE_NAMES, PRIORITY_NAMES,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

def _build_description() -> str:
    return f"""
## TestRail Mock Service — API v2

A fully-compatible TestRail API v2 mock for integration testing and training.

---

## 🔑 Authentication — Use ONLY These Credentials

> **All students must use the same fixed credentials below. No other email/API key will work.**

| Field | Value |
|-------|-------|
| **Email** | `{MOCK_EMAIL}` |
| **API Key** | `{MOCK_API_KEY}` |
| **Pre-computed Basic token** | `{_EXPECTED_BASIC}` |

### How to set the header

This mock follows the **exact same auth pattern as real TestRail**: HTTP Basic Auth where the
username is your email and the password is your API key.

```
Authorization: Basic {_EXPECTED_BASIC}
```

Which is `base64("{MOCK_EMAIL}:{MOCK_API_KEY}")`.

**Click the 🔒 Authorize button at the top-right, then enter:**
- Username: `{MOCK_EMAIL}`
- Password: `{MOCK_API_KEY}`

### Option 2 — Bearer Token *(convenience shortcut)*

You can also pass the API key directly as a Bearer token:

```
Authorization: Bearer {MOCK_API_KEY}
```

---

## 🌐 Real TestRail URL Pattern

All endpoints work as exact real TestRail URLs (with the `?` separator):

```
GET  http://localhost:4002/index.php?/api/v2/get_case/42
POST http://localhost:4002/index.php?/api/v2/add_case/1
POST http://localhost:4002/index.php?/api/v2/add_result_for_case/1/42
POST http://localhost:4002/index.php?/api/v2/add_results_for_cases/1
```

---

## 📋 Key Endpoints

| Action | Method | Path |
|--------|--------|------|
| Get test case | GET | `/index.php?/api/v2/get_case/{{case_id}}` |
| Get test cases | GET | `/index.php?/api/v2/get_cases/{{project_id}}` |
| Create test case | POST | `/index.php?/api/v2/add_case/{{section_id}}` |
| Update test case | POST | `/index.php?/api/v2/update_case/{{case_id}}` |
| Delete test case | POST | `/index.php?/api/v2/delete_case/{{case_id}}` |
| Add result for case | POST | `/index.php?/api/v2/add_result_for_case/{{run_id}}/{{case_id}}` |
| Bulk add results | POST | `/index.php?/api/v2/add_results_for_cases/{{run_id}}` |
| Get results | GET | `/index.php?/api/v2/get_results/{{test_id}}` |
| Create run | POST | `/index.php?/api/v2/add_run/{{project_id}}` |
| Get run | GET | `/index.php?/api/v2/get_run/{{run_id}}` |
| Close run | POST | `/index.php?/api/v2/close_run/{{run_id}}` |
"""


_DESCRIPTION = _build_description()

app = FastAPI(
    title="TestRail Mock Service",
    description=_DESCRIPTION,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


def _custom_openapi():
    """Inject HTTP Basic + Bearer security schemes into the OpenAPI spec."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    schema.setdefault("components", {})
    schema["components"]["securitySchemes"] = {
        "BasicAuth": {
            "type": "http",
            "scheme": "basic",
            "description": (
                f"HTTP Basic Auth (same as real TestRail). "
                f"Username = email, Password = API key. "
                f"**Fixed credentials for this mock** — "
                f"Username: `{MOCK_EMAIL}` / Password: `{MOCK_API_KEY}`. "
                f"Pre-computed header value: `Basic {_EXPECTED_BASIC}`"
            ),
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "description": (
                f"Convenience shortcut: pass the API key as a Bearer token. "
                f"Fixed token for this mock: `{MOCK_API_KEY}`"
            ),
        },
    }

    # Apply both schemes globally (either one satisfies auth)
    schema["security"] = [{"BasicAuth": []}, {"BearerAuth": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------------
# Middleware: rewrite  /index.php?/api/v2/...  →  /index.php/api/v2/...
# ---------------------------------------------------------------------------

@app.middleware("http")
async def rewrite_testrail_url(request: Request, call_next):
    """
    TestRail uses URLs like:  GET index.php?/api/v2/get_case/42
    In HTTP the part after '?' is the query string, so:
      path         = /index.php
      query_string = /api/v2/get_case/42

    Optionally there may be real query params appended with &:
      query_string = /api/v2/get_cases/34&limit=10&offset=5

    We rewrite this so FastAPI sees:
      path         = /index.php/api/v2/get_case/42
      query_string = (empty)          or limit=10&offset=5
    """
    path = request.scope.get("path", "")
    qs: bytes = request.scope.get("query_string", b"")
    qs_str = qs.decode("utf-8", errors="replace")

    if path == "/index.php" and qs_str.startswith("/api/v2/"):
        # Split the API path from any trailing key=value params
        parts = qs_str.split("&", 1)
        api_path = parts[0]          # e.g. /api/v2/get_case/42
        remaining = parts[1] if len(parts) > 1 else ""

        new_path = f"/index.php{api_path}"
        request.scope["path"] = new_path
        request.scope["raw_path"] = new_path.encode()
        request.scope["query_string"] = remaining.encode()

    return await call_next(request)


# Include API router AFTER middleware is registered
app.include_router(api_router)


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

STATUS_CLASSES = {
    1: "passed",
    2: "blocked",
    3: "untested",
    4: "retest",
    5: "failed",
}


def get_latest_case_statuses(db: Session, case_ids: List[int]) -> dict:
    latest = {}
    for cid in case_ids:
        r = (db.query(TestResult)
             .filter(TestResult.case_id == cid)
             .order_by(desc(TestResult.created_on))
             .first())
        if r:
            latest[cid] = r
    return latest


# ---------------------------------------------------------------------------
# UI Routes
# ---------------------------------------------------------------------------

@app.get("/ui", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_database)):
    try:
        project = db.query(Project).filter(Project.id == 1).first()
        if not project:
            project = Project(id=1, name="Demo Project", description="Sample project")
            db.add(project)
            db.commit()

        sections = db.query(Section).filter(Section.project_id == 1).all()
        section_case_counts = {}
        total_cases = 0
        for sec in sections:
            cnt = db.query(TestCase).filter(TestCase.section_id == sec.id).count()
            section_case_counts[sec.id] = cnt
            total_cases += cnt

        recent_results = (db.query(TestResult)
                          .join(TestCase)
                          .order_by(desc(TestResult.created_on))
                          .limit(10).all())

        test_runs = (db.query(TestRun)
                     .filter(TestRun.project_id == 1)
                     .order_by(desc(TestRun.created_on))
                     .limit(5).all())

        status_counts = {sid: 0 for sid in STATUS_NAMES}
        for r in recent_results:
            status_counts[r.status_id] = status_counts.get(r.status_id, 0) + 1

        stats = {"total_cases": total_cases, "overall_status_counts": status_counts}
    except Exception as e:
        print(f"Dashboard error: {e}")
        project = type("P", (), {"id": 1, "name": "Demo Project", "description": ""})()
        sections, section_case_counts, recent_results, test_runs = [], {}, [], []
        stats = {"total_cases": 0, "overall_status_counts": {sid: 0 for sid in STATUS_NAMES}}

    return templates.TemplateResponse("index.html", {
        "request": request,
        "project": project,
        "sections": sections,
        "section_case_counts": section_case_counts,
        "recent_results": recent_results,
        "test_runs": test_runs,
        "stats": stats,
        "status_names": STATUS_NAMES,
        "status_classes": STATUS_CLASSES,
    })


@app.get("/ui/cases", response_class=HTMLResponse)
def cases_list(
    request: Request,
    section_id: Optional[str] = Query(None),
    type_id: Optional[str] = Query(None),
    priority_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(25, le=100),
    db: Session = Depends(get_database),
):
    def to_int(v):
        try:
            return int(v) if v and str(v).strip() else None
        except (ValueError, TypeError):
            return None

    section_id_int = to_int(section_id)
    type_id_int = to_int(type_id)
    priority_id_int = to_int(priority_id)

    try:
        query = db.query(TestCase).join(Section).filter(Section.project_id == 1)
        if section_id_int:
            query = query.filter(TestCase.section_id == section_id_int)
        if type_id_int:
            query = query.filter(TestCase.type_id == type_id_int)
        if priority_id_int:
            query = query.filter(TestCase.priority_id == priority_id_int)
        if search:
            query = query.filter(TestCase.title.ilike(f"%{search}%"))

        total_cases = query.count()
        total_pages = max(1, (total_cases + limit - 1) // limit)
        cases = query.order_by(TestCase.id).offset((page - 1) * limit).limit(limit).all()

        sections = db.query(Section).filter(Section.project_id == 1).all()
        section_case_counts = {sec.id: db.query(TestCase).filter(TestCase.section_id == sec.id).count()
                                for sec in sections}
        case_statuses = get_latest_case_statuses(db, [c.id for c in cases])
    except Exception as e:
        print(f"Cases list error: {e}")
        cases, sections, section_case_counts, case_statuses = [], [], {}, {}
        total_cases, total_pages = 0, 1

    qp = "&".join(filter(None, [
        f"section_id={section_id_int}" if section_id_int else "",
        f"type_id={type_id_int}" if type_id_int else "",
        f"priority_id={priority_id_int}" if priority_id_int else "",
        f"search={search}" if search else "",
    ]))

    return templates.TemplateResponse("cases_list.html", {
        "request": request,
        "cases": cases,
        "sections": sections,
        "section_case_counts": section_case_counts,
        "case_statuses": case_statuses,
        "status_counts": {sid: 0 for sid in STATUS_NAMES},
        "total_cases": total_cases,
        "current_page": page,
        "total_pages": total_pages,
        "query_params": qp,
        "current_section_id": section_id_int,
        "current_type_id": type_id_int,
        "current_priority_id": priority_id_int,
        "search": search or "",
        "status_names": STATUS_NAMES,
        "type_names": TYPE_NAMES,
        "priority_names": PRIORITY_NAMES,
        "status_classes": STATUS_CLASSES,
    })


@app.get("/ui/case/{case_id}", response_class=HTMLResponse)
def case_detail(request: Request, case_id: int, db: Session = Depends(get_database)):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")

    results = (db.query(TestResult)
               .filter(TestResult.case_id == case_id)
               .order_by(desc(TestResult.created_on)).all())

    section_cases = (db.query(TestCase)
                     .filter(TestCase.section_id == case.section_id)
                     .order_by(TestCase.title).all())

    return templates.TemplateResponse("testcase_detail.html", {
        "request": request,
        "case": case,
        "results": results,
        "latest_result": results[0] if results else None,
        "section_cases": section_cases,
        "status_names": STATUS_NAMES,
        "type_names": TYPE_NAMES,
        "priority_names": PRIORITY_NAMES,
        "status_classes": STATUS_CLASSES,
    })


@app.get("/ui/case/{case_id}/execute", response_class=HTMLResponse)
def execute_case_form(request: Request, case_id: int, db: Session = Depends(get_database)):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return templates.TemplateResponse("case_execute.html", {
        "request": request,
        "case": case,
        "status_names": STATUS_NAMES,
        "priority_names": PRIORITY_NAMES,
        "type_names": TYPE_NAMES,
        "status_classes": STATUS_CLASSES,
    })


@app.post("/ui/case/{case_id}/execute")
def execute_case(
    case_id: int,
    status_id: int = Form(...),
    comment: Optional[str] = Form(None),
    elapsed: Optional[str] = Form(None),
    db: Session = Depends(get_database),
):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    db.add(TestResult(case_id=case_id, status_id=status_id, comment=comment, elapsed=elapsed, created_by=1))
    db.commit()
    return RedirectResponse(url=f"/ui/case/{case_id}", status_code=303)


@app.get("/ui/runs", response_class=HTMLResponse)
def runs_list(request: Request, db: Session = Depends(get_database)):
    test_runs = (db.query(TestRun)
                 .filter(TestRun.project_id == 1)
                 .order_by(desc(TestRun.created_on)).all())

    # Build run stats
    run_stats = {}
    for run in test_runs:
        entries = db.query(RunEntry).filter(RunEntry.run_id == run.id).all()
        counts = {sid: 0 for sid in STATUS_NAMES}
        for e in entries:
            counts[e.status_id] = counts.get(e.status_id, 0) + 1
        run_stats[run.id] = {"total": len(entries), "counts": counts}

    return templates.TemplateResponse("runs_list.html", {
        "request": request,
        "test_runs": test_runs,
        "run_stats": run_stats,
        "status_names": STATUS_NAMES,
        "status_classes": STATUS_CLASSES,
    })


@app.get("/ui/cases/create", response_class=HTMLResponse)
def create_case_form(request: Request, db: Session = Depends(get_database)):
    sections = db.query(Section).filter(Section.project_id == 1).all()
    case_templates = db.query(Template).all()
    return templates.TemplateResponse("case_create.html", {
        "request": request,
        "sections": sections,
        "templates": case_templates,
        "type_names": TYPE_NAMES,
        "priority_names": PRIORITY_NAMES,
    })


@app.post("/ui/cases/create")
async def create_case_submit(
    request: Request,
    section_id: int = Form(...),
    title: str = Form(...),
    template_id: int = Form(1),
    type_id: int = Form(1),
    priority_id: int = Form(2),
    expected_result: str = Form(""),
    preconditions: str = Form(""),
    db: Session = Depends(get_database),
):
    form_data = await request.form()
    steps_data = []
    i = 0
    while f"steps[{i}][step]" in form_data or f"steps[{i}][content]" in form_data:
        action = (form_data.get(f"steps[{i}][content]") or form_data.get(f"steps[{i}][step]", "")).strip()
        expected = form_data.get(f"steps[{i}][expected]", "").strip()
        if action:
            steps_data.append({"content": action, "expected": expected})
        i += 1

    case = TestCase(
        section_id=section_id,
        title=title,
        template_id=template_id,
        type_id=type_id,
        priority_id=priority_id,
        expected_result=expected_result or None,
        preconditions=preconditions or None,
        steps=steps_data or None,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return RedirectResponse(url=f"/ui/case/{case.id}", status_code=303)


@app.get("/ui/case/{case_id}/edit", response_class=HTMLResponse)
def edit_case_form(request: Request, case_id: int, db: Session = Depends(get_database)):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    sections = db.query(Section).filter(Section.project_id == 1).all()
    case_templates = db.query(Template).all()
    return templates.TemplateResponse("case_edit.html", {
        "request": request,
        "case": case,
        "sections": sections,
        "templates": case_templates,
        "type_names": TYPE_NAMES,
        "priority_names": PRIORITY_NAMES,
    })


@app.post("/ui/case/{case_id}/edit")
async def edit_case_submit(
    case_id: int,
    request: Request,
    section_id: int = Form(...),
    title: str = Form(...),
    template_id: int = Form(...),
    type_id: int = Form(...),
    priority_id: int = Form(...),
    expected_result: str = Form(""),
    preconditions: str = Form(""),
    db: Session = Depends(get_database),
):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")

    form_data = await request.form()
    steps_data = []
    i = 0
    while f"steps[{i}][step]" in form_data or f"steps[{i}][content]" in form_data:
        action = (form_data.get(f"steps[{i}][content]") or form_data.get(f"steps[{i}][step]", "")).strip()
        expected = form_data.get(f"steps[{i}][expected]", "").strip()
        if action:
            steps_data.append({"content": action, "expected": expected})
        i += 1

    case.section_id = section_id
    case.title = title
    case.template_id = template_id
    case.type_id = type_id
    case.priority_id = priority_id
    case.expected_result = expected_result or None
    case.preconditions = preconditions or None
    case.steps = steps_data or None
    case.updated_on = datetime.utcnow()
    db.commit()
    return RedirectResponse(url=f"/ui/case/{case_id}", status_code=303)


@app.get("/ui/case/{case_id}/copy", response_class=HTMLResponse)
def copy_case_form(request: Request, case_id: int, db: Session = Depends(get_database)):
    original_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not original_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    sections = db.query(Section).filter(Section.project_id == 1).all()
    case_templates = db.query(Template).all()
    return templates.TemplateResponse("case_copy.html", {
        "request": request,
        "original_case": original_case,
        "sections": sections,
        "templates": case_templates,
        "type_names": TYPE_NAMES,
        "priority_names": PRIORITY_NAMES,
    })


@app.post("/ui/case/{case_id}/delete")
def delete_case_ui(case_id: int, db: Session = Depends(get_database)):
    c = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Test case not found")
    db.query(TestResult).filter(TestResult.case_id == case_id).delete()
    db.query(RunEntry).filter(RunEntry.case_id == case_id).delete()
    db.delete(c)
    db.commit()
    return RedirectResponse(url="/ui/cases", status_code=303)


@app.get("/ui/sections/create", response_class=HTMLResponse)
def create_section_form(request: Request, db: Session = Depends(get_database)):
    sections = db.query(Section).filter(Section.project_id == 1).all()
    return templates.TemplateResponse("section_create.html", {
        "request": request,
        "sections": sections,
    })


@app.post("/ui/sections/create")
def create_section_submit(
    name: str = Form(...),
    description: str = Form(""),
    parent_id: Optional[int] = Form(None),
    db: Session = Depends(get_database),
):
    db.add(Section(project_id=1, name=name, description=description or None, parent_id=parent_id or None))
    db.commit()
    return RedirectResponse(url="/ui/cases", status_code=303)


@app.get("/ui/runs/create", response_class=HTMLResponse)
def create_run_form(request: Request, db: Session = Depends(get_database)):
    sections = db.query(Section).filter(Section.project_id == 1).all()
    return templates.TemplateResponse("run_create.html", {"request": request, "sections": sections})


@app.post("/ui/runs/create")
def create_run_submit(
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_database),
):
    run = TestRun(project_id=1, name=name, description=description or None, suite_id=1)
    db.add(run)
    db.commit()
    db.refresh(run)
    return RedirectResponse(url=f"/ui/run/{run.id}", status_code=303)


@app.get("/ui/run/{run_id}", response_class=HTMLResponse)
def run_detail(request: Request, run_id: int, db: Session = Depends(get_database)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    entries = (db.query(RunEntry).join(TestCase)
               .filter(RunEntry.run_id == run_id).all())
    status_counts = {sid: 0 for sid in STATUS_NAMES}
    for e in entries:
        status_counts[e.status_id] = status_counts.get(e.status_id, 0) + 1

    return templates.TemplateResponse("run_detail.html", {
        "request": request,
        "run": run,
        "entries": entries,
        "status_counts": status_counts,
        "status_names": STATUS_NAMES,
        "status_classes": STATUS_CLASSES,
    })


@app.get("/ui/run/{run_id}/add-cases", response_class=HTMLResponse)
def add_cases_to_run(request: Request, run_id: int, db: Session = Depends(get_database)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    existing_ids = [e.case_id for e in db.query(RunEntry).filter(RunEntry.run_id == run_id).all()]
    available = (db.query(TestCase).join(Section)
                 .filter(Section.project_id == 1)
                 .filter(~TestCase.id.in_(existing_ids)).all())
    sections = db.query(Section).filter(Section.project_id == 1).all()
    return templates.TemplateResponse("run_add_cases.html", {
        "request": request,
        "run": run,
        "available_cases": available,
        "sections": sections,
        "type_names": TYPE_NAMES,
        "priority_names": PRIORITY_NAMES,
    })


@app.post("/ui/run/{run_id}/add-cases")
def add_cases_to_run_submit(
    run_id: int,
    case_ids: list = Form(...),
    db: Session = Depends(get_database),
):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    for cid in case_ids:
        existing = db.query(RunEntry).filter(RunEntry.run_id == run_id, RunEntry.case_id == int(cid)).first()
        if not existing:
            db.add(RunEntry(run_id=run_id, case_id=int(cid), status_id=3))
    db.commit()
    return RedirectResponse(url=f"/ui/run/{run_id}", status_code=303)


@app.get("/ui/run/{run_id}/complete")
def complete_run_ui(run_id: int, db: Session = Depends(get_database)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    run.is_completed = True
    run.completed_on = datetime.utcnow()
    db.commit()
    return RedirectResponse(url=f"/ui/run/{run_id}", status_code=303)


@app.get("/ui/run/{run_id}/edit", response_class=HTMLResponse)
def edit_run_form(request: Request, run_id: int, db: Session = Depends(get_database)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return templates.TemplateResponse("run_edit.html", {"request": request, "run": run})


@app.post("/ui/run/{run_id}/edit")
def edit_run_submit(
    run_id: int,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_database),
):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    run.name = name
    run.description = description or None
    db.commit()
    return RedirectResponse(url=f"/ui/run/{run_id}", status_code=303)


@app.post("/ui/run/{run_id}/delete")
def delete_run_ui(run_id: int, db: Session = Depends(get_database)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    db.delete(run)
    db.commit()
    return RedirectResponse(url="/ui/runs", status_code=303)


@app.post("/ui/run/{run_id}/entry/{entry_id}/update")
def update_run_entry(
    run_id: int,
    entry_id: int,
    status_id: int = Form(...),
    comment: Optional[str] = Form(None),
    elapsed: Optional[str] = Form(None),
    db: Session = Depends(get_database),
):
    entry = db.query(RunEntry).filter(RunEntry.id == entry_id, RunEntry.run_id == run_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Run entry not found")
    entry.status_id = status_id
    entry.comment = comment
    entry.elapsed = elapsed
    # Also log a TestResult
    db.add(TestResult(case_id=entry.case_id, run_id=run_id, status_id=status_id,
                      comment=comment, elapsed=elapsed, created_by=1))
    db.commit()
    return RedirectResponse(url=f"/ui/run/{run_id}", status_code=303)


# Placeholder routes
for path, feature, desc_text, back in [
    ("/ui/run/{run_id}/execute", "Execute Test Run",
     "Execute all test cases in a run sequentially or assign them to team members.", "/ui/runs"),
    ("/ui/run/{run_id}/report", "Generate Test Run Report",
     "Generate comprehensive reports with charts, statistics, and detailed test results.", "/ui/runs"),
    ("/ui/cases/import", "Import Test Cases",
     "Import test cases from CSV, Excel, or other TestRail instances.", "/ui/cases"),
]:
    @app.get(path, response_class=HTMLResponse)
    def _placeholder(request: Request, feature_name=feature, description=desc_text, back_url=back,
                     **kwargs):
        return templates.TemplateResponse("placeholder.html", {
            "request": request,
            "feature_name": feature_name,
            "description": description,
            "back_url": back_url,
        })


@app.get("/ui/section/{section_id}", response_class=HTMLResponse)
def section_view(section_id: int):
    return RedirectResponse(url=f"/ui/cases?section_id={section_id}")


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return RedirectResponse(url="/ui")


@app.get("/health", include_in_schema=False)
def health_check(db: Session = Depends(get_database)):
    try:
        cnt = db.query(Project).count()
        return {"status": "healthy", "database": "connected", "projects": cnt,
                "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=4002, reload=False, log_level="info")
