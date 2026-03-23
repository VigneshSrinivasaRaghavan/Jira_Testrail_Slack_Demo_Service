"""
TestRail Mock Service - Database Models
"""

from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel

Base = declarative_base()


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Models
# ---------------------------------------------------------------------------

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    announcement = Column(Text, nullable=True)
    show_announcement = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    created_on = Column(DateTime, default=datetime.utcnow)

    sections = relationship("Section", back_populates="project", cascade="all, delete-orphan")
    runs = relationship("TestRun", back_populates="project", cascade="all, delete-orphan")


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    depth = Column(Integer, default=0)
    display_order = Column(Integer, default=1)
    created_on = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="sections")
    parent = relationship("Section", remote_side=[id], backref="children")
    cases = relationship("TestCase", back_populates="section", cascade="all, delete-orphan")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    is_default = Column(Boolean, default=False)

    cases = relationship("TestCase", back_populates="template")


class TestCase(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    title = Column(String(500), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    type_id = Column(Integer, default=1)
    priority_id = Column(Integer, default=2)
    suite_id = Column(Integer, default=1)
    milestone_id = Column(Integer, nullable=True)
    refs = Column(String(500), nullable=True)
    estimate = Column(String(50), nullable=True)
    # Custom fields (stored directly, exposed as custom_* in API)
    steps = Column(JSON, nullable=True)           # → custom_steps_separated
    expected_result = Column(Text, nullable=True)  # → custom_expected
    preconditions = Column(Text, nullable=True)    # → custom_preconds
    created_on = Column(DateTime, default=datetime.utcnow)
    updated_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    section = relationship("Section", back_populates="cases")
    template = relationship("Template", back_populates="cases")
    results = relationship("TestResult", back_populates="case", cascade="all, delete-orphan")
    run_entries = relationship("RunEntry", back_populates="case", cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=True)
    status_id = Column(Integer, nullable=False)
    comment = Column(Text)
    elapsed = Column(String(50))
    defects = Column(String(500), nullable=True)
    version = Column(String(100), nullable=True)
    assignedto_id = Column(Integer, nullable=True)
    created_on = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, default=1)

    case = relationship("TestCase", back_populates="results")


class TestRun(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    suite_id = Column(Integer, default=1)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    refs = Column(String(500), nullable=True)
    milestone_id = Column(Integer, nullable=True)
    assignedto_id = Column(Integer, nullable=True)
    include_all = Column(Boolean, default=True)
    created_on = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, default=1)
    is_completed = Column(Boolean, default=False)
    completed_on = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="runs")
    entries = relationship("RunEntry", back_populates="run", cascade="all, delete-orphan")


class RunEntry(Base):
    __tablename__ = "run_entries"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    status_id = Column(Integer, default=3)
    comment = Column(Text)
    elapsed = Column(String(50))

    run = relationship("TestRun", back_populates="entries")
    case = relationship("TestCase", back_populates="run_entries")


# ---------------------------------------------------------------------------
# Helper: ORM → TestRail-format dict converters
# (timestamps as UNIX integers, field names matching real API)
# ---------------------------------------------------------------------------

def _ts(dt: Optional[datetime]) -> Optional[int]:
    if dt is None:
        return None
    return int(dt.timestamp())


def case_to_dict(case: TestCase) -> dict:
    return {
        "id": case.id,
        "title": case.title,
        "section_id": case.section_id,
        "template_id": case.template_id,
        "type_id": case.type_id,
        "priority_id": case.priority_id,
        "suite_id": getattr(case, "suite_id", 1) or 1,
        "milestone_id": getattr(case, "milestone_id", None),
        "refs": getattr(case, "refs", None),
        "created_by": 1,
        "updated_by": 1,
        "estimate": getattr(case, "estimate", None),
        "estimate_forecast": None,
        "is_deleted": 0,
        "display_order": 1,
        "custom_automation_type": 0,
        "created_on": _ts(case.created_on),
        "updated_on": _ts(case.updated_on),
        "custom_preconds": case.preconditions,
        "custom_steps": None,
        "custom_expected": case.expected_result,
        "custom_steps_separated": case.steps,
        "custom_mission": None,
        "custom_goals": None,
    }


def result_to_dict(result: TestResult) -> dict:
    return {
        "id": result.id,
        "test_id": result.case_id,
        "case_id": result.case_id,
        "run_id": getattr(result, "run_id", None),
        "status_id": result.status_id,
        "comment": result.comment,
        "elapsed": result.elapsed,
        "defects": getattr(result, "defects", None),
        "version": getattr(result, "version", None),
        "assignedto_id": getattr(result, "assignedto_id", None),
        "created_by": getattr(result, "created_by", 1) or 1,
        "created_on": _ts(result.created_on),
        "custom_step_results": [],
    }


def run_to_dict(run: TestRun) -> dict:
    entries = run.entries or []
    passed = sum(1 for e in entries if e.status_id == 1)
    blocked = sum(1 for e in entries if e.status_id == 2)
    untested = sum(1 for e in entries if e.status_id == 3)
    retest = sum(1 for e in entries if e.status_id == 4)
    failed = sum(1 for e in entries if e.status_id == 5)

    return {
        "id": run.id,
        "project_id": run.project_id,
        "suite_id": getattr(run, "suite_id", 1) or 1,
        "name": run.name,
        "description": run.description,
        "refs": getattr(run, "refs", None),
        "milestone_id": getattr(run, "milestone_id", None),
        "assignedto_id": getattr(run, "assignedto_id", None),
        "include_all": getattr(run, "include_all", True),
        "is_completed": run.is_completed,
        "completed_on": _ts(getattr(run, "completed_on", None)),
        "created_by": getattr(run, "created_by", 1) or 1,
        "created_on": _ts(run.created_on),
        "plan_id": None,
        "passed_count": passed,
        "blocked_count": blocked,
        "untested_count": untested,
        "retest_count": retest,
        "failed_count": failed,
        "config": None,
        "config_ids": [],
        "url": f"http://localhost:4002/ui/run/{run.id}",
    }


def project_to_dict(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "announcement": getattr(project, "announcement", None),
        "show_announcement": getattr(project, "show_announcement", False),
        "is_completed": getattr(project, "is_completed", False),
        "url": f"http://localhost:4002/ui",
        "created_on": _ts(project.created_on),
    }


def section_to_dict(section: Section) -> dict:
    return {
        "id": section.id,
        "project_id": section.project_id,
        "name": section.name,
        "description": section.description,
        "parent_id": section.parent_id,
        "depth": getattr(section, "depth", 0) or 0,
        "display_order": getattr(section, "display_order", 1) or 1,
        "suite_id": 1,
    }


# ---------------------------------------------------------------------------
# Pydantic models (used for request bodies)
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    announcement: Optional[str] = None
    show_announcement: bool = False


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_on: Optional[datetime] = None

    class Config:
        from_attributes = True


class SectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    suite_id: Optional[int] = None


class SectionResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    created_on: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestStep(BaseModel):
    content: Optional[str] = None
    expected: Optional[str] = None
    # Legacy field names
    step: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "content": self.content or self.step or "",
            "expected": self.expected or "",
        }


class TestCaseCreate(BaseModel):
    title: str
    template_id: int = 1
    type_id: int = 1
    priority_id: int = 2
    suite_id: Optional[int] = 1
    milestone_id: Optional[int] = None
    refs: Optional[str] = None
    estimate: Optional[str] = None
    custom_preconds: Optional[str] = None
    custom_expected: Optional[str] = None
    custom_steps_separated: Optional[List[Any]] = None
    custom_steps: Optional[str] = None
    # Also accept legacy field names
    steps: Optional[List[Any]] = None
    expected_result: Optional[str] = None
    preconditions: Optional[str] = None
    section_id: Optional[int] = None


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    template_id: Optional[int] = None
    type_id: Optional[int] = None
    priority_id: Optional[int] = None
    section_id: Optional[int] = None
    suite_id: Optional[int] = None
    milestone_id: Optional[int] = None
    refs: Optional[str] = None
    estimate: Optional[str] = None
    custom_preconds: Optional[str] = None
    custom_expected: Optional[str] = None
    custom_steps_separated: Optional[List[Any]] = None
    # Legacy field names
    steps: Optional[List[Any]] = None
    expected_result: Optional[str] = None
    preconditions: Optional[str] = None


class TestCaseResponse(BaseModel):
    id: int
    section_id: int
    title: str
    template_id: int
    type_id: int
    priority_id: int
    steps: Optional[List[Any]] = None
    expected_result: Optional[str] = None
    preconditions: Optional[str] = None
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestResultCreate(BaseModel):
    status_id: int
    comment: Optional[str] = None
    elapsed: Optional[str] = None
    defects: Optional[str] = None
    version: Optional[str] = None
    assignedto_id: Optional[int] = None
    custom_step_results: Optional[List[Any]] = None


class BulkResultItem(BaseModel):
    test_id: Optional[int] = None
    case_id: Optional[int] = None
    status_id: Optional[int] = None
    comment: Optional[str] = None
    elapsed: Optional[str] = None
    defects: Optional[str] = None
    version: Optional[str] = None
    assignedto_id: Optional[int] = None


class BulkResultsCreate(BaseModel):
    results: List[BulkResultItem]


class TestResultResponse(BaseModel):
    id: int
    case_id: int
    status_id: int
    comment: Optional[str] = None
    elapsed: Optional[str] = None
    created_on: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class TestRunCreate(BaseModel):
    name: str
    description: Optional[str] = None
    suite_id: Optional[int] = 1
    milestone_id: Optional[int] = None
    assignedto_id: Optional[int] = None
    include_all: bool = True
    case_ids: Optional[List[int]] = None
    refs: Optional[str] = None


class TestRunUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    milestone_id: Optional[int] = None
    include_all: Optional[bool] = None
    case_ids: Optional[List[int]] = None
    refs: Optional[str] = None


class TestRunResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    created_on: Optional[datetime] = None
    is_completed: bool = False

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATUS_NAMES = {
    1: "Passed",
    2: "Blocked",
    3: "Untested",
    4: "Retest",
    5: "Failed",
}

TYPE_NAMES = {
    1: "Functional",
    2: "Regression",
    3: "Smoke",
    4: "Performance",
    5: "Security",
    6: "Acceptance",
    7: "Automated",
}

PRIORITY_NAMES = {
    1: "Critical",
    2: "High",
    3: "Medium",
    4: "Low",
}
