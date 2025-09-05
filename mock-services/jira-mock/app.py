from fastapi import FastAPI, Request, HTTPException, Header, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import sqlite3
import os
import json

app = FastAPI(title="Jira Mock Service")

# Templates & static
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

DB_PATH = os.path.join(os.path.dirname(__file__), "jira.db")

class IssueCreate(BaseModel):
    fields: dict


class IssueForm(BaseModel):
    summary: str
    description: Optional[str] = ""


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.on_event("startup")
async def startup():
    # ensure db
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        summary TEXT,
        description TEXT,
        issue_type TEXT,
        created_on TEXT
    )
    """)
    conn.commit()
    conn.close()
    # seed from shared if empty
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(1) as cnt FROM issues")
    cnt = c.fetchone()[0]
    if cnt == 0:
        seed_path = os.path.join(os.path.dirname(__file__), "..", "shared", "seed", "sample_issues.json")
        seed_path = os.path.normpath(seed_path)
        if os.path.exists(seed_path):
            with open(seed_path, "r") as fh:
                data = json.load(fh)
            for item in data:
                fields = item.get("fields", {})
                summary = fields.get("summary", "seed")
                description = fields.get("description", "")
                issue_type = fields.get("issuetype", {}).get("name", "Task")
                c.execute("INSERT INTO issues (key, summary, description, issue_type, created_on) VALUES (?, ?, ?, ?, datetime('now'))",
                          (item.get("key"), summary, description, issue_type))
            conn.commit()
    conn.close()


def require_bearer(authorization: Optional[str] = Header(None)):
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")


@app.post("/rest/api/3/issue")
async def create_issue(issue: IssueCreate = None, authorization: Optional[str] = Header(None)):
    # JSON API: require bearer
    if issue is None:
        raise HTTPException(status_code=400, detail="Missing issue payload")
    require_bearer(authorization)
    fields = issue.fields
    summary = fields.get("summary") or fields.get("project", {}).get("name", "No summary")
    description = fields.get("description", "")
    issue_type = fields.get("issuetype", {}).get("name", "Task")

    conn = get_db_conn()
    c = conn.cursor()
    # generate key like QA-<id>
    c.execute("INSERT INTO issues (key, summary, description, issue_type, created_on) VALUES (?, ?, ?, ?, datetime('now'))",
              (None, summary, description, issue_type))
    issue_id = c.lastrowid
    key = f"QA-{issue_id}"
    c.execute("UPDATE issues SET key=? WHERE id=?", (key, issue_id))
    conn.commit()
    conn.close()

    return JSONResponse(status_code=201, content={"id": {"id": str(issue_id)}, "key": key, "self": f"/rest/api/3/issue/{key}"})


# Form-based quick create from UI
@app.post("/ui/create")
async def ui_create(summary: str = Form(...), description: str = Form("")):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("INSERT INTO issues (key, summary, description, issue_type, created_on) VALUES (?, ?, ?, ?, datetime('now'))",
              (None, summary, description, "Task"))
    issue_id = c.lastrowid
    key = f"QA-{issue_id}"
    c.execute("UPDATE issues SET key=? WHERE id=?", (key, issue_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/ui/issue/{key}", status_code=303)


@app.get("/rest/api/3/issue/{issue_key}")
async def get_issue(issue_key: str, authorization: Optional[str] = Header(None)):
    require_bearer(authorization)
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM issues WHERE key=?", (issue_key,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {"id": row["id"], "key": row["key"], "fields": {"summary": row["summary"], "description": row["description"], "issuetype": {"name": row["issue_type"]}}}


@app.get("/ui", response_class=HTMLResponse)
async def ui_index(request: Request):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM issues ORDER BY id DESC LIMIT 100")
    rows = c.fetchall()
    conn.close()
    issues = [dict(r) for r in rows]
    return templates.TemplateResponse("index.html", {"request": request, "issues": issues})


@app.get("/rest/api/3/search")
async def search_issues(startAt: int = 0, maxResults: int = 50, authorization: Optional[str] = Header(None)):
    require_bearer(authorization)
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM issues ORDER BY id DESC LIMIT ? OFFSET ?", (maxResults, startAt))
    rows = c.fetchall()
    conn.close()
    issues = [{"id": r["id"], "key": r["key"], "fields": {"summary": r["summary"]}} for r in rows]
    return {"startAt": startAt, "maxResults": maxResults, "total": len(issues), "issues": issues}



@app.delete("/rest/api/3/issue/{issue_key}")
async def delete_issue(issue_key: str, authorization: Optional[str] = Header(None)):
    """Delete a single issue by key. Returns 204 if deleted, 404 if not found."""
    require_bearer(authorization)
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM issues WHERE key=?", (issue_key,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")
    c.execute("DELETE FROM issues WHERE key=?", (issue_key,))
    conn.commit()
    conn.close()
    return Response(status_code=204)


@app.post("/admin/reset")
async def admin_reset(authorization: Optional[str] = Header(None)):
    """Reset the database and reseed from shared/seed/sample_issues.json. Requires Authorization header."""
    require_bearer(authorization)
    # remove DB file if exists
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError:
            pass
    # recreate and reseed by calling startup
    await startup()
    return {"status": "reset"}


@app.get("/ui/issue/{key}", response_class=HTMLResponse)
async def ui_issue_detail(request: Request, key: str):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM issues WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Issue not found")
    issue = dict(row)
    return templates.TemplateResponse("issue_detail.html", {"request": request, "issue": issue})


@app.get("/health")
async def health():
    return {"status": "ok"}
