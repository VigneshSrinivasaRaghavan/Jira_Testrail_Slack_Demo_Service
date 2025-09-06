from fastapi import FastAPI, Request, HTTPException, Header, Form, Response, Query, Path
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List
import sqlite3
import os
import json

app = FastAPI(
    title="Jira Mock Service",
    description="""
    ## Mock Jira REST API v3 for Testing & Demos
    
    This service mimics core Jira Cloud REST API endpoints for educational purposes.
    Perfect for testing agentic AI integrations without real Jira credentials.
    
    ### Authentication
    All API endpoints require `Authorization: Bearer <token>` header (any token accepted).
    
    ### Key Features
    - ✅ Create, read, update, delete issues
    - ✅ Search/list issues with pagination  
    - ✅ Realistic field support (assignee, priority, labels, components)
    - ✅ Admin reset functionality
    - ✅ Simple web UI for visual inspection
    - ✅ SQLite persistence with seed data
    
    ### Quick Start
    1. **Health Check**: `GET /health`
    2. **List Issues**: `GET /rest/api/3/search` (with auth)
    3. **Create Issue**: `POST /rest/api/3/issue` (with auth + JSON payload)
    4. **View UI**: `GET /ui` (no auth required)
    
    ### Supported Issue Fields
    - `summary`, `description`, `issuetype`
    - `assignee`, `reporter`, `priority` 
    - `labels` (array), `components` (array)
    - `created`, `updated` (auto-managed)
    - `project`, `status` (fixed values)
    """,
    version="1.0.0",
    contact={
        "name": "Mock Services",
        "url": "https://github.com/your-repo/mock-services",
    },
    license_info={
        "name": "MIT",
    },
)

# Templates & static
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

DB_PATH = os.path.join(os.path.dirname(__file__), "jira.db")

# Pydantic response models for OpenAPI documentation
class IssueTypeResponse(BaseModel):
    name: str = Field(..., example="Bug", description="Issue type name")

class PriorityResponse(BaseModel):
    name: str = Field(..., example="High", description="Priority level")

class ProjectResponse(BaseModel):
    key: str = Field(..., example="QA", description="Project key")
    name: str = Field(..., example="QA Project", description="Project name")

class StatusResponse(BaseModel):
    name: str = Field(..., example="To Do", description="Status name")
    statusCategory: dict = Field(..., example={"name": "To Do"}, description="Status category")

class AssigneeResponse(BaseModel):
    displayName: str = Field(..., example="John Doe", description="Display name of assignee")

class ReporterResponse(BaseModel):
    accountId: str = Field(..., example="mock-reporter", description="Account ID")
    displayName: str = Field(..., example="Mock Reporter", description="Display name")

class IssueFieldsResponse(BaseModel):
    project: ProjectResponse
    summary: str = Field(..., example="Login page not loading", description="Issue summary")
    description: str = Field(..., example="When clicking login, page shows 404 error", description="Issue description")
    issuetype: IssueTypeResponse
    priority: PriorityResponse
    status: StatusResponse
    assignee: Optional[AssigneeResponse] = Field(None, description="Assigned user (null if unassigned)")
    reporter: ReporterResponse
    created: str = Field(..., example="2025-09-06 16:51:17", description="Creation timestamp")
    updated: str = Field(..., example="2025-09-06 16:55:20", description="Last update timestamp")
    labels: List[str] = Field(..., example=["ui", "critical"], description="Issue labels")
    components: List[dict] = Field(..., example=[{"name": "frontend"}], description="Components affected")
    comments: List[dict] = Field(..., example=[], description="Comments (empty in mock)")
    attachment: List[dict] = Field(..., example=[], description="Attachments (empty in mock)")
    resolution: Optional[str] = Field(None, example=None, description="Resolution (null for open issues)")

class IssueResponse(BaseModel):
    id: int = Field(..., example=1, description="Internal issue ID")
    key: str = Field(..., example="QA-1", description="Issue key")
    self: str = Field(..., example="/rest/api/3/issue/QA-1", description="Self URL")
    fields: IssueFieldsResponse

class IssueCreateResponse(BaseModel):
    id: dict = Field(..., example={"id": "4"}, description="Issue ID object")
    key: str = Field(..., example="QA-4", description="Generated issue key")
    self: str = Field(..., example="/rest/api/3/issue/QA-4", description="Self URL")
    fields: IssueFieldsResponse

class SearchIssueItem(BaseModel):
    id: int = Field(..., example=1, description="Issue ID")
    key: str = Field(..., example="QA-1", description="Issue key")
    fields: dict = Field(..., example={"summary": "Sample issue"}, description="Basic issue fields")

class SearchResponse(BaseModel):
    startAt: int = Field(..., example=0, description="Starting index")
    maxResults: int = Field(..., example=50, description="Maximum results requested")
    total: int = Field(..., example=3, description="Total number of issues found")
    issues: List[SearchIssueItem] = Field(..., description="List of issues")

class HealthResponse(BaseModel):
    status: str = Field(..., example="ok", description="Service status")
    service: str = Field(..., example="jira-mock", description="Service name")
    version: str = Field(..., example="1.0.0", description="Service version")

class ResetResponse(BaseModel):
    status: str = Field(..., example="reset", description="Reset operation status")

# Input models for OpenAPI documentation
class IssueType(BaseModel):
    name: str = Field(..., example="Bug", description="Issue type name")

class Priority(BaseModel):
    name: str = Field(..., example="High", description="Priority level")

class Assignee(BaseModel):
    name: Optional[str] = Field(None, example="john.doe", description="Username of assignee")
    displayName: Optional[str] = Field(None, example="John Doe", description="Display name")

class Project(BaseModel):
    key: str = Field(..., example="QA", description="Project key")
    name: Optional[str] = Field(None, example="QA Project", description="Project name")

class IssueFields(BaseModel):
    project: Optional[Project] = Field(None, description="Project information")
    summary: str = Field(..., example="Login page not loading", description="Brief issue summary")
    description: Optional[str] = Field("", example="When clicking login, page shows 404 error", description="Detailed description")
    issuetype: IssueType = Field(..., description="Type of issue")
    priority: Optional[Priority] = Field(None, description="Issue priority")
    assignee: Optional[str] = Field(None, example="jane.smith", description="Assignee username")
    reporter: Optional[str] = Field(None, example="john.doe", description="Reporter username")
    labels: Optional[List[str]] = Field([], example=["ui", "critical"], description="Issue labels")
    components: Optional[List[str]] = Field([], example=["frontend"], description="Components affected")

class IssueCreate(BaseModel):
    fields: IssueFields = Field(..., description="Issue field data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fields": {
                    "project": {"key": "QA"},
                    "summary": "Login page not loading",
                    "description": "When clicking login, page shows 404 error",
                    "issuetype": {"name": "Bug"},
                    "priority": {"name": "High"},
                    "assignee": "jane.smith",
                    "labels": ["ui", "critical"],
                    "components": ["frontend"]
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
                    "assignee": "new.assignee",
                    "priority": {"name": "Critical"},
                    "labels": ["updated", "urgent"]
                }
            }
        }

class IssueForm(BaseModel):
    summary: str
    description: Optional[str] = ""


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def require_bearer(authorization: Optional[str]):
    """Validate Bearer token authorization"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header. Please provide Bearer token.")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header. Must be 'Bearer <token>'.")
    # In mock service, we accept any token after "Bearer "
    token = authorization[7:]  # Remove "Bearer " prefix
    if not token.strip():
        raise HTTPException(status_code=401, detail="Empty Bearer token provided.")


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
            with open(seed_path, "r", encoding="utf-8") as fh:
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
    # Ensure enhanced columns exist (priority, assignee, reporter, labels, components, updated_on)
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("PRAGMA table_info(issues)")
    existing_cols = [r[1] for r in c.fetchall()]
    alters = []
    if "priority" not in existing_cols:
        alters.append("ALTER TABLE issues ADD COLUMN priority TEXT")
    if "assignee" not in existing_cols:
        alters.append("ALTER TABLE issues ADD COLUMN assignee TEXT")
    if "reporter" not in existing_cols:
        alters.append("ALTER TABLE issues ADD COLUMN reporter TEXT")
    if "labels" not in existing_cols:
        alters.append("ALTER TABLE issues ADD COLUMN labels TEXT")
    if "components" not in existing_cols:
        alters.append("ALTER TABLE issues ADD COLUMN components TEXT")
    if "updated_on" not in existing_cols:
        alters.append("ALTER TABLE issues ADD COLUMN updated_on TEXT")
    for s in alters:
        try:
            c.execute(s)
        except Exception:
            pass
    conn.commit()
    conn.close()


def require_bearer(authorization: Optional[str] = Header(None)):
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")


@app.post("/rest/api/3/issue", 
          summary="Create Issue",
          description="""
          Create a new issue in the project.
          
          **Required fields:**
          - `fields.summary`: Brief description of the issue
          - `fields.issuetype.name`: Type of issue (Bug, Task, Story, etc.)
          
          **Optional fields:**
          - `fields.description`: Detailed description
          - `fields.assignee`: Username to assign issue to
          - `fields.priority.name`: Priority level (Low, Medium, High, Critical)
          - `fields.labels`: Array of label strings
          - `fields.components`: Array of component strings
          - `fields.reporter`: Username of reporter
          
          **Authentication:** Requires `Authorization: Bearer <token>` header.
          
          **Returns:** Created issue with generated key (e.g., QA-123) and full field data.
          """,
          tags=["Issues"],
          response_model=IssueCreateResponse,
          responses={
              201: {"description": "Issue created successfully", "model": IssueCreateResponse},
              400: {"description": "Invalid request payload"},
              401: {"description": "Missing or invalid authorization"}
          })
async def create_issue(issue: IssueCreate, authorization: Optional[str] = Header(None)):
    # JSON API: require bearer
    if issue is None:
        raise HTTPException(status_code=400, detail="Missing issue payload")
    require_bearer(authorization)
    fields = issue.fields
    summary = fields.summary or "No summary"
    description = fields.description or ""
    issue_type = fields.issuetype.name if fields.issuetype else "Task"

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

    # Build realistic response fields
    created_ts = None
    # fetch created value
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT created_on FROM issues WHERE id=?", (issue_id,))
    row = c.fetchone()
    if row:
        created_ts = row["created_on"]
    conn.close()

    # If priority/assignee/reporter/labels/components are stored in DB, read them
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT priority, assignee, reporter, labels, components, updated_on FROM issues WHERE id=?", (issue_id,))
    meta = c.fetchone()
    conn.close()

    resp = {
        "id": {"id": str(issue_id)},
        "key": key,
        "self": f"/rest/api/3/issue/{key}",
        "fields": {
            "project": {"key": os.environ.get("JIRA_PROJECT_KEY", "QA"), "name": "QA Project"},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
            "priority": {"name": (meta[0] if meta and meta[0] else "Medium")},
            "status": {"name": "To Do", "statusCategory": {"name": "To Do"}},
            "assignee": ( {"displayName": meta[1]} if meta and meta[1] else None),
            "reporter": ( {"displayName": meta[2]} if meta and meta[2] else {"accountId": "mock-reporter", "displayName": "Mock Reporter"}),
            "created": created_ts,
            "updated": created_ts,
            "labels": (json.loads(meta[3]) if meta and meta[3] else []),
            "components": (json.loads(meta[4]) if meta and meta[4] else []),
            "comments": [],
            "attachment": [],
            "resolution": None
        }
    }

    return JSONResponse(status_code=201, content=resp)


# Form-based quick create from UI
@app.post("/ui/create",
          summary="Web UI - Quick Create Issue",
          description="""
          Form-based issue creation from the web UI.
          
          **Form Fields:**
          - `summary`: Issue summary (required)
          - `description`: Issue description (optional)
          
          **No authentication required** - for demos and quick testing.
          
          **Returns:** Redirect to the created issue detail page.
          """,
          tags=["UI"],
          responses={
              303: {"description": "Redirect to created issue detail page"}
          })
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



@app.get("/",
         summary="Root Redirect",
         description="Redirects to the web UI at `/ui`",
         tags=["UI"],
         responses={302: {"description": "Redirect to UI"}})
async def root_redirect():
    """Redirect root to the UI index."""
    return RedirectResponse(url="/ui", status_code=302)


@app.get("/rest/api/3/issue/{issue_key}",
         summary="Get Issue",
         description="""
         Retrieve a single issue by its key (e.g., QA-123).
         
         **Path Parameters:**
         - `issue_key`: The issue key (e.g., QA-1, QA-123)
         
         **Authentication:** Requires `Authorization: Bearer <token>` header.
         
         **Returns:** Complete issue data including all fields, timestamps, and metadata.
         """,
         tags=["Issues"],
         response_model=IssueResponse,
         responses={
             200: {"description": "Issue retrieved successfully", "model": IssueResponse},
             401: {"description": "Missing or invalid authorization"},
             404: {"description": "Issue not found"}
         })
async def get_issue(issue_key: str = Path(..., example="QA-1", description="Issue key"), 
                   authorization: Optional[str] = Header(None)):
    require_bearer(authorization)
    conn = get_db_conn()
    c = conn.cursor()
    # Select all columns explicitly to handle missing columns gracefully
    c.execute("""SELECT id, key, summary, description, issue_type, created_on, 
                        priority, assignee, reporter, labels, components, updated_on 
                 FROM issues WHERE key=?""", (issue_key,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Build response safely handling None values
    created = row[5] if row[5] else None  # created_on
    updated = row[11] if row[11] else created  # updated_on
    priority_name = row[6] if row[6] else "Medium"  # priority
    assignee_val = row[7]  # assignee
    reporter_val = row[8]  # reporter
    labels_val = row[9]  # labels
    components_val = row[10]  # components
    
    # Parse JSON fields safely
    labels_parsed = []
    components_parsed = []
    if labels_val:
        try:
            labels_parsed = json.loads(labels_val)
        except:
            labels_parsed = []
    if components_val:
        try:
            components_parsed = json.loads(components_val)
        except:
            components_parsed = []
    
    return {
        "id": row[0],  # id
        "key": row[1],  # key
        "self": f"/rest/api/3/issue/{row[1]}",
        "fields": {
            "project": {"key": os.environ.get("JIRA_PROJECT_KEY", "QA"), "name": "QA Project"},
            "summary": row[2],  # summary
            "description": row[3],  # description
            "issuetype": {"name": row[4]},  # issue_type
            "priority": {"name": priority_name},
            "status": {"name": "To Do", "statusCategory": {"name": "To Do"}},
            "assignee": ({"displayName": assignee_val} if assignee_val else None),
            "reporter": ({"displayName": reporter_val} if reporter_val else {"accountId": "mock-reporter", "displayName": "Mock Reporter"}),
            "created": created,
            "updated": updated,
            "labels": labels_parsed,
            "components": components_parsed,
            "comments": [],
            "attachment": [],
            "resolution": None
        }
    }


@app.get("/ui", 
         response_class=HTMLResponse,
         summary="Web UI - Issue List",
         description="""
         Simple web interface showing all issues with a quick-create form.
         
         **No authentication required** - for visual inspection and demos.
         
         **Features:**
         - List all issues with links to details
         - Quick-create form for new issues
         - Real-time updates from API changes
         """,
         tags=["UI"],
         responses={200: {"description": "HTML page with issue list"}})
async def ui_index(request: Request):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM issues ORDER BY id DESC LIMIT 100")
    rows = c.fetchall()
    conn.close()
    issues = [dict(r) for r in rows]
    return templates.TemplateResponse("index.html", {"request": request, "issues": issues})


@app.get("/rest/api/3/search",
         summary="Search Issues",
         description="""
         Search and list issues with pagination support.
         
         **Query Parameters:**
         - `startAt`: Starting index for pagination (default: 0)
         - `maxResults`: Maximum number of results to return (default: 50, max: 100)
         
         **Authentication:** Requires `Authorization: Bearer <token>` header.
         
         **Returns:** Paginated list of issues with summary information.
         """,
         tags=["Issues"],
         response_model=SearchResponse,
         responses={
             200: {"description": "Issues retrieved successfully", "model": SearchResponse},
             401: {"description": "Missing or invalid authorization"}
         })
async def search_issues(
    startAt: int = Query(0, ge=0, description="Starting index for pagination"),
    maxResults: int = Query(50, ge=1, le=100, description="Maximum results to return"),
    authorization: Optional[str] = Header(None)
):
    require_bearer(authorization)
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM issues ORDER BY id DESC LIMIT ? OFFSET ?", (maxResults, startAt))
    rows = c.fetchall()
    conn.close()
    issues = [{"id": r["id"], "key": r["key"], "fields": {"summary": r["summary"]}} for r in rows]
    return {"startAt": startAt, "maxResults": maxResults, "total": len(issues), "issues": issues}



@app.delete("/rest/api/3/issue/{issue_key}",
           summary="Delete Issue",
           description="""
           Permanently delete an issue by its key.
           
           **Path Parameters:**
           - `issue_key`: The issue key to delete (e.g., QA-1)
           
           **Authentication:** Requires `Authorization: Bearer <token>` header.
           
           **Returns:** No content (204) on successful deletion.
           """,
           tags=["Issues"],
           responses={
               204: {"description": "Issue deleted successfully"},
               401: {"description": "Missing or invalid authorization"},
               404: {"description": "Issue not found"}
           })
async def delete_issue(
    issue_key: str = Path(..., example="QA-1", description="Issue key to delete"),
    authorization: Optional[str] = Header(None)
):
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


@app.patch("/rest/api/3/issue/{issue_key}",
          summary="Update Issue", 
          description="""
          Update specific fields of an existing issue.
          
          **Path Parameters:**
          - `issue_key`: The issue key to update (e.g., QA-1)
          
          **Updatable Fields:**
          - `fields.summary`: Issue summary
          - `fields.description`: Issue description  
          - `fields.issuetype.name`: Issue type
          - `fields.assignee`: Assignee username
          - `fields.priority`: Priority name or object
          - `fields.reporter`: Reporter username
          - `fields.labels`: Array of labels
          - `fields.components`: Array of components
          
          **Authentication:** Requires `Authorization: Bearer <token>` header.
          
          **Returns:** Updated issue with all current field values.
          """,
          tags=["Issues"],
          response_model=IssueResponse,
          responses={
              200: {"description": "Issue updated successfully", "model": IssueResponse},
              400: {"description": "Invalid request payload or no updatable fields"},
              401: {"description": "Missing or invalid authorization"},
              404: {"description": "Issue not found"}
          })
async def update_issue(
    request: Request, 
    issue_key: str = Path(..., example="QA-1", description="Issue key to update"),
    authorization: Optional[str] = Header(None)
):
    """Update provided fields on an existing issue. Expects Jira-like payload {"fields": {...}}."""
    require_bearer(authorization)
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    fields = payload.get("fields") if isinstance(payload, dict) else None
    if not fields:
        raise HTTPException(status_code=400, detail="Missing fields payload")

    # allowed updatable columns: summary, description, issue_type
    updates = {}
    if "summary" in fields:
        updates["summary"] = fields["summary"]
    if "description" in fields:
        updates["description"] = fields["description"]
    if "issuetype" in fields and isinstance(fields["issuetype"], dict):
        updates["issue_type"] = fields["issuetype"].get("name")
    # optional updatable fields
    if "priority" in fields:
        updates["priority"] = fields["priority"].get("name") if isinstance(fields["priority"], dict) else fields["priority"]
    if "assignee" in fields:
        # accept string username or object
        if isinstance(fields["assignee"], dict):
            updates["assignee"] = fields["assignee"].get("name")
        else:
            updates["assignee"] = fields["assignee"]
    if "reporter" in fields:
        if isinstance(fields["reporter"], dict):
            updates["reporter"] = fields["reporter"].get("name")
        else:
            updates["reporter"] = fields["reporter"]
    if "labels" in fields:
        # store JSON string of labels
        updates["labels"] = json.dumps(fields.get("labels", []))
    if "components" in fields:
        updates["components"] = json.dumps(fields.get("components", []))

    if not updates:
        raise HTTPException(status_code=400, detail="No updatable fields provided")

    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM issues WHERE key=?", (issue_key,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    # build SET clause
    set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
    params = list(updates.values()) + [issue_key]
    # update updated_on timestamp instead of overwriting created_on
    set_clause_full = set_clause + ", updated_on=datetime('now')"
    c.execute(f"UPDATE issues SET {set_clause_full} WHERE key=?", params)
    conn.commit()
    conn.close()

    # return updated issue
    return await get_issue(issue_key, authorization=authorization)


@app.post("/admin/reset",
          summary="Reset Database",
          description="""
          **⚠️ ADMIN OPERATION ⚠️**
          
          Reset the entire database and reload seed data from `shared/seed/sample_issues.json`.
          This will permanently delete all existing issues and restore the original sample data.
          
          **Use Cases:**
          - Clean up test data during development
          - Reset to known state for demos
          - Clear database after testing
          
          **Authentication:** Requires `Authorization: Bearer <token>` header.
          
          **Returns:** Confirmation message with reset status.
          """,
          tags=["Admin"],
          response_model=ResetResponse,
          responses={
              200: {"description": "Database reset successfully", "model": ResetResponse},
              401: {"description": "Missing or invalid authorization"}
          })
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


@app.get("/ui/issue/{key}", 
         response_class=HTMLResponse,
         summary="Web UI - Issue Detail",
         description="""
         Detailed view of a single issue with all fields displayed.
         
         **Path Parameters:**
         - `key`: Issue key (e.g., QA-1)
         
         **No authentication required** - for visual inspection and demos.
         
         **Features:**
         - Complete issue information display
         - All fields including assignee, priority, labels, etc.
         - Formatted timestamps and metadata
         """,
         tags=["UI"],
         responses={
             200: {"description": "HTML page with issue details"},
             404: {"description": "Issue not found"}
         })
async def ui_issue_detail(request: Request, key: str):
    # Reuse API representation to build template context (keeps UI consistent with API)
    api_issue = await get_issue(key, authorization="Bearer internal")

    # api_issue has shape {id, key, self, fields: {...}}
    fields = api_issue.get("fields", {})
    # Flatten for template: top-level keys used by template (project, reporter, assignee, etc.)
    issue = dict(fields)
    issue["key"] = api_issue.get("key")
    issue["id"] = api_issue.get("id")
    # Ensure nested objects exist for template safety
    issue.setdefault("project", {"key": os.environ.get("JIRA_PROJECT_KEY", "QA"), "name": "QA Project"})
    issue.setdefault("reporter", {"accountId": "mock-reporter", "displayName": "Mock Reporter"})
    issue.setdefault("assignee", None)
    issue.setdefault("labels", [])
    issue.setdefault("components", [])
    issue.setdefault("comments", [])
    issue.setdefault("attachment", [])

    return templates.TemplateResponse("issue_detail.html", {"request": request, "issue": issue})


@app.get("/health",
         summary="Health Check",
         description="""
         Simple health check endpoint to verify the service is running.
         
         **No authentication required.**
         
         **Returns:** Service status information.
         """,
         tags=["System"],
         response_model=HealthResponse,
         responses={
             200: {"description": "Service is healthy", "model": HealthResponse}
         })
async def health():
    """Health check endpoint - no authentication required."""
    return {"status": "ok", "service": "jira-mock", "version": "1.0.0"}
