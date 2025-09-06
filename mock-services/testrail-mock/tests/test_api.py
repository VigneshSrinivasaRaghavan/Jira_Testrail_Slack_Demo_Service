"""
TestRail Mock Service - API Tests
Comprehensive test suite for all endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from app import app
from storage import get_database
from models import Base, Project, Section, Template, TestCase, TestResult

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_database():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_database] = override_get_database

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def sample_project(db_session):
    project = Project(name="Test Project", description="Test project for API testing")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project

@pytest.fixture
def sample_section(db_session, sample_project):
    section = Section(
        project_id=sample_project.id,
        name="Test Section",
        description="Test section for API testing"
    )
    db_session.add(section)
    db_session.commit()
    db_session.refresh(section)
    return section

@pytest.fixture
def sample_template(db_session):
    template = Template(name="Test Template", is_default=True)
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template

@pytest.fixture
def sample_case(db_session, sample_section, sample_template):
    case = TestCase(
        section_id=sample_section.id,
        title="Sample Test Case",
        template_id=sample_template.id,
        type_id=1,
        priority_id=2,
        steps=[
            {"step": "Step 1", "expected": "Expected 1"},
            {"step": "Step 2", "expected": "Expected 2"}
        ],
        expected_result="Test should pass",
        preconditions="System is running"
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case

class TestHealthCheck:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "testrail-mock"

class TestAuthentication:
    def test_api_requires_auth(self, client):
        response = client.get("/api/v2/projects")
        assert response.status_code == 401
        
    def test_api_with_valid_auth(self, client, auth_headers):
        response = client.get("/api/v2/projects", headers=auth_headers)
        assert response.status_code == 200

class TestProjects:
    def test_get_projects(self, client, auth_headers, sample_project):
        response = client.get("/api/v2/projects", headers=auth_headers)
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) >= 1
        assert any(p["name"] == sample_project.name for p in projects)
    
    def test_get_project_by_id(self, client, auth_headers, sample_project):
        response = client.get(f"/api/v2/project/{sample_project.id}", headers=auth_headers)
        assert response.status_code == 200
        project = response.json()
        assert project["name"] == sample_project.name
        assert project["id"] == sample_project.id
    
    def test_get_nonexistent_project(self, client, auth_headers):
        response = client.get("/api/v2/project/999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_create_project(self, client, auth_headers):
        project_data = {
            "name": "New Test Project",
            "description": "Created via API"
        }
        response = client.post("/api/v2/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project = response.json()
        assert project["name"] == project_data["name"]
        assert project["description"] == project_data["description"]
        assert "id" in project

class TestSections:
    def test_get_sections(self, client, auth_headers, sample_section):
        response = client.get(f"/api/v2/sections/{sample_section.project_id}", headers=auth_headers)
        assert response.status_code == 200
        sections = response.json()
        assert len(sections) >= 1
        assert any(s["name"] == sample_section.name for s in sections)
    
    def test_get_section_by_id(self, client, auth_headers, sample_section):
        response = client.get(f"/api/v2/section/{sample_section.id}", headers=auth_headers)
        assert response.status_code == 200
        section = response.json()
        assert section["name"] == sample_section.name
        assert section["id"] == sample_section.id
    
    def test_create_section(self, client, auth_headers, sample_project):
        section_data = {
            "name": "New Test Section",
            "description": "Created via API"
        }
        response = client.post(f"/api/v2/sections/{sample_project.id}", json=section_data, headers=auth_headers)
        assert response.status_code == 200
        section = response.json()
        assert section["name"] == section_data["name"]
        assert section["project_id"] == sample_project.id

class TestCases:
    def test_get_cases(self, client, auth_headers, sample_case):
        project_id = sample_case.section.project_id
        response = client.get(f"/api/v2/cases/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        cases = response.json()
        assert len(cases) >= 1
        assert any(c["title"] == sample_case.title for c in cases)
    
    def test_get_cases_by_section(self, client, auth_headers, sample_case):
        project_id = sample_case.section.project_id
        section_id = sample_case.section_id
        response = client.get(f"/api/v2/cases/{project_id}?section_id={section_id}", headers=auth_headers)
        assert response.status_code == 200
        cases = response.json()
        assert all(c["section_id"] == section_id for c in cases)
    
    def test_get_case_by_id(self, client, auth_headers, sample_case):
        response = client.get(f"/api/v2/case/{sample_case.id}", headers=auth_headers)
        assert response.status_code == 200
        case = response.json()
        assert case["title"] == sample_case.title
        assert case["id"] == sample_case.id
        assert len(case["steps"]) == 2
    
    def test_create_case(self, client, auth_headers, sample_section, sample_template):
        case_data = {
            "title": "New Test Case",
            "template_id": sample_template.id,
            "type_id": 1,
            "priority_id": 2,
            "steps": [
                {"step": "Test step", "expected": "Expected result"}
            ],
            "expected_result": "Should work",
            "preconditions": "System ready"
        }
        response = client.post(f"/api/v2/cases/{sample_section.id}", json=case_data, headers=auth_headers)
        assert response.status_code == 200
        case = response.json()
        assert case["title"] == case_data["title"]
        assert case["section_id"] == sample_section.id
    
    def test_update_case(self, client, auth_headers, sample_case):
        update_data = {
            "title": "Updated Test Case",
            "template_id": sample_case.template_id,
            "type_id": 2,
            "priority_id": 1
        }
        response = client.put(f"/api/v2/case/{sample_case.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        case = response.json()
        assert case["title"] == update_data["title"]
        assert case["type_id"] == update_data["type_id"]

class TestResults:
    def test_get_results(self, client, auth_headers, sample_case):
        response = client.get(f"/api/v2/results/{sample_case.id}", headers=auth_headers)
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
    
    def test_create_result(self, client, auth_headers, sample_case):
        result_data = {
            "status_id": 1,
            "comment": "Test passed successfully",
            "elapsed": "2m 30s"
        }
        response = client.post(f"/api/v2/results/{sample_case.id}", json=result_data, headers=auth_headers)
        assert response.status_code == 200
        result = response.json()
        assert result["status_id"] == result_data["status_id"]
        assert result["comment"] == result_data["comment"]
        assert result["case_id"] == sample_case.id
    
    def test_create_result_invalid_status(self, client, auth_headers, sample_case):
        result_data = {
            "status_id": 999,  # Invalid status
            "comment": "Test result"
        }
        response = client.post(f"/api/v2/results/{sample_case.id}", json=result_data, headers=auth_headers)
        assert response.status_code == 400

class TestUtilityEndpoints:
    def test_get_statuses(self, client, auth_headers):
        response = client.get("/api/v2/statuses", headers=auth_headers)
        assert response.status_code == 200
        statuses = response.json()
        assert len(statuses) == 5
        assert any(s["name"] == "Passed" for s in statuses)
        assert any(s["name"] == "Failed" for s in statuses)
    
    def test_get_types(self, client, auth_headers):
        response = client.get("/api/v2/types", headers=auth_headers)
        assert response.status_code == 200
        types = response.json()
        assert len(types) >= 1
        assert any(t["name"] == "Functional" for t in types)
    
    def test_get_priorities(self, client, auth_headers):
        response = client.get("/api/v2/priorities", headers=auth_headers)
        assert response.status_code == 200
        priorities = response.json()
        assert len(priorities) >= 1
        assert any(p["name"] == "High" for p in priorities)
    
    def test_get_templates(self, client, auth_headers, sample_template):
        response = client.get("/api/v2/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()
        assert len(templates) >= 1
        assert any(t["name"] == sample_template.name for t in templates)

class TestStatistics:
    def test_get_project_stats(self, client, auth_headers, sample_case):
        project_id = sample_case.section.project_id
        response = client.get(f"/api/v2/stats/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()
        assert "total_cases" in stats
        assert "sections" in stats
        assert "overall_status_counts" in stats
        assert stats["project_id"] == project_id

class TestPagination:
    def test_cases_pagination(self, client, auth_headers, sample_case):
        project_id = sample_case.section.project_id
        response = client.get(f"/api/v2/cases/{project_id}?limit=1&offset=0", headers=auth_headers)
        assert response.status_code == 200
        cases = response.json()
        assert len(cases) <= 1

class TestErrorHandling:
    def test_nonexistent_case(self, client, auth_headers):
        response = client.get("/api/v2/case/999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_nonexistent_section(self, client, auth_headers):
        response = client.get("/api/v2/section/999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_create_case_invalid_section(self, client, auth_headers):
        case_data = {"title": "Test Case", "template_id": 1}
        response = client.post("/api/v2/cases/999", json=case_data, headers=auth_headers)
        assert response.status_code == 404

class TestUIEndpoints:
    def test_dashboard_redirect(self, client):
        response = client.get("/")
        assert response.status_code == 307  # Redirect
        assert response.headers["location"] == "/ui"
    
    def test_dashboard_loads(self, client):
        response = client.get("/ui")
        assert response.status_code == 200
        assert "TestRail Mock" in response.text
    
    def test_cases_list_loads(self, client):
        response = client.get("/ui/cases")
        assert response.status_code == 200
        assert "Test Cases" in response.text
