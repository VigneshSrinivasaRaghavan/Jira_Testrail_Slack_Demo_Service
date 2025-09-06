"""
TestRail Mock Service - Database Models
Enhanced schema with projects, sections, templates, cases, results, and runs
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel

Base = declarative_base()

# Database Models
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
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
    type_id = Column(Integer, default=1)  # 1=Functional, 2=Regression, 3=Smoke, etc.
    priority_id = Column(Integer, default=2)  # 1=Critical, 2=High, 3=Medium, 4=Low
    steps = Column(JSON)  # List of test steps
    expected_result = Column(Text)
    preconditions = Column(Text)
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
    status_id = Column(Integer, nullable=False)  # 1=Passed, 2=Blocked, 3=Untested, 4=Retest, 5=Failed
    comment = Column(Text)
    elapsed = Column(String(50))  # Time taken (e.g., "2m 30s")
    created_on = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), default="mock-user")
    
    case = relationship("TestCase", back_populates="results")

class TestRun(Base):
    __tablename__ = "runs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_on = Column(DateTime, default=datetime.utcnow)
    is_completed = Column(Boolean, default=False)
    
    project = relationship("Project", back_populates="runs")
    entries = relationship("RunEntry", back_populates="run", cascade="all, delete-orphan")

class RunEntry(Base):
    __tablename__ = "run_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    status_id = Column(Integer, default=3)  # Default to Untested
    comment = Column(Text)
    elapsed = Column(String(50))
    
    run = relationship("TestRun", back_populates="entries")
    case = relationship("TestCase", back_populates="run_entries")

# Pydantic Models for API
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_on: datetime
    
    class Config:
        from_attributes = True

class SectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class SectionResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    created_on: datetime
    
    class Config:
        from_attributes = True

class TestStep(BaseModel):
    step: str
    expected: str

class TestCaseCreate(BaseModel):
    title: str
    template_id: int = 1
    type_id: int = 1
    priority_id: int = 2
    steps: Optional[List[TestStep]] = None
    expected_result: Optional[str] = None
    preconditions: Optional[str] = None

class TestCaseResponse(BaseModel):
    id: int
    section_id: int
    title: str
    template_id: int
    type_id: int
    priority_id: int
    steps: Optional[List[TestStep]]
    expected_result: Optional[str]
    preconditions: Optional[str]
    created_on: datetime
    updated_on: datetime
    
    class Config:
        from_attributes = True

class TestResultCreate(BaseModel):
    status_id: int
    comment: Optional[str] = None
    elapsed: Optional[str] = None

class TestResultResponse(BaseModel):
    id: int
    case_id: int
    status_id: int
    comment: Optional[str]
    elapsed: Optional[str]
    created_on: datetime
    created_by: str
    
    class Config:
        from_attributes = True

class TestRunCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TestRunResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    created_on: datetime
    is_completed: bool
    
    class Config:
        from_attributes = True

# Constants
STATUS_NAMES = {
    1: "Passed",
    2: "Blocked", 
    3: "Untested",
    4: "Retest",
    5: "Failed"
}

TYPE_NAMES = {
    1: "Functional",
    2: "Regression", 
    3: "Smoke",
    4: "Performance",
    5: "Security"
}

PRIORITY_NAMES = {
    1: "Critical",
    2: "High",
    3: "Medium", 
    4: "Low"
}
