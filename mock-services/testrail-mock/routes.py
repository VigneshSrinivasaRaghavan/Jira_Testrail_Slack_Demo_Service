"""
TestRail Mock Service - API Routes
Clean REST API with TestRail compatibility
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from storage import get_database
from models import (
    Project, Section, Template, TestCase, TestResult, TestRun, RunEntry,
    ProjectCreate, ProjectResponse, SectionCreate, SectionResponse,
    TestCaseCreate, TestCaseResponse, TestResultCreate, TestResultResponse,
    TestRunCreate, TestRunResponse, STATUS_NAMES, TYPE_NAMES, PRIORITY_NAMES
)

# Create API router
api_router = APIRouter()

# Projects endpoints
@api_router.get("/api/v2/projects", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_database)):
    """Get all projects"""
    projects = db.query(Project).all()
    return projects

@api_router.get("/api/v2/project/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_database)):
    """Get project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@api_router.post("/api/v2/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_database)):
    """Create new project"""
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

# Sections endpoints
@api_router.get("/api/v2/sections/{project_id}", response_model=List[SectionResponse])
def get_sections(project_id: int, db: Session = Depends(get_database)):
    """Get sections for a project"""
    sections = db.query(Section).filter(Section.project_id == project_id).all()
    return sections

@api_router.get("/api/v2/section/{section_id}", response_model=SectionResponse)
def get_section(section_id: int, db: Session = Depends(get_database)):
    """Get section by ID"""
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section

@api_router.post("/api/v2/sections/{project_id}", response_model=SectionResponse)
def create_section(project_id: int, section: SectionCreate, db: Session = Depends(get_database)):
    """Create new section in project"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_section = Section(project_id=project_id, **section.dict())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

# Test Cases endpoints
@api_router.get("/api/v2/cases/{project_id}", response_model=List[TestCaseResponse])
def get_cases(
    project_id: int,
    section_id: Optional[int] = Query(None),
    limit: int = Query(50, le=250),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database)
):
    """Get test cases for a project, optionally filtered by section"""
    query = db.query(TestCase).join(Section).filter(Section.project_id == project_id)
    
    if section_id:
        query = query.filter(TestCase.section_id == section_id)
    
    cases = query.offset(offset).limit(limit).all()
    return cases

@api_router.get("/api/v2/case/{case_id}", response_model=TestCaseResponse)
def get_case(case_id: int, db: Session = Depends(get_database)):
    """Get test case by ID"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return case

@api_router.post("/api/v2/cases/{section_id}", response_model=TestCaseResponse)
def create_case(section_id: int, case: TestCaseCreate, db: Session = Depends(get_database)):
    """Create new test case in section"""
    # Verify section exists
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    db_case = TestCase(section_id=section_id, **case.dict())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@api_router.put("/api/v2/case/{case_id}", response_model=TestCaseResponse)
def update_case(case_id: int, case: TestCaseCreate, db: Session = Depends(get_database)):
    """Update test case"""
    db_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    for field, value in case.dict(exclude_unset=True).items():
        setattr(db_case, field, value)
    
    db.commit()
    db.refresh(db_case)
    return db_case

# Test Results endpoints
@api_router.get("/api/v2/results/{case_id}", response_model=List[TestResultResponse])
def get_results(case_id: int, limit: int = Query(50), db: Session = Depends(get_database)):
    """Get test results for a case"""
    results = (db.query(TestResult)
              .filter(TestResult.case_id == case_id)
              .order_by(desc(TestResult.created_on))
              .limit(limit)
              .all())
    return results

@api_router.post("/api/v2/results/{case_id}", response_model=TestResultResponse)
def create_result(case_id: int, result: TestResultCreate, db: Session = Depends(get_database)):
    """Add test result for a case"""
    # Verify case exists
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Validate status_id
    if result.status_id not in STATUS_NAMES:
        raise HTTPException(status_code=400, detail="Invalid status_id")
    
    db_result = TestResult(case_id=case_id, **result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

# Test Runs endpoints
@api_router.get("/api/v2/runs/{project_id}", response_model=List[TestRunResponse])
def get_runs(project_id: int, db: Session = Depends(get_database)):
    """Get test runs for a project"""
    runs = db.query(TestRun).filter(TestRun.project_id == project_id).all()
    return runs

@api_router.get("/api/v2/run/{run_id}", response_model=TestRunResponse)
def get_run(run_id: int, db: Session = Depends(get_database)):
    """Get test run by ID"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return run

@api_router.post("/api/v2/runs/{project_id}", response_model=TestRunResponse)
def create_run(project_id: int, run: TestRunCreate, db: Session = Depends(get_database)):
    """Create new test run"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_run = TestRun(project_id=project_id, **run.dict())
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

# Legacy TestRail-style endpoints for compatibility
@api_router.post("/index.php", response_model=TestCaseResponse)
def legacy_add_case(section_id: int = Query(..., alias="section_id"), case: TestCaseCreate = None, db: Session = Depends(get_database)):
    """Legacy TestRail endpoint: add_case/{section_id}"""
    return create_case(section_id, case, db)

@api_router.post("/index.php", response_model=TestResultResponse)  
def legacy_add_result(case_id: int = Query(..., alias="case_id"), result: TestResultCreate = None, db: Session = Depends(get_database)):
    """Legacy TestRail endpoint: add_result/{case_id}"""
    return create_result(case_id, result, db)

@api_router.get("/index.php", response_model=TestCaseResponse)
def legacy_get_case(case_id: int = Query(..., alias="case_id"), db: Session = Depends(get_database)):
    """Legacy TestRail endpoint: get_case/{case_id}"""
    return get_case(case_id, db)

# Utility endpoints
@api_router.get("/api/v2/statuses")
def get_statuses():
    """Get available test statuses"""
    return [{"id": k, "name": v} for k, v in STATUS_NAMES.items()]

@api_router.get("/api/v2/types")
def get_types():
    """Get available test case types"""
    return [{"id": k, "name": v} for k, v in TYPE_NAMES.items()]

@api_router.get("/api/v2/priorities")
def get_priorities():
    """Get available priorities"""
    return [{"id": k, "name": v} for k, v in PRIORITY_NAMES.items()]

@api_router.get("/api/v2/templates")
def get_templates(db: Session = Depends(get_database)):
    """Get available templates"""
    templates = db.query(Template).all()
    return [{"id": t.id, "name": t.name, "is_default": t.is_default} for t in templates]

# Health check
@api_router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "testrail-mock"}

# Statistics endpoint
@api_router.get("/api/v2/stats/{project_id}")
def get_project_stats(project_id: int, db: Session = Depends(get_database)):
    """Get project statistics"""
    # Count cases by section
    sections = db.query(Section).filter(Section.project_id == project_id).all()
    section_stats = []
    
    total_cases = 0
    status_counts = {status_id: 0 for status_id in STATUS_NAMES.keys()}
    
    for section in sections:
        case_count = db.query(TestCase).filter(TestCase.section_id == section.id).count()
        total_cases += case_count
        
        # Get latest results for cases in this section
        latest_results = (db.query(TestResult)
                         .join(TestCase)
                         .filter(TestCase.section_id == section.id)
                         .order_by(desc(TestResult.created_on))
                         .all())
        
        section_status_counts = {status_id: 0 for status_id in STATUS_NAMES.keys()}
        for result in latest_results:
            section_status_counts[result.status_id] += 1
            status_counts[result.status_id] += 1
        
        section_stats.append({
            "section_id": section.id,
            "section_name": section.name,
            "case_count": case_count,
            "status_counts": section_status_counts
        })
    
    return {
        "project_id": project_id,
        "total_cases": total_cases,
        "sections": section_stats,
        "overall_status_counts": status_counts
    }
