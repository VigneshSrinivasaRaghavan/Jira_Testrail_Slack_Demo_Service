from fastapi import FastAPI, Request, HTTPException, Header, Form, Query, Path, Security
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Any
import sqlite3
import os
import json
import re

app = FastAPI(
    title="Jira Mock Service",
    description="""
## Mock Jira REST API v3 — Training & Demo Environment

This service mimics Jira Cloud REST API v3 endpoints for AI agent integration training.

---

## 🔑 Authentication — Required for ALL API calls

Every API endpoint requires a Bearer token in the `Authorization` header.

**The token is fixed. Only this exact value is accepted:**

```
Authorization: Bearer mock-jira-token-2025
```

Any other token → **401 Unauthorized**.

**How to authorize in this UI:**
1. Click the **Authorize 🔒** button at the top right of this page
2. In the `BearerAuth` field enter: `mock-jira-token-2025`
3. Click **Authorize** → **Close**
4. All requests from this UI will now include the correct header automatically

---

## Key Features
- **Create / Read / Edit / Delete** issues (Story & Bug)
- **Status transitions**: To Do → In Progress → Done
- **Story fields**: story points (`customfield_10016`), sprint (`customfield_10020`), epic link (`customfield_10014`)
- **Bug fields**: environment, fixVersions, duedate
- **ADF description** format (same as real Jira Cloud)
- **JQL search**: `?jql=issuetype=Story`, `?jql=status="In Progress"`
- **Transitions API**: `GET/POST /rest/api/3/issue/{key}/transitions`
- **Admin reset**: `POST /admin/reset` — wipes DB and reloads seed data

---

## Base URL
```
http://localhost:4001
```
    """,
    version="2.0.0",
    openapi_tags=[
        {"name": "Issues", "description": "CRUD operations for Jira issues (Story, Bug, Task)"},
        {"name": "System",  "description": "Health check and service info"},
        {"name": "Admin",   "description": "Reset and maintenance operations"},
        {"name": "UI",      "description": "Browser UI routes (no auth required)"},
    ],
    swagger_ui_parameters={"persistAuthorization": True},
)

# Inject BearerAuth security scheme into OpenAPI spec so the Authorize button
# appears in Swagger UI pre-filled with the scheme name.
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    schema.setdefault("components", {})
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "description": "Enter the mock API token: **mock-jira-token-2025**",
        }
    }
    # Apply security globally to every operation
    for path_data in schema.get("paths", {}).values():
        for operation in path_data.values():
            if isinstance(operation, dict):
                operation.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

DB_PATH = os.path.join(os.path.dirname(__file__), "jira.db")

PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "QA")
PROJECT_NAME = os.environ.get("JIRA_PROJECT_NAME", "QA Project")

# Fixed API token — only this value is accepted in the Authorization header.
# Configurable via env var JIRA_API_TOKEN; defaults to the value below.
VALID_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "mock-jira-token-2025")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class IssueType(BaseModel):
    name: str = Field(..., example="Story")

class Priority(BaseModel):
    name: str = Field(..., example="High")

class Assignee(BaseModel):
    name: Optional[str] = None
    displayName: Optional[str] = None
    id: Optional[str] = None

class Project(BaseModel):
    key: str = Field(..., example="QA")
    name: Optional[str] = None
    id: Optional[str] = None

class FixVersion(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None

class IssueFields(BaseModel):
    project: Optional[Project] = None
    summary: str = Field(..., example="User can log in with valid credentials")
    description: Optional[Any] = Field(None, description="Plain string or ADF doc object")
    issuetype: IssueType
    priority: Optional[Priority] = None
    assignee: Optional[Any] = Field(None, description="Username string or assignee object")
    reporter: Optional[Any] = Field(None, description="Username string or reporter object")
    labels: Optional[List[str]] = Field(default_factory=list)
    components: Optional[List[Any]] = Field(default_factory=list)
    status: Optional[str] = None
    # Story fields
    customfield_10016: Optional[int] = Field(None, description="Story Points")
    customfield_10020: Optional[Any] = Field(None, description="Sprint")
    customfield_10014: Optional[str] = Field(None, description="Epic Link")
    # Bug fields
    environment: Optional[Any] = Field(None, description="Environment (plain text or ADF doc)")
    fixVersions: Optional[List[Any]] = Field(default_factory=list)
    duedate: Optional[str] = None

class IssueCreate(BaseModel):
    fields: IssueFields

    class Config:
        json_schema_extra = {
            "example": {
                "fields": {
                    "project": {"key": "QA"},
                    "summary": "User can log in with valid credentials",
                    "description": "As a user I want to log in so that I can access the system.\n\nACCEPTANCE CRITERIA\nAC1 - Valid login redirects to dashboard.",
                    "issuetype": {"name": "Story"},
                    "priority": {"name": "High"},
                    "assignee": "jane.smith",
                    "labels": ["auth", "ui"],
                    "customfield_10016": 3,
                    "customfield_10020": "Sprint 1"
                }
            }
        }

class IssueUpdate(BaseModel):
    fields: dict = Field(..., description="Fields to update")

    class Config:
        json_schema_extra = {
            "example": {
                "fields": {
                    "summary": "Updated summary",
                    "priority": {"name": "Critical"},
                    "customfield_10016": 5
                }
            }
        }

class TransitionRequest(BaseModel):
    transition: dict = Field(..., example={"id": "2"})

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

class ResetResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def require_bearer(authorization: Optional[str]):
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Required: Authorization: Bearer mock-jira-token-2025"
        )
    token = authorization[7:].strip()
    if token != VALID_API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token. Only the mock API token is accepted. See /docs for the correct token."
        )


def extract_text_from_adf(node: Any) -> str:
    """Recursively extract plain text from an ADF document node."""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        parts = []
        for child in node.get("content", []):
            parts.append(extract_text_from_adf(child))
        return "\n".join(p for p in parts if p)
    return ""


def to_adf(text: Optional[str]) -> Optional[dict]:
    """Wrap plain text in minimal ADF doc format."""
    if not text:
        return None
    paragraphs = text.split("\n\n")
    content = []
    for para in paragraphs:
        lines = para.strip()
        if lines:
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": lines}]
            })
    if not content:
        return None
    return {"type": "doc", "version": 1, "content": content}


def parse_description(raw: Any) -> str:
    """Accept ADF dict or plain string, return plain text for storage."""
    if raw is None:
        return ""
    if isinstance(raw, dict):
        return extract_text_from_adf(raw)
    return str(raw)


def parse_assignee_input(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, dict):
        return val.get("displayName") or val.get("name") or val.get("id")
    return str(val)


def parse_reporter_input(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, dict):
        return val.get("displayName") or val.get("name") or val.get("id")
    return str(val)


def parse_components_input(val: Any) -> List[dict]:
    if not val:
        return []
    result = []
    for c in val:
        if isinstance(c, dict):
            result.append({"name": c.get("name", c.get("id", ""))})
        else:
            result.append({"name": str(c)})
    return result


def parse_fix_versions_input(val: Any) -> List[dict]:
    if not val:
        return []
    result = []
    for v in val:
        if isinstance(v, dict):
            result.append({"name": v.get("name", v.get("id", ""))})
        else:
            result.append({"name": str(v)})
    return result


def parse_sprint_input(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, dict):
        return val.get("name") or val.get("id")
    if isinstance(val, list) and val:
        first = val[0]
        if isinstance(first, dict):
            return first.get("name") or first.get("id")
        return str(first)
    return str(val)


TRANSITIONS = {
    "To Do": [
        {"id": "2", "name": "In Progress", "to": {"name": "In Progress", "statusCategory": {"name": "In Progress"}}},
    ],
    "In Progress": [
        {"id": "3", "name": "Done", "to": {"name": "Done", "statusCategory": {"name": "Done"}}},
        {"id": "1", "name": "To Do", "to": {"name": "To Do", "statusCategory": {"name": "To Do"}}},
    ],
    "Done": [
        {"id": "1", "name": "To Do", "to": {"name": "To Do", "statusCategory": {"name": "To Do"}}},
        {"id": "2", "name": "In Progress", "to": {"name": "In Progress", "statusCategory": {"name": "In Progress"}}},
    ],
}

TRANSITION_ID_TO_STATUS = {"1": "To Do", "2": "In Progress", "3": "Done"}


def build_issue_response(row) -> dict:
    """Build a full Jira-like issue response dict from a DB row."""
    created = row["created_on"] or None
    updated = row["updated_on"] or created
    priority_name = row["priority"] or "Medium"
    assignee_val = row["assignee"]
    reporter_val = row["reporter"]
    status_val = row["status"] or "To Do"

    labels_parsed = []
    if row["labels"]:
        try:
            labels_parsed = json.loads(row["labels"])
        except Exception:
            labels_parsed = []

    components_parsed = []
    if row["components"]:
        try:
            components_parsed = json.loads(row["components"])
        except Exception:
            components_parsed = []

    fix_versions_parsed = []
    if row["fix_versions"]:
        try:
            fix_versions_parsed = json.loads(row["fix_versions"])
        except Exception:
            fix_versions_parsed = []

    description_adf = to_adf(row["description"])

    environment_adf = to_adf(row["environment"]) if row["environment"] else None

    sprint_val = row["sprint"]
    sprint_field = None
    if sprint_val:
        sprint_field = [{"id": 1, "name": sprint_val, "state": "active"}]

    result = {
        "id": str(row["id"]),
        "key": row["key"],
        "self": f"/rest/api/3/issue/{row['key']}",
        "fields": {
            "project": {"key": PROJECT_KEY, "name": PROJECT_NAME},
            "summary": row["summary"],
            "description": description_adf,
            "issuetype": {"name": row["issue_type"] or "Task"},
            "priority": {"name": priority_name},
            "status": {
                "name": status_val,
                "statusCategory": {"name": status_val}
            },
            "assignee": ({"accountId": assignee_val, "displayName": assignee_val} if assignee_val else None),
            "reporter": {"accountId": reporter_val or "mock-reporter", "displayName": reporter_val or "Mock Reporter"},
            "created": created,
            "updated": updated,
            "labels": labels_parsed,
            "components": components_parsed,
            "comments": [],
            "attachment": [],
            "resolution": None,
            # Story fields
            "customfield_10016": row["story_points"],
            "customfield_10020": sprint_field,
            "customfield_10014": row["epic_link"],
            # Bug fields
            "environment": environment_adf,
            "fixVersions": fix_versions_parsed,
            "duedate": row["due_date"],
        }
    }
    return result


def apply_field_updates(fields: dict) -> dict:
    """Parse a fields dict from PUT/PATCH body into DB column updates."""
    updates = {}
    if "summary" in fields:
        updates["summary"] = fields["summary"]
    if "description" in fields:
        updates["description"] = parse_description(fields["description"])
    if "issuetype" in fields and isinstance(fields["issuetype"], dict):
        updates["issue_type"] = fields["issuetype"].get("name")
    if "priority" in fields:
        p = fields["priority"]
        updates["priority"] = p.get("name") if isinstance(p, dict) else p
    if "assignee" in fields:
        updates["assignee"] = parse_assignee_input(fields["assignee"])
    if "reporter" in fields:
        updates["reporter"] = parse_reporter_input(fields["reporter"])
    if "labels" in fields:
        updates["labels"] = json.dumps(fields.get("labels", []))
    if "components" in fields:
        updates["components"] = json.dumps(parse_components_input(fields.get("components", [])))
    if "status" in fields:
        s = fields["status"]
        updates["status"] = s.get("name") if isinstance(s, dict) else s
    # Story fields
    if "customfield_10016" in fields:
        sp = fields["customfield_10016"]
        updates["story_points"] = int(sp) if sp is not None else None
    if "customfield_10020" in fields:
        updates["sprint"] = parse_sprint_input(fields["customfield_10020"])
    if "customfield_10014" in fields:
        updates["epic_link"] = fields["customfield_10014"]
    # Bug fields
    if "environment" in fields:
        updates["environment"] = parse_description(fields["environment"])
    if "fixVersions" in fields:
        updates["fix_versions"] = json.dumps(parse_fix_versions_input(fields.get("fixVersions", [])))
    if "duedate" in fields:
        updates["due_date"] = fields["duedate"]
    return updates


# ---------------------------------------------------------------------------
# DB startup / migration
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        summary TEXT,
        description TEXT,
        issue_type TEXT DEFAULT 'Task',
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'To Do',
        assignee TEXT,
        reporter TEXT DEFAULT 'mock-reporter',
        labels TEXT DEFAULT '[]',
        components TEXT DEFAULT '[]',
        story_points INTEGER,
        sprint TEXT,
        epic_link TEXT,
        environment TEXT,
        fix_versions TEXT DEFAULT '[]',
        due_date TEXT,
        created_on TEXT,
        updated_on TEXT
    )
    """)
    conn.commit()

    # Migration: add any missing columns to existing tables
    c.execute("PRAGMA table_info(issues)")
    existing_cols = {r[1] for r in c.fetchall()}
    migrations = {
        "priority": "ALTER TABLE issues ADD COLUMN priority TEXT DEFAULT 'Medium'",
        "status": "ALTER TABLE issues ADD COLUMN status TEXT DEFAULT 'To Do'",
        "assignee": "ALTER TABLE issues ADD COLUMN assignee TEXT",
        "reporter": "ALTER TABLE issues ADD COLUMN reporter TEXT DEFAULT 'mock-reporter'",
        "labels": "ALTER TABLE issues ADD COLUMN labels TEXT DEFAULT '[]'",
        "components": "ALTER TABLE issues ADD COLUMN components TEXT DEFAULT '[]'",
        "story_points": "ALTER TABLE issues ADD COLUMN story_points INTEGER",
        "sprint": "ALTER TABLE issues ADD COLUMN sprint TEXT",
        "epic_link": "ALTER TABLE issues ADD COLUMN epic_link TEXT",
        "environment": "ALTER TABLE issues ADD COLUMN environment TEXT",
        "fix_versions": "ALTER TABLE issues ADD COLUMN fix_versions TEXT DEFAULT '[]'",
        "due_date": "ALTER TABLE issues ADD COLUMN due_date TEXT",
        "updated_on": "ALTER TABLE issues ADD COLUMN updated_on TEXT",
    }
    for col, sql in migrations.items():
        if col not in existing_cols:
            try:
                c.execute(sql)
            except Exception:
                pass
    conn.commit()
    conn.close()

    # Seed if empty
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(1) as cnt FROM issues")
    if c.fetchone()[0] == 0:
        seed_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "seed", "sample_issues.json"))
        if os.path.exists(seed_path):
            with open(seed_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for item in data:
                f = item.get("fields", {})
                c.execute("""INSERT INTO issues
                    (key, summary, description, issue_type, priority, status,
                     assignee, reporter, labels, components,
                     story_points, sprint, epic_link,
                     environment, fix_versions, due_date,
                     created_on, updated_on)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))""",
                    (
                        item.get("key"),
                        f.get("summary", ""),
                        parse_description(f.get("description", "")),
                        f.get("issuetype", {}).get("name", "Task"),
                        f.get("priority", {}).get("name", "Medium") if isinstance(f.get("priority"), dict) else f.get("priority", "Medium"),
                        f.get("status", "To Do"),
                        parse_assignee_input(f.get("assignee")),
                        parse_reporter_input(f.get("reporter")) or "mock-reporter",
                        json.dumps(f.get("labels", [])),
                        json.dumps(parse_components_input(f.get("components", []))),
                        f.get("customfield_10016"),
                        parse_sprint_input(f.get("customfield_10020")),
                        f.get("customfield_10014"),
                        parse_description(f.get("environment", "")),
                        json.dumps(parse_fix_versions_input(f.get("fixVersions", []))),
                        f.get("duedate"),
                    ))
            conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/ui", status_code=302)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    return {"status": "ok", "service": "jira-mock", "version": "2.0.0"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# --- Issues CRUD ---

@app.post("/rest/api/3/issue", tags=["Issues"], status_code=201,
          summary="Create Issue")
async def create_issue(issue: IssueCreate, authorization: Optional[str] = Header(None)):
    require_bearer(authorization)
    f = issue.fields
    summary = f.summary or "No summary"
    description = parse_description(f.description)
    issue_type = f.issuetype.name if f.issuetype else "Task"
    priority = f.priority.name if f.priority else "Medium"
    status = "To Do"
    assignee = parse_assignee_input(f.assignee)
    reporter = parse_reporter_input(f.reporter) or "mock-reporter"
    labels = json.dumps(f.labels or [])
    components = json.dumps(parse_components_input(f.components or []))
    story_points = f.customfield_10016
    sprint = parse_sprint_input(f.customfield_10020)
    epic_link = f.customfield_10014
    environment = parse_description(f.environment)
    fix_versions = json.dumps(parse_fix_versions_input(f.fixVersions or []))
    due_date = f.duedate

    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO issues
        (key, summary, description, issue_type, priority, status,
         assignee, reporter, labels, components,
         story_points, sprint, epic_link,
         environment, fix_versions, due_date,
         created_on, updated_on)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))""",
        (None, summary, description, issue_type, priority, status,
         assignee, reporter, labels, components,
         story_points, sprint, epic_link,
         environment, fix_versions, due_date))
    issue_id = c.lastrowid
    key = f"{PROJECT_KEY}-{issue_id}"
    c.execute("UPDATE issues SET key=? WHERE id=?", (key, issue_id))
    conn.commit()
    c.execute("SELECT * FROM issues WHERE id=?", (issue_id,))
    row = c.fetchone()
    conn.close()

    return JSONResponse(status_code=201, content=build_issue_response(row))


@app.get("/rest/api/3/issue/{issue_key}", tags=["Issues"], summary="Get Issue")
async def get_issue(
    issue_key: str = Path(..., example="QA-1"),
    authorization: Optional[str] = Header(None)
):
    require_bearer(authorization)
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM issues WHERE key=?", (issue_key,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Issue not found")
    return build_issue_response(row)


@app.put("/rest/api/3/issue/{issue_key}", tags=["Issues"], summary="Edit Issue",
         status_code=204)
async def edit_issue(
    request: Request,
    issue_key: str = Path(..., example="QA-1"),
    authorization: Optional[str] = Header(None)
):
    """Real Jira uses PUT for edits; returns 204 No Content on success."""
    require_bearer(authorization)
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    fields = payload.get("fields") or {}
    update = payload.get("update") or {}

    # Merge update block into fields (handle add/set/remove ops for labels etc.)
    for field_name, ops in update.items():
        if isinstance(ops, list):
            for op in ops:
                if "set" in op:
                    fields[field_name] = op["set"]
                elif "add" in op and field_name == "labels":
                    fields.setdefault("labels", [])
                    if isinstance(fields["labels"], list):
                        fields["labels"].append(op["add"])

    updates = apply_field_updates(fields)
    if not updates:
        raise HTTPException(status_code=400, detail="No updatable fields provided")

    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM issues WHERE key=?", (issue_key,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    set_clause = ", ".join([f"{k}=?" for k in updates.keys()]) + ", updated_on=datetime('now')"
    params = list(updates.values()) + [issue_key]
    c.execute(f"UPDATE issues SET {set_clause} WHERE key=?", params)
    conn.commit()
    conn.close()
    return Response(status_code=204)


@app.patch("/rest/api/3/issue/{issue_key}", tags=["Issues"], summary="Update Issue (PATCH)",
           status_code=204)
async def update_issue(
    request: Request,
    issue_key: str = Path(..., example="QA-1"),
    authorization: Optional[str] = Header(None)
):
    """Backward-compatible PATCH endpoint — delegates to PUT logic."""
    return await edit_issue(request, issue_key=issue_key, authorization=authorization)


@app.delete("/rest/api/3/issue/{issue_key}", tags=["Issues"], summary="Delete Issue",
            status_code=204)
async def delete_issue(
    issue_key: str = Path(..., example="QA-1"),
    authorization: Optional[str] = Header(None)
):
    require_bearer(authorization)
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM issues WHERE key=?", (issue_key,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")
    c.execute("DELETE FROM issues WHERE key=?", (issue_key,))
    conn.commit()
    conn.close()
    return Response(status_code=204)


# --- Transitions ---

@app.get("/rest/api/3/issue/{issue_key}/transitions", tags=["Issues"],
         summary="Get Transitions")
async def get_transitions(
    issue_key: str = Path(..., example="QA-1"),
    authorization: Optional[str] = Header(None)
):
    require_bearer(authorization)
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT status FROM issues WHERE key=?", (issue_key,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Issue not found")
    current_status = row["status"] or "To Do"
    return {"transitions": TRANSITIONS.get(current_status, [])}


@app.post("/rest/api/3/issue/{issue_key}/transitions", tags=["Issues"],
          summary="Transition Issue", status_code=204)
async def transition_issue(
    request: Request,
    issue_key: str = Path(..., example="QA-1"),
    authorization: Optional[str] = Header(None)
):
    require_bearer(authorization)
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    transition_id = str(payload.get("transition", {}).get("id", ""))
    if transition_id not in TRANSITION_ID_TO_STATUS:
        raise HTTPException(status_code=400, detail=f"Invalid transition id: {transition_id}")

    new_status = TRANSITION_ID_TO_STATUS[transition_id]
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM issues WHERE key=?", (issue_key,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")
    c.execute("UPDATE issues SET status=?, updated_on=datetime('now') WHERE key=?",
              (new_status, issue_key))
    conn.commit()
    conn.close()
    return Response(status_code=204)


# --- Search ---

@app.get("/rest/api/3/search", tags=["Issues"], summary="Search Issues")
async def search_issues(
    jql: Optional[str] = Query(None, description="JQL filter, e.g. 'issuetype = Story'"),
    startAt: int = Query(0, ge=0),
    maxResults: int = Query(50, ge=1, le=100),
    fields: Optional[str] = Query(None, description="Comma-separated fields to return"),
    authorization: Optional[str] = Header(None)
):
    require_bearer(authorization)

    conditions = []
    params = []

    if jql:
        # Simple JQL parsing: issuetype = X / status = X / project = X
        type_match = re.search(r'issuetype\s*=\s*["\']?(\w+)["\']?', jql, re.I)
        status_match = re.search(r'status\s*=\s*["\']?([^"\'&]+?)["\']?(?:\s|$)', jql, re.I)
        project_match = re.search(r'project\s*=\s*["\']?(\w+)["\']?', jql, re.I)

        if type_match:
            conditions.append("LOWER(issue_type) = LOWER(?)")
            params.append(type_match.group(1))
        if status_match:
            conditions.append("LOWER(status) = LOWER(?)")
            params.append(status_match.group(1).strip())
        if project_match:
            pass  # single project mock — ignore

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    conn = get_db_conn()
    c = conn.cursor()
    c.execute(f"SELECT COUNT(1) FROM issues {where_clause}", params)
    total = c.fetchone()[0]
    c.execute(f"SELECT * FROM issues {where_clause} ORDER BY id DESC LIMIT ? OFFSET ?",
              params + [maxResults, startAt])
    rows = c.fetchall()
    conn.close()

    issues = []
    for r in rows:
        resp = build_issue_response(r)
        if fields:
            wanted = set(fields.split(","))
            resp["fields"] = {k: v for k, v in resp["fields"].items() if k in wanted}
        issues.append(resp)

    return {"startAt": startAt, "maxResults": maxResults, "total": total, "issues": issues}


# --- Admin ---

@app.post("/admin/reset", tags=["Admin"], summary="Reset Database")
async def admin_reset(authorization: Optional[str] = Header(None)):
    require_bearer(authorization)
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError:
            pass
    await startup()
    return {"status": "reset"}


# ---------------------------------------------------------------------------
# UI Routes
# ---------------------------------------------------------------------------

def _get_issue_for_ui(key: str) -> dict:
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM issues WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    r = build_issue_response(row)
    issue = dict(r["fields"])
    issue["key"] = r["key"]
    issue["id"] = r["id"]
    # Flatten description back to plain text for UI editing
    issue["description_text"] = row["description"] or ""
    issue["environment_text"] = row["environment"] or ""
    issue["sprint_text"] = row["sprint"] or ""
    issue["story_points"] = row["story_points"]
    issue["epic_link"] = row["epic_link"]
    issue["due_date_val"] = row["due_date"] or ""
    return issue


@app.get("/ui", response_class=HTMLResponse, tags=["UI"], summary="Issue List")
async def ui_index(
    request: Request,
    filter_type: Optional[str] = Query(None),
    filter_status: Optional[str] = Query(None)
):
    conn = get_db_conn()
    c = conn.cursor()
    conditions = []
    params = []
    if filter_type:
        conditions.append("LOWER(issue_type) = LOWER(?)")
        params.append(filter_type)
    if filter_status:
        conditions.append("LOWER(status) = LOWER(?)")
        params.append(filter_status)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    c.execute(f"SELECT * FROM issues {where} ORDER BY id DESC LIMIT 200", params)
    rows = c.fetchall()
    conn.close()
    issues = [dict(r) for r in rows]
    # Parse labels for display
    for iss in issues:
        try:
            iss["labels_list"] = json.loads(iss.get("labels") or "[]")
        except Exception:
            iss["labels_list"] = []
    return templates.TemplateResponse("index.html", {
        "request": request,
        "issues": issues,
        "filter_type": filter_type or "",
        "filter_status": filter_status or "",
    })


@app.post("/ui/create", tags=["UI"], summary="Create Issue (Form)")
async def ui_create(
    summary: str = Form(...),
    description: str = Form(""),
    issue_type: str = Form("Story"),
    priority: str = Form("Medium"),
    assignee: str = Form(""),
    story_points: str = Form(""),
    sprint: str = Form(""),
    epic_link: str = Form(""),
    environment: str = Form(""),
    fix_versions: str = Form(""),
    due_date: str = Form(""),
):
    sp = int(story_points) if story_points.strip().isdigit() else None
    fv = json.dumps([{"name": v.strip()} for v in fix_versions.split(",") if v.strip()]) if fix_versions.strip() else "[]"
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO issues
        (key, summary, description, issue_type, priority, status,
         assignee, reporter, labels, components,
         story_points, sprint, epic_link,
         environment, fix_versions, due_date,
         created_on, updated_on)
        VALUES (?,?,?,?,?,'To Do',?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))""",
        (None, summary, description, issue_type, priority,
         assignee or None, "mock-reporter", "[]", "[]",
         sp, sprint or None, epic_link or None,
         environment or None, fv, due_date or None))
    issue_id = c.lastrowid
    key = f"{PROJECT_KEY}-{issue_id}"
    c.execute("UPDATE issues SET key=? WHERE id=?", (key, issue_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/ui/issue/{key}", status_code=303)


@app.get("/ui/issue/{key}", response_class=HTMLResponse, tags=["UI"],
         summary="Issue Detail")
async def ui_issue_detail(request: Request, key: str):
    issue = _get_issue_for_ui(key)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return templates.TemplateResponse("issue_detail.html", {"request": request, "issue": issue})


@app.post("/ui/issue/{key}/edit", tags=["UI"], summary="Edit Issue (Form)")
async def ui_issue_edit(
    key: str,
    summary: str = Form(...),
    description: str = Form(""),
    priority: str = Form("Medium"),
    assignee: str = Form(""),
    status: str = Form("To Do"),
    story_points: str = Form(""),
    sprint: str = Form(""),
    epic_link: str = Form(""),
    environment: str = Form(""),
    fix_versions: str = Form(""),
    due_date: str = Form(""),
    labels: str = Form(""),
):
    sp = int(story_points) if story_points.strip().isdigit() else None
    fv = json.dumps([{"name": v.strip()} for v in fix_versions.split(",") if v.strip()]) if fix_versions.strip() else "[]"
    labels_list = json.dumps([l.strip() for l in labels.split(",") if l.strip()])
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM issues WHERE key=?", (key,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")
    c.execute("""UPDATE issues SET
        summary=?, description=?, priority=?, assignee=?, status=?,
        story_points=?, sprint=?, epic_link=?,
        environment=?, fix_versions=?, due_date=?,
        labels=?, updated_on=datetime('now')
        WHERE key=?""",
        (summary, description, priority, assignee or None, status,
         sp, sprint or None, epic_link or None,
         environment or None, fv, due_date or None,
         labels_list, key))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/ui/issue/{key}", status_code=303)


@app.post("/ui/issue/{key}/transition", tags=["UI"], summary="Transition Status (Form)")
async def ui_transition(key: str, status: str = Form(...)):
    valid = {"To Do", "In Progress", "Done"}
    if status not in valid:
        raise HTTPException(status_code=400, detail="Invalid status")
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM issues WHERE key=?", (key,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")
    c.execute("UPDATE issues SET status=?, updated_on=datetime('now') WHERE key=?",
              (status, key))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/ui/issue/{key}", status_code=303)


@app.post("/ui/issue/{key}/delete", tags=["UI"], summary="Delete Issue (Form)")
async def ui_delete(key: str):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("DELETE FROM issues WHERE key=?", (key,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/ui", status_code=303)
