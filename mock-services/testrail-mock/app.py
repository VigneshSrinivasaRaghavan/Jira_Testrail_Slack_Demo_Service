"""
TestRail Mock Service - Main FastAPI Application
Enhanced TestRail-like test case management system
"""

import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Request, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import uvicorn

from storage import get_database, storage
from routes import api_router
from models import (
    Project, Section, Template, TestCase, TestResult, TestRun, RunEntry,
    TestCaseCreate, TestResultCreate,
    STATUS_NAMES, TYPE_NAMES, PRIORITY_NAMES
)

# Initialize FastAPI app
app = FastAPI(
    title="TestRail Mock Service",
    description="Enhanced TestRail-like test case management and execution tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(api_router)

# Authentication middleware (simple Bearer token check)
def check_auth(request: Request):
    """Simple auth check for API endpoints"""
    if request.url.path.startswith("/api/") or request.url.path.startswith("/index.php"):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
    return True

# Helper functions for templates
def get_status_classes():
    return {
        1: "passed",
        2: "blocked", 
        3: "untested",
        4: "retest",
        5: "failed"
    }

def get_latest_case_statuses(db: Session, case_ids: List[int]):
    """Get latest test result status for each case - ROBUST VERSION"""
    latest_results = {}
    if not case_ids:
        return latest_results
        
    try:
        for case_id in case_ids:
            try:
                result = (db.query(TestResult)
                         .filter(TestResult.case_id == case_id)
                         .order_by(desc(TestResult.created_on))
                         .first())
                if result:
                    latest_results[case_id] = result
            except Exception as e:
                print(f"Error getting status for case {case_id}: {e}")
                continue
    except Exception as e:
        print(f"Error in get_latest_case_statuses: {e}")
        
    return latest_results

# UI Routes
@app.get("/ui", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_database)):
    """Main dashboard"""
    # Get default project (ID=1)
    project = db.query(Project).filter(Project.id == 1).first()
    if not project:
        raise HTTPException(status_code=404, detail="Default project not found")
    
    # Get project statistics
    stats = {"total_cases": 0, "overall_status_counts": {}}
    
    # Get sections with case counts
    sections = db.query(Section).filter(Section.project_id == 1).all()
    section_case_counts = {}
    for section in sections:
        count = db.query(TestCase).filter(TestCase.section_id == section.id).count()
        section_case_counts[section.id] = count
        stats["total_cases"] += count
    
    # Get recent test results
    recent_results = (db.query(TestResult)
                     .join(TestCase)
                     .order_by(desc(TestResult.created_on))
                     .limit(10)
                     .all())
    
    # Get test runs
    test_runs = (db.query(TestRun)
                .filter(TestRun.project_id == 1)
                .order_by(desc(TestRun.created_on))
                .limit(5)
                .all())
    
    # Calculate status counts
    status_counts = {status_id: 0 for status_id in STATUS_NAMES.keys()}
    for result in recent_results:
        status_counts[result.status_id] = status_counts.get(result.status_id, 0) + 1
    
    stats["overall_status_counts"] = status_counts
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "project": project,
        "sections": sections,
        "section_case_counts": section_case_counts,
        "recent_results": recent_results,
        "test_runs": test_runs,
        "stats": stats,
        "status_names": STATUS_NAMES,
        "status_classes": get_status_classes()
    })

@app.get("/ui/cases", response_class=HTMLResponse)
def cases_list(
    request: Request,
    section_id: Optional[str] = Query(None),
    type_id: Optional[str] = Query(None),
    priority_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(25, le=100),
    db: Session = Depends(get_database)
):
    """Test cases list with filtering - ROBUST VERSION"""
    try:
        # Convert string parameters to integers, handling empty strings
        section_id_int = None
        type_id_int = None
        priority_id_int = None
        
        try:
            if section_id and section_id.strip():
                section_id_int = int(section_id)
        except (ValueError, AttributeError):
            section_id_int = None
            
        try:
            if type_id and type_id.strip():
                type_id_int = int(type_id)
        except (ValueError, AttributeError):
            type_id_int = None
            
        try:
            if priority_id and priority_id.strip():
                priority_id_int = int(priority_id)
        except (ValueError, AttributeError):
            priority_id_int = None
        
        # Build query with error handling
        try:
            query = db.query(TestCase).join(Section).filter(Section.project_id == 1)
            
            if section_id_int:
                query = query.filter(TestCase.section_id == section_id_int)
            if type_id_int:
                query = query.filter(TestCase.type_id == type_id_int)
            if priority_id_int:
                query = query.filter(TestCase.priority_id == priority_id_int)
            
            # Get total count
            total_cases = query.count()
            total_pages = max(1, (total_cases + limit - 1) // limit)
            
            # Get paginated results
            offset = (page - 1) * limit
            cases = query.offset(offset).limit(limit).all()
            
        except Exception as e:
            print(f"Error in query: {e}")
            cases = []
            total_cases = 0
            total_pages = 1
        
        # Get sections and case counts with error handling
        try:
            sections = db.query(Section).filter(Section.project_id == 1).all()
            section_case_counts = {}
            for section in sections:
                try:
                    count = db.query(TestCase).filter(TestCase.section_id == section.id).count()
                    section_case_counts[section.id] = count
                except Exception as e:
                    print(f"Error counting cases for section {section.id}: {e}")
                    section_case_counts[section.id] = 0
        except Exception as e:
            print(f"Error getting sections: {e}")
            sections = []
            section_case_counts = {}
        
        # Get case statuses with error handling
        case_statuses = {}
        status_counts = {status_id: 0 for status_id in STATUS_NAMES.keys()}
        
        try:
            if cases:
                case_ids = [case.id for case in cases]
                case_statuses = get_latest_case_statuses(db, case_ids)
        except Exception as e:
            print(f"Error getting case statuses: {e}")
            case_statuses = {}
        
        # Build query params for pagination
        query_params = []
        if section_id_int:
            query_params.append(f"section_id={section_id_int}")
        if type_id_int:
            query_params.append(f"type_id={type_id_int}")
        if priority_id_int:
            query_params.append(f"priority_id={priority_id_int}")
        query_params_str = "&".join(query_params)
        
        return templates.TemplateResponse("cases_list.html", {
            "request": request,
            "cases": cases,
            "sections": sections,
            "section_case_counts": section_case_counts,
            "case_statuses": case_statuses,
            "status_counts": status_counts,
            "total_cases": total_cases,
            "current_page": page,
            "total_pages": total_pages,
            "query_params": query_params_str,
            "current_section_id": section_id_int,
            "current_type_id": type_id_int,
            "current_priority_id": priority_id_int,
            "status_names": STATUS_NAMES,
            "type_names": TYPE_NAMES,
            "priority_names": PRIORITY_NAMES,
            "status_classes": get_status_classes()
        })
        
    except Exception as e:
        print(f"Critical error in cases_list: {e}")
        # Return a minimal working response
        return templates.TemplateResponse("cases_list.html", {
            "request": request,
            "cases": [],
            "sections": [],
            "section_case_counts": {},
            "case_statuses": {},
            "status_counts": {status_id: 0 for status_id in STATUS_NAMES.keys()},
            "total_cases": 0,
            "current_page": 1,
            "total_pages": 1,
            "query_params": "",
            "current_section_id": None,
            "current_type_id": None,
            "current_priority_id": None,
            "status_names": STATUS_NAMES,
            "type_names": TYPE_NAMES,
            "priority_names": PRIORITY_NAMES,
            "status_classes": get_status_classes()
        })

@app.get("/ui/case/{case_id}", response_class=HTMLResponse)
def case_detail(request: Request, case_id: int, db: Session = Depends(get_database)):
    """Test case detail view"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Get execution history
    results = (db.query(TestResult)
              .filter(TestResult.case_id == case_id)
              .order_by(desc(TestResult.created_on))
              .all())
    
    # Get latest result
    latest_result = results[0] if results else None
    
    # Get other cases in same section
    section_cases = (db.query(TestCase)
                    .filter(TestCase.section_id == case.section_id)
                    .order_by(TestCase.title)
                    .all())
    
    return templates.TemplateResponse("testcase_detail.html", {
        "request": request,
        "case": case,
        "results": results,
        "latest_result": latest_result,
        "section_cases": section_cases,
        "status_names": STATUS_NAMES,
        "type_names": TYPE_NAMES,
        "priority_names": PRIORITY_NAMES,
        "status_classes": get_status_classes()
    })

@app.get("/ui/case/{case_id}/execute", response_class=HTMLResponse)
def execute_case_form(request: Request, case_id: int, db: Session = Depends(get_database)):
    """Execute test case form"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    return templates.TemplateResponse("case_execute.html", {
        "request": request,
        "case": case,
        "status_names": STATUS_NAMES,
        "priority_names": PRIORITY_NAMES,
        "type_names": TYPE_NAMES,
        "status_classes": get_status_classes()
    })

@app.post("/ui/case/{case_id}/execute")
def execute_case(
    case_id: int,
    status_id: int = Form(...),
    comment: Optional[str] = Form(None),
    elapsed: Optional[str] = Form(None),
    db: Session = Depends(get_database)
):
    """Execute test case and add result"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Create test result
    result = TestResult(
        case_id=case_id,
        status_id=status_id,
        comment=comment,
        elapsed=elapsed
    )
    db.add(result)
    db.commit()
    
    return RedirectResponse(url=f"/ui/case/{case_id}", status_code=303)

@app.get("/ui/runs", response_class=HTMLResponse)
def runs_list(request: Request, db: Session = Depends(get_database)):
    """Test runs list"""
    # Get test runs for default project
    test_runs = (db.query(TestRun)
                .filter(TestRun.project_id == 1)
                .order_by(desc(TestRun.created_on))
                .all())
    
    return templates.TemplateResponse("runs_list.html", {
        "request": request,
        "test_runs": test_runs,
        "status_names": STATUS_NAMES,
        "status_classes": get_status_classes()
    })

# Test Case Management Routes
@app.get("/ui/cases/create", response_class=HTMLResponse)
def create_case_form(request: Request, db: Session = Depends(get_database)):
    """Create test case form"""
    sections = db.query(Section).filter(Section.project_id == 1).all()
    case_templates = db.query(Template).all()
    
    return templates.TemplateResponse("case_create.html", {
        "request": request,
        "sections": sections,
        "templates": case_templates,
        "type_names": TYPE_NAMES,
        "priority_names": PRIORITY_NAMES
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
    db: Session = Depends(get_database)
):
    """Handle test case creation"""
    # Parse form data to extract steps
    form_data = await request.form()
    steps_data = []
    
    # Extract steps from form data
    step_index = 0
    while f"steps[{step_index}][step]" in form_data:
        step_action = form_data.get(f"steps[{step_index}][step]", "").strip()
        step_expected = form_data.get(f"steps[{step_index}][expected]", "").strip()
        
        if step_action and step_expected:
            steps_data.append({
                "step": step_action,
                "expected": step_expected
            })
        step_index += 1
    
    case = TestCase(
        section_id=section_id,
        title=title,
        template_id=template_id,
        type_id=type_id,
        priority_id=priority_id,
        expected_result=expected_result if expected_result else None,
        preconditions=preconditions if preconditions else None,
        steps=steps_data if steps_data else None
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    return RedirectResponse(url=f"/ui/case/{case.id}", status_code=303)

@app.get("/ui/case/{case_id}/edit", response_class=HTMLResponse)
def edit_case_form(request: Request, case_id: int, db: Session = Depends(get_database)):
    """Edit test case form"""
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
        "priority_names": PRIORITY_NAMES
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
    db: Session = Depends(get_database)
):
    """Handle test case editing"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Parse form data to extract steps
    form_data = await request.form()
    steps_data = []
    
    # Extract steps from form data
    step_index = 0
    while f"steps[{step_index}][step]" in form_data:
        step_action = form_data.get(f"steps[{step_index}][step]", "").strip()
        step_expected = form_data.get(f"steps[{step_index}][expected]", "").strip()
        
        if step_action and step_expected:
            steps_data.append({
                "step": step_action,
                "expected": step_expected
            })
        step_index += 1
    
    case.section_id = section_id
    case.title = title
    case.template_id = template_id
    case.type_id = type_id
    case.priority_id = priority_id
    case.expected_result = expected_result if expected_result else None
    case.preconditions = preconditions if preconditions else None
    case.steps = steps_data if steps_data else None
    
    db.commit()
    
    return RedirectResponse(url=f"/ui/case/{case_id}", status_code=303)

@app.get("/ui/case/{case_id}/copy", response_class=HTMLResponse)
def copy_case_form(request: Request, case_id: int, db: Session = Depends(get_database)):
    """Copy test case form"""
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
        "priority_names": PRIORITY_NAMES
    })

# Section Management Routes
@app.get("/ui/sections/create", response_class=HTMLResponse)
def create_section_form(request: Request, db: Session = Depends(get_database)):
    """Create section form"""
    sections = db.query(Section).filter(Section.project_id == 1).all()
    
    return templates.TemplateResponse("section_create.html", {
        "request": request,
        "sections": sections
    })

@app.post("/ui/sections/create")
def create_section_submit(
    name: str = Form(...),
    description: str = Form(""),
    parent_id: Optional[int] = Form(None),
    db: Session = Depends(get_database)
):
    """Handle section creation"""
    section = Section(
        project_id=1,
        name=name,
        description=description if description else None,
        parent_id=parent_id if parent_id else None
    )
    db.add(section)
    db.commit()
    
    return RedirectResponse(url="/ui/cases", status_code=303)

# Test Run Management Routes
@app.get("/ui/runs/create", response_class=HTMLResponse)
def create_run_form(request: Request, db: Session = Depends(get_database)):
    """Create test run form"""
    sections = db.query(Section).filter(Section.project_id == 1).all()
    
    return templates.TemplateResponse("run_create.html", {
        "request": request,
        "sections": sections
    })

@app.post("/ui/runs/create")
def create_run_submit(
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_database)
):
    """Handle test run creation"""
    run = TestRun(
        project_id=1,
        name=name,
        description=description if description else None
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    return RedirectResponse(url=f"/ui/run/{run.id}", status_code=303)

@app.get("/ui/run/{run_id}", response_class=HTMLResponse)
def run_detail(request: Request, run_id: int, db: Session = Depends(get_database)):
    """Test run detail view"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    # Get run entries with case details
    entries = (db.query(RunEntry)
              .join(TestCase)
              .filter(RunEntry.run_id == run_id)
              .all())
    
    return templates.TemplateResponse("run_detail.html", {
        "request": request,
        "run": run,
        "entries": entries,
        "status_names": STATUS_NAMES,
        "status_classes": get_status_classes()
    })

@app.get("/ui/run/{run_id}/add-cases", response_class=HTMLResponse)
def add_cases_to_run(request: Request, run_id: int, db: Session = Depends(get_database)):
    """Add test cases to run"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    # Get all test cases not already in this run
    existing_case_ids = [entry.case_id for entry in db.query(RunEntry).filter(RunEntry.run_id == run_id).all()]
    available_cases = (db.query(TestCase)
                      .join(Section)
                      .filter(Section.project_id == 1)
                      .filter(~TestCase.id.in_(existing_case_ids))
                      .all())
    
    sections = db.query(Section).filter(Section.project_id == 1).all()
    
    return templates.TemplateResponse("run_add_cases.html", {
        "request": request,
        "run": run,
        "available_cases": available_cases,
        "sections": sections,
        "type_names": TYPE_NAMES,
        "priority_names": PRIORITY_NAMES
    })

@app.post("/ui/run/{run_id}/add-cases")
def add_cases_to_run_submit(
    run_id: int,
    case_ids: list = Form(...),
    db: Session = Depends(get_database)
):
    """Handle adding cases to run"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    # Add selected cases to run
    for case_id in case_ids:
        # Check if case is already in run
        existing = db.query(RunEntry).filter(
            RunEntry.run_id == run_id,
            RunEntry.case_id == case_id
        ).first()
        
        if not existing:
            entry = RunEntry(
                run_id=run_id,
                case_id=int(case_id),
                status_id=3  # Untested
            )
            db.add(entry)
    
    db.commit()
    return RedirectResponse(url=f"/ui/run/{run_id}", status_code=303)

@app.get("/ui/run/{run_id}/complete", response_class=HTMLResponse)
def complete_run(run_id: int, db: Session = Depends(get_database)):
    """Mark test run as complete"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    run.is_completed = True
    db.commit()
    
    return RedirectResponse(url=f"/ui/run/{run_id}", status_code=303)

@app.get("/ui/run/{run_id}/edit", response_class=HTMLResponse)
def edit_run_form(request: Request, run_id: int, db: Session = Depends(get_database)):
    """Edit test run form"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    return templates.TemplateResponse("run_edit.html", {
        "request": request,
        "run": run
    })

@app.post("/ui/run/{run_id}/edit")
def edit_run_submit(
    run_id: int,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_database)
):
    """Handle test run editing"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    run.name = name
    run.description = description if description else None
    db.commit()
    
    return RedirectResponse(url=f"/ui/run/{run_id}", status_code=303)

@app.get("/ui/run/{run_id}/execute", response_class=HTMLResponse)
def execute_run_placeholder(request: Request, run_id: int):
    """Execute test run (placeholder)"""
    return templates.TemplateResponse("placeholder.html", {
        "request": request,
        "feature_name": "Execute Test Run",
        "description": "This feature will allow you to execute all test cases in a run sequentially or assign them to team members.",
        "back_url": f"/ui/run/{run_id}"
    })

@app.get("/ui/run/{run_id}/report", response_class=HTMLResponse)
def generate_run_report_placeholder(request: Request, run_id: int):
    """Generate test run report (placeholder)"""
    return templates.TemplateResponse("placeholder.html", {
        "request": request,
        "feature_name": "Generate Test Run Report",
        "description": "This feature will generate comprehensive reports with charts, statistics, and detailed test results.",
        "back_url": f"/ui/run/{run_id}"
    })

# Placeholder routes for future features
@app.get("/ui/cases/import", response_class=HTMLResponse)
def import_cases_placeholder(request: Request):
    """Import test cases (placeholder)"""
    return templates.TemplateResponse("placeholder.html", {
        "request": request,
        "feature_name": "Import Test Cases",
        "description": "This feature will allow you to import test cases from CSV, Excel, or other TestRail instances.",
        "back_url": "/ui/cases"
    })

@app.get("/ui/section/{section_id}", response_class=HTMLResponse)
def section_view(request: Request, section_id: int, db: Session = Depends(get_database)):
    """Section view with cases"""
    return RedirectResponse(url=f"/ui/cases?section_id={section_id}")

# Health check
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "testrail-mock", "version": "1.0.0"}

# Root redirect
@app.get("/")
def root():
    """Redirect root to UI"""
    return RedirectResponse(url="/ui")

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=4002,
        reload=True,
        log_level="info"
    )
