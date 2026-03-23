"""
TestRail Mock Service - API Routes

Implements real TestRail API v2 endpoint patterns:
  GET/POST index.php?/api/v2/{action}/{id}
  (URL is rewritten by middleware in app.py before reaching these handlers)

Authentication: HTTP Basic Auth  →  Authorization: Basic base64(email:api_key)
               Bearer token      →  Authorization: Bearer <token>
"""

import base64
import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from storage import get_database
from models import (
    Project, Section, Template, TestCase, TestResult, TestRun, RunEntry,
    ProjectCreate, SectionCreate,
    TestCaseCreate, TestCaseUpdate,
    TestResultCreate, BulkResultsCreate,
    TestRunCreate, TestRunUpdate,
    STATUS_NAMES, TYPE_NAMES, PRIORITY_NAMES,
    case_to_dict, result_to_dict, run_to_dict, project_to_dict, section_to_dict,
)

# ---------------------------------------------------------------------------
# Auth  — fixed credentials (same pattern as real TestRail)
# ---------------------------------------------------------------------------

# Single set of credentials every student uses.
# Override via environment variables if needed.
MOCK_EMAIL   = os.getenv("TESTRAIL_MOCK_EMAIL",   "admin@testrail.mock")
MOCK_API_KEY = os.getenv("TESTRAIL_MOCK_API_KEY",  "MockAPI@123")

# Pre-compute the expected Basic token so we only do it once.
_EXPECTED_BASIC = base64.b64encode(f"{MOCK_EMAIL}:{MOCK_API_KEY}".encode()).decode()


def require_auth(authorization: Optional[str] = Header(None)):
    """
    Validates against a single fixed email + API key (same as real TestRail Basic Auth).

    Expected header:
        Authorization: Basic <base64(email:api_key)>

    Credentials for this mock:
        Email  : admin@testrail.mock
        API Key: MockAPI@123
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Authentication required.",
                "hint": f"Use HTTP Basic Auth with email={MOCK_EMAIL!r} and api_key={MOCK_API_KEY!r}",
                "header_format": "Authorization: Basic <base64(email:api_key)>",
                "example": f"Authorization: Basic {_EXPECTED_BASIC}",
            },
        )

    if authorization.startswith("Basic "):
        try:
            decoded = base64.b64decode(authorization[6:]).decode("utf-8")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid Base64 encoding in Authorization header.")

        if decoded != f"{MOCK_EMAIL}:{MOCK_API_KEY}":
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Invalid credentials.",
                    "hint": f"Use email={MOCK_EMAIL!r} and api_key={MOCK_API_KEY!r}",
                    "example": f"Authorization: Basic {_EXPECTED_BASIC}",
                },
            )
        return True

    # Also accept: Bearer MockAPI@123  (convenience for quick curl tests)
    if authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        if token != MOCK_API_KEY:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Invalid Bearer token.",
                    "hint": f"Use api_key={MOCK_API_KEY!r} as the Bearer token, "
                            f"or switch to Basic Auth with email={MOCK_EMAIL!r}",
                },
            )
        return True

    raise HTTPException(
        status_code=401,
        detail="Unsupported auth scheme. Use 'Basic' or 'Bearer'.",
    )


# Router with auth dependency on all routes
api_router = APIRouter(dependencies=[Depends(require_auth)])

# ---------------------------------------------------------------------------
# Paginated list helpers
# ---------------------------------------------------------------------------

def paginated(items: list, key: str, offset: int, limit: int, base_path: str) -> dict:
    total = len(items)
    page = items[offset: offset + limit]
    nxt = f"{base_path}&limit={limit}&offset={offset + limit}" if offset + limit < total else None
    prv = f"{base_path}&limit={limit}&offset={max(0, offset - limit)}" if offset > 0 else None
    return {
        "offset": offset,
        "limit": limit,
        "size": len(page),
        "_links": {"next": nxt, "prev": prv},
        key: page,
    }


# ===========================================================================
# PROJECTS
# ===========================================================================

@api_router.get("/index.php/api/v2/get_projects")
@api_router.get("/api/v2/get_projects")
def get_projects(db: Session = Depends(get_database)):
    projects = db.query(Project).all()
    return [project_to_dict(p) for p in projects]


@api_router.get("/index.php/api/v2/get_project/{project_id}")
@api_router.get("/api/v2/get_project/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_database)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=400, detail="Invalid or unknown project")
    return project_to_dict(p)


@api_router.post("/index.php/api/v2/add_project")
@api_router.post("/api/v2/add_project")
def add_project(project: ProjectCreate, db: Session = Depends(get_database)):
    p = Project(**project.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


@api_router.post("/index.php/api/v2/update_project/{project_id}")
@api_router.post("/api/v2/update_project/{project_id}")
def update_project(project_id: int, data: ProjectCreate, db: Session = Depends(get_database)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=400, detail="Invalid or unknown project")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


@api_router.post("/index.php/api/v2/delete_project/{project_id}")
@api_router.post("/api/v2/delete_project/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_database)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=400, detail="Invalid or unknown project")
    db.delete(p)
    db.commit()
    return {}


# ===========================================================================
# SECTIONS
# ===========================================================================

@api_router.get("/index.php/api/v2/get_section/{section_id}")
@api_router.get("/api/v2/get_section/{section_id}")
def get_section(section_id: int, db: Session = Depends(get_database)):
    s = db.query(Section).filter(Section.id == section_id).first()
    if not s:
        raise HTTPException(status_code=400, detail="Invalid or unknown section")
    return section_to_dict(s)


@api_router.get("/index.php/api/v2/get_sections/{project_id}")
@api_router.get("/api/v2/get_sections/{project_id}")
def get_sections(
    project_id: int,
    suite_id: Optional[int] = Query(None),
    limit: int = Query(250, le=250),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
):
    secs = db.query(Section).filter(Section.project_id == project_id).all()
    all_dicts = [section_to_dict(s) for s in secs]
    return paginated(all_dicts, "sections", offset, limit, f"/api/v2/get_sections/{project_id}")


@api_router.post("/index.php/api/v2/add_section/{project_id}")
@api_router.post("/api/v2/add_section/{project_id}")
def add_section(project_id: int, data: SectionCreate, db: Session = Depends(get_database)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=400, detail="Invalid or unknown project")
    s = Section(project_id=project_id, name=data.name, description=data.description, parent_id=data.parent_id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return section_to_dict(s)


@api_router.post("/index.php/api/v2/update_section/{section_id}")
@api_router.post("/api/v2/update_section/{section_id}")
def update_section(section_id: int, data: SectionCreate, db: Session = Depends(get_database)):
    s = db.query(Section).filter(Section.id == section_id).first()
    if not s:
        raise HTTPException(status_code=400, detail="Invalid or unknown section")
    for k, v in data.dict(exclude_unset=True).items():
        if hasattr(s, k):
            setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return section_to_dict(s)


@api_router.post("/index.php/api/v2/delete_section/{section_id}")
@api_router.post("/api/v2/delete_section/{section_id}")
def delete_section(section_id: int, db: Session = Depends(get_database)):
    s = db.query(Section).filter(Section.id == section_id).first()
    if not s:
        raise HTTPException(status_code=400, detail="Invalid or unknown section")
    db.delete(s)
    db.commit()
    return {}


# ===========================================================================
# CASES
# ===========================================================================

@api_router.get("/index.php/api/v2/get_case/{case_id}")
@api_router.get("/api/v2/get_case/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_database)):
    c = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not c:
        raise HTTPException(status_code=400, detail="Invalid or unknown test case")
    return case_to_dict(c)


@api_router.get("/index.php/api/v2/get_cases/{project_id}")
@api_router.get("/api/v2/get_cases/{project_id}")
def get_cases(
    project_id: int,
    suite_id: Optional[int] = Query(None),
    section_id: Optional[int] = Query(None),
    priority_id: Optional[str] = Query(None),
    type_id: Optional[str] = Query(None),
    filter: Optional[str] = Query(None),
    limit: int = Query(250, le=250),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
):
    query = db.query(TestCase).join(Section).filter(Section.project_id == project_id)

    if section_id:
        query = query.filter(TestCase.section_id == section_id)
    if priority_id:
        ids = [int(x) for x in priority_id.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(TestCase.priority_id.in_(ids))
    if type_id:
        ids = [int(x) for x in type_id.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(TestCase.type_id.in_(ids))
    if filter:
        query = query.filter(TestCase.title.ilike(f"%{filter}%"))

    all_cases = query.order_by(TestCase.id).all()
    all_dicts = [case_to_dict(c) for c in all_cases]
    return paginated(all_dicts, "cases", offset, limit, f"/api/v2/get_cases/{project_id}")


@api_router.post("/index.php/api/v2/add_case/{section_id}")
@api_router.post("/api/v2/add_case/{section_id}")
def add_case(section_id: int, data: TestCaseCreate, db: Session = Depends(get_database)):
    sec = db.query(Section).filter(Section.id == section_id).first()
    if not sec:
        raise HTTPException(status_code=400, detail="Invalid or unknown section")

    # Normalise step format
    raw_steps = data.custom_steps_separated or data.steps
    steps = None
    if raw_steps:
        steps = []
        for s in raw_steps:
            if isinstance(s, dict):
                steps.append({"content": s.get("content") or s.get("step", ""), "expected": s.get("expected", "")})
            else:
                steps.append(s)

    c = TestCase(
        section_id=section_id,
        title=data.title,
        template_id=data.template_id,
        type_id=data.type_id,
        priority_id=data.priority_id,
        suite_id=data.suite_id or 1,
        milestone_id=data.milestone_id,
        refs=data.refs,
        estimate=data.estimate,
        steps=steps,
        expected_result=data.custom_expected or data.expected_result,
        preconditions=data.custom_preconds or data.preconditions,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return case_to_dict(c)


@api_router.post("/index.php/api/v2/update_case/{case_id}")
@api_router.post("/api/v2/update_case/{case_id}")
def update_case(case_id: int, data: TestCaseUpdate, db: Session = Depends(get_database)):
    c = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not c:
        raise HTTPException(status_code=400, detail="Invalid or unknown test case")

    update_data = data.dict(exclude_unset=True)

    # Field mappings: TestRail custom fields → internal columns
    if "custom_preconds" in update_data:
        c.preconditions = update_data.pop("custom_preconds")
    if "preconditions" in update_data:
        c.preconditions = update_data.pop("preconditions")
    if "custom_expected" in update_data:
        c.expected_result = update_data.pop("custom_expected")
    if "expected_result" in update_data:
        c.expected_result = update_data.pop("expected_result")
    if "custom_steps_separated" in update_data or "steps" in update_data:
        raw = update_data.pop("custom_steps_separated", None) or update_data.pop("steps", None)
        if raw:
            c.steps = [
                {"content": s.get("content") or s.get("step", ""), "expected": s.get("expected", "")}
                if isinstance(s, dict) else s
                for s in raw
            ]
        else:
            c.steps = None

    for k, v in update_data.items():
        if hasattr(c, k):
            setattr(c, k, v)

    c.updated_on = datetime.utcnow()
    db.commit()
    db.refresh(c)
    return case_to_dict(c)


@api_router.post("/index.php/api/v2/delete_case/{case_id}")
@api_router.post("/api/v2/delete_case/{case_id}")
def delete_case(case_id: int, soft: int = Query(0), db: Session = Depends(get_database)):
    c = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not c:
        raise HTTPException(status_code=400, detail="Invalid or unknown test case")
    if soft == 1:
        affected = db.query(TestResult).filter(TestResult.case_id == case_id).count()
        return {"affected_tests": affected}
    db.query(TestResult).filter(TestResult.case_id == case_id).delete()
    db.query(RunEntry).filter(RunEntry.case_id == case_id).delete()
    db.delete(c)
    db.commit()
    return {}


@api_router.post("/index.php/api/v2/delete_cases/{project_id}")
@api_router.post("/api/v2/delete_cases/{project_id}")
def delete_cases(project_id: int, body: dict, soft: int = Query(0), db: Session = Depends(get_database)):
    case_ids = body.get("case_ids", [])
    if not case_ids:
        raise HTTPException(status_code=400, detail="case_ids required")
    deleted = []
    for cid in case_ids:
        c = db.query(TestCase).filter(TestCase.id == cid).first()
        if c:
            if soft != 1:
                db.query(TestResult).filter(TestResult.case_id == cid).delete()
                db.query(RunEntry).filter(RunEntry.case_id == cid).delete()
                db.delete(c)
            deleted.append(cid)
    if soft != 1:
        db.commit()
    return {"deleted_count": len(deleted), "deleted_case_ids": deleted}


# move / copy cases
@api_router.post("/index.php/api/v2/copy_cases_to_section/{section_id}")
@api_router.post("/api/v2/copy_cases_to_section/{section_id}")
def copy_cases_to_section(section_id: int, body: dict, db: Session = Depends(get_database)):
    sec = db.query(Section).filter(Section.id == section_id).first()
    if not sec:
        raise HTTPException(status_code=400, detail="Invalid or unknown section")
    case_ids = body.get("case_ids", [])
    new_cases = []
    for cid in case_ids:
        orig = db.query(TestCase).filter(TestCase.id == cid).first()
        if orig:
            nc = TestCase(
                section_id=section_id,
                title=f"Copy of {orig.title}",
                template_id=orig.template_id,
                type_id=orig.type_id,
                priority_id=orig.priority_id,
                steps=orig.steps,
                expected_result=orig.expected_result,
                preconditions=orig.preconditions,
            )
            db.add(nc)
            new_cases.append(nc)
    db.commit()
    for nc in new_cases:
        db.refresh(nc)
    return [case_to_dict(nc) for nc in new_cases]


@api_router.post("/index.php/api/v2/move_cases_to_section/{section_id}")
@api_router.post("/api/v2/move_cases_to_section/{section_id}")
def move_cases_to_section(section_id: int, body: dict, db: Session = Depends(get_database)):
    sec = db.query(Section).filter(Section.id == section_id).first()
    if not sec:
        raise HTTPException(status_code=400, detail="Invalid or unknown section")
    case_ids = body.get("case_ids", [])
    moved = []
    for cid in case_ids:
        c = db.query(TestCase).filter(TestCase.id == cid).first()
        if c:
            c.section_id = section_id
            moved.append(c)
    db.commit()
    return [case_to_dict(c) for c in moved]


# ===========================================================================
# RESULTS
# ===========================================================================

@api_router.get("/index.php/api/v2/get_results/{test_id}")
@api_router.get("/api/v2/get_results/{test_id}")
def get_results(
    test_id: int,
    limit: int = Query(250, le=250),
    offset: int = Query(0, ge=0),
    status_id: Optional[str] = Query(None),
    db: Session = Depends(get_database),
):
    """test_id maps to case_id in this mock."""
    q = db.query(TestResult).filter(TestResult.case_id == test_id).order_by(desc(TestResult.created_on))
    if status_id:
        ids = [int(x) for x in status_id.split(",") if x.strip().isdigit()]
        if ids:
            q = q.filter(TestResult.status_id.in_(ids))
    all_results = q.all()
    all_dicts = [result_to_dict(r) for r in all_results]
    return paginated(all_dicts, "results", offset, limit, f"/api/v2/get_results/{test_id}")


@api_router.get("/index.php/api/v2/get_results_for_case/{run_id}/{case_id}")
@api_router.get("/api/v2/get_results_for_case/{run_id}/{case_id}")
def get_results_for_case(
    run_id: int,
    case_id: int,
    limit: int = Query(250, le=250),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=400, detail="Invalid or unknown test run")
    q = (db.query(TestResult)
         .filter(TestResult.case_id == case_id)
         .filter(TestResult.run_id == run_id)
         .order_by(desc(TestResult.created_on)))
    all_results = q.all()
    if not all_results:
        # Fall back to results not tied to a specific run
        all_results = (db.query(TestResult)
                       .filter(TestResult.case_id == case_id)
                       .order_by(desc(TestResult.created_on))
                       .all())
    all_dicts = [result_to_dict(r) for r in all_results]
    return paginated(all_dicts, "results", offset, limit,
                     f"/api/v2/get_results_for_case/{run_id}/{case_id}")


@api_router.get("/index.php/api/v2/get_results_for_run/{run_id}")
@api_router.get("/api/v2/get_results_for_run/{run_id}")
def get_results_for_run(
    run_id: int,
    limit: int = Query(250, le=250),
    offset: int = Query(0, ge=0),
    status_id: Optional[str] = Query(None),
    db: Session = Depends(get_database),
):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=400, detail="Invalid or unknown test run")
    q = db.query(TestResult).filter(TestResult.run_id == run_id).order_by(desc(TestResult.created_on))
    if status_id:
        ids = [int(x) for x in status_id.split(",") if x.strip().isdigit()]
        if ids:
            q = q.filter(TestResult.status_id.in_(ids))
    all_results = q.all()
    all_dicts = [result_to_dict(r) for r in all_results]
    return paginated(all_dicts, "results", offset, limit, f"/api/v2/get_results_for_run/{run_id}")


@api_router.post("/index.php/api/v2/add_result/{test_id}")
@api_router.post("/api/v2/add_result/{test_id}")
def add_result(test_id: int, data: TestResultCreate, db: Session = Depends(get_database)):
    """test_id maps to case_id."""
    c = db.query(TestCase).filter(TestCase.id == test_id).first()
    if not c:
        raise HTTPException(status_code=400, detail="Invalid or unknown test")
    if data.status_id not in STATUS_NAMES:
        raise HTTPException(status_code=400, detail="Invalid status_id")
    r = TestResult(
        case_id=test_id,
        status_id=data.status_id,
        comment=data.comment,
        elapsed=data.elapsed,
        defects=data.defects,
        version=data.version,
        assignedto_id=data.assignedto_id,
        created_by=1,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return result_to_dict(r)


@api_router.post("/index.php/api/v2/add_result_for_case/{run_id}/{case_id}")
@api_router.post("/api/v2/add_result_for_case/{run_id}/{case_id}")
def add_result_for_case(run_id: int, case_id: int, data: TestResultCreate, db: Session = Depends(get_database)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=400, detail="Invalid or unknown test run")
    c = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not c:
        raise HTTPException(status_code=400, detail="Invalid or unknown test case")
    if data.status_id not in STATUS_NAMES:
        raise HTTPException(status_code=400, detail="Invalid status_id")

    r = TestResult(
        case_id=case_id,
        run_id=run_id,
        status_id=data.status_id,
        comment=data.comment,
        elapsed=data.elapsed,
        defects=data.defects,
        version=data.version,
        assignedto_id=data.assignedto_id,
        created_by=1,
    )
    db.add(r)

    # Update the run entry status if it exists
    entry = db.query(RunEntry).filter(RunEntry.run_id == run_id, RunEntry.case_id == case_id).first()
    if entry:
        entry.status_id = data.status_id
        entry.comment = data.comment
        entry.elapsed = data.elapsed

    db.commit()
    db.refresh(r)
    return result_to_dict(r)


@api_router.post("/index.php/api/v2/add_results/{run_id}")
@api_router.post("/api/v2/add_results/{run_id}")
def add_results(run_id: int, data: BulkResultsCreate, db: Session = Depends(get_database)):
    """Bulk add by test_id (test_id == case_id in this mock)."""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=400, detail="Invalid or unknown test run")

    created = []
    for item in data.results:
        cid = item.test_id or item.case_id
        if not cid:
            continue
        c = db.query(TestCase).filter(TestCase.id == cid).first()
        if not c:
            continue
        r = TestResult(
            case_id=cid,
            run_id=run_id,
            status_id=item.status_id or 3,
            comment=item.comment,
            elapsed=item.elapsed,
            defects=item.defects,
            version=item.version,
            assignedto_id=item.assignedto_id,
            created_by=1,
        )
        db.add(r)
        created.append(r)

        entry = db.query(RunEntry).filter(RunEntry.run_id == run_id, RunEntry.case_id == cid).first()
        if entry and item.status_id:
            entry.status_id = item.status_id

    db.commit()
    for r in created:
        db.refresh(r)
    return [result_to_dict(r) for r in created]


@api_router.post("/index.php/api/v2/add_results_for_cases/{run_id}")
@api_router.post("/api/v2/add_results_for_cases/{run_id}")
def add_results_for_cases(run_id: int, data: BulkResultsCreate, db: Session = Depends(get_database)):
    """Bulk add by case_id."""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=400, detail="Invalid or unknown test run")

    created = []
    for item in data.results:
        cid = item.case_id or item.test_id
        if not cid:
            continue
        c = db.query(TestCase).filter(TestCase.id == cid).first()
        if not c:
            continue
        r = TestResult(
            case_id=cid,
            run_id=run_id,
            status_id=item.status_id or 3,
            comment=item.comment,
            elapsed=item.elapsed,
            defects=item.defects,
            version=item.version,
            assignedto_id=item.assignedto_id,
            created_by=1,
        )
        db.add(r)
        created.append(r)

        entry = db.query(RunEntry).filter(RunEntry.run_id == run_id, RunEntry.case_id == cid).first()
        if entry and item.status_id:
            entry.status_id = item.status_id

    db.commit()
    for r in created:
        db.refresh(r)
    return [result_to_dict(r) for r in created]


# ===========================================================================
# RUNS
# ===========================================================================

@api_router.get("/index.php/api/v2/get_run/{run_id}")
@api_router.get("/api/v2/get_run/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_database)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=400, detail="Invalid or unknown test run")
    return run_to_dict(run)


@api_router.get("/index.php/api/v2/get_runs/{project_id}")
@api_router.get("/api/v2/get_runs/{project_id}")
def get_runs(
    project_id: int,
    is_completed: Optional[int] = Query(None),
    limit: int = Query(250, le=250),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
):
    q = db.query(TestRun).filter(TestRun.project_id == project_id).order_by(desc(TestRun.created_on))
    if is_completed is not None:
        q = q.filter(TestRun.is_completed == bool(is_completed))
    all_runs = q.all()
    all_dicts = [run_to_dict(r) for r in all_runs]
    return paginated(all_dicts, "runs", offset, limit, f"/api/v2/get_runs/{project_id}")


@api_router.post("/index.php/api/v2/add_run/{project_id}")
@api_router.post("/api/v2/add_run/{project_id}")
def add_run(project_id: int, data: TestRunCreate, db: Session = Depends(get_database)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=400, detail="Invalid or unknown project")

    run = TestRun(
        project_id=project_id,
        name=data.name,
        description=data.description,
        suite_id=data.suite_id or 1,
        milestone_id=data.milestone_id,
        assignedto_id=data.assignedto_id,
        include_all=data.include_all,
        refs=data.refs,
        created_by=1,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Add cases if specified
    case_ids = data.case_ids or []
    if data.include_all and not case_ids:
        # Add all cases from the project
        sections = db.query(Section).filter(Section.project_id == project_id).all()
        for sec in sections:
            for c in sec.cases:
                db.add(RunEntry(run_id=run.id, case_id=c.id, status_id=3))
    else:
        for cid in case_ids:
            db.add(RunEntry(run_id=run.id, case_id=cid, status_id=3))

    db.commit()
    db.refresh(run)
    return run_to_dict(run)


@api_router.post("/index.php/api/v2/update_run/{run_id}")
@api_router.post("/api/v2/update_run/{run_id}")
def update_run(run_id: int, data: TestRunUpdate, db: Session = Depends(get_database)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=400, detail="Invalid or unknown test run")

    update_data = data.dict(exclude_unset=True)
    case_ids = update_data.pop("case_ids", None)
    include_all = update_data.get("include_all")

    for k, v in update_data.items():
        if hasattr(run, k):
            setattr(run, k, v)

    if case_ids is not None:
        # Remove existing entries and replace
        db.query(RunEntry).filter(RunEntry.run_id == run_id).delete()
        for cid in case_ids:
            db.add(RunEntry(run_id=run_id, case_id=cid, status_id=3))

    db.commit()
    db.refresh(run)
    return run_to_dict(run)


@api_router.post("/index.php/api/v2/close_run/{run_id}")
@api_router.post("/api/v2/close_run/{run_id}")
def close_run(run_id: int, db: Session = Depends(get_database)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=400, detail="Invalid or unknown test run")
    run.is_completed = True
    run.completed_on = datetime.utcnow()
    db.commit()
    db.refresh(run)
    return run_to_dict(run)


@api_router.post("/index.php/api/v2/delete_run/{run_id}")
@api_router.post("/api/v2/delete_run/{run_id}")
def delete_run(run_id: int, soft: int = Query(0), db: Session = Depends(get_database)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=400, detail="Invalid or unknown test run")
    if soft == 1:
        count = db.query(RunEntry).filter(RunEntry.run_id == run_id).count()
        return {"affected_tests": count}
    db.delete(run)
    db.commit()
    return {}


# ===========================================================================
# UTILITIES  (statuses, types, priorities, templates)
# ===========================================================================

@api_router.get("/index.php/api/v2/get_statuses")
@api_router.get("/api/v2/get_statuses")
@api_router.get("/api/v2/statuses")
def get_statuses():
    return [{"id": k, "name": v, "label": v, "color_dark": 0, "color_medium": 0, "color_bright": 0,
             "is_system": True, "is_untested": k == 3, "is_final": k in (1, 5)}
            for k, v in STATUS_NAMES.items()]


@api_router.get("/index.php/api/v2/get_case_types")
@api_router.get("/api/v2/get_case_types")
@api_router.get("/api/v2/types")
def get_case_types():
    return [{"id": k, "name": v, "is_default": k == 1} for k, v in TYPE_NAMES.items()]


@api_router.get("/index.php/api/v2/get_priorities")
@api_router.get("/api/v2/get_priorities")
@api_router.get("/api/v2/priorities")
def get_priorities():
    return [{"id": k, "name": v, "short_name": v[:1], "is_default": k == 2, "priority": k}
            for k, v in PRIORITY_NAMES.items()]


@api_router.get("/index.php/api/v2/get_templates/{project_id}")
@api_router.get("/api/v2/get_templates/{project_id}")
@api_router.get("/api/v2/templates")
def get_templates(project_id: int = 1, db: Session = Depends(get_database)):
    templates = db.query(Template).all()
    return [{"id": t.id, "name": t.name, "is_default": t.is_default} for t in templates]


# ===========================================================================
# LEGACY  (/api/v2/ CRUD style — backward compat for existing clients)
# ===========================================================================

@api_router.get("/api/v2/projects")
def _compat_get_projects(db: Session = Depends(get_database)):
    return get_projects(db)


@api_router.get("/api/v2/project/{project_id}")
def _compat_get_project(project_id: int, db: Session = Depends(get_database)):
    return get_project(project_id, db)


@api_router.post("/api/v2/projects")
def _compat_add_project(project: ProjectCreate, db: Session = Depends(get_database)):
    return add_project(project, db)


@api_router.get("/api/v2/sections/{project_id}")
def _compat_get_sections(
    project_id: int,
    limit: int = Query(250, le=250),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
):
    return get_sections(project_id, suite_id=None, limit=limit, offset=offset, db=db)


@api_router.post("/api/v2/sections/{project_id}")
def _compat_add_section(project_id: int, section: SectionCreate, db: Session = Depends(get_database)):
    return add_section(project_id, section, db)


@api_router.get("/api/v2/case/{case_id}")
def _compat_get_case(case_id: int, db: Session = Depends(get_database)):
    return get_case(case_id, db)


@api_router.get("/api/v2/cases/{project_id}")
def _compat_get_cases(
    project_id: int,
    section_id: Optional[int] = Query(None),
    limit: int = Query(250, le=250),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
):
    # Pass all optional params explicitly to avoid FastAPI Query defaults leaking in
    return get_cases(project_id, section_id=section_id, priority_id=None,
                     type_id=None, filter=None, limit=limit, offset=offset, db=db)


@api_router.post("/api/v2/cases/{section_id}")
def _compat_add_case(section_id: int, case: TestCaseCreate, db: Session = Depends(get_database)):
    return add_case(section_id, case, db)


@api_router.put("/api/v2/case/{case_id}")
def _compat_update_case(case_id: int, case: TestCaseUpdate, db: Session = Depends(get_database)):
    return update_case(case_id, case, db)


@api_router.delete("/api/v2/case/{case_id}")
def _compat_delete_case(case_id: int, db: Session = Depends(get_database)):
    return delete_case(case_id, soft=0, db=db)


@api_router.get("/api/v2/results/{case_id}")
def _compat_get_results(case_id: int, limit: int = Query(50), db: Session = Depends(get_database)):
    return get_results(case_id, limit=limit, status_id=None, offset=0, db=db)


@api_router.post("/api/v2/results/{case_id}")
def _compat_add_result(case_id: int, result: TestResultCreate, db: Session = Depends(get_database)):
    return add_result(case_id, result, db)


@api_router.get("/api/v2/runs/{project_id}")
def _compat_get_runs(project_id: int, db: Session = Depends(get_database)):
    return get_runs(project_id, is_completed=None, limit=250, offset=0, db=db)


@api_router.get("/api/v2/run/{run_id}")
def _compat_get_run(run_id: int, db: Session = Depends(get_database)):
    return get_run(run_id, db)


@api_router.post("/api/v2/runs/{project_id}")
def _compat_add_run(project_id: int, run: TestRunCreate, db: Session = Depends(get_database)):
    return add_run(project_id, run, db)


# ===========================================================================
# STATS  (non-standard, UI helper)
# ===========================================================================

@api_router.get("/api/v2/stats/{project_id}")
def get_project_stats(project_id: int, db: Session = Depends(get_database)):
    sections = db.query(Section).filter(Section.project_id == project_id).all()
    section_stats = []
    total_cases = 0
    status_counts = {sid: 0 for sid in STATUS_NAMES}

    for sec in sections:
        cnt = db.query(TestCase).filter(TestCase.section_id == sec.id).count()
        total_cases += cnt
        latest = (db.query(TestResult).join(TestCase)
                  .filter(TestCase.section_id == sec.id)
                  .order_by(desc(TestResult.created_on)).all())
        sec_counts = {sid: 0 for sid in STATUS_NAMES}
        for r in latest:
            sec_counts[r.status_id] = sec_counts.get(r.status_id, 0) + 1
            status_counts[r.status_id] = status_counts.get(r.status_id, 0) + 1
        section_stats.append({
            "section_id": sec.id,
            "section_name": sec.name,
            "case_count": cnt,
            "status_counts": sec_counts,
        })

    return {
        "project_id": project_id,
        "total_cases": total_cases,
        "sections": section_stats,
        "overall_status_counts": status_counts,
    }
