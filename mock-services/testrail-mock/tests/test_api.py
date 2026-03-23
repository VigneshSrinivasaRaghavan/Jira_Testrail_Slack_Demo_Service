"""
TestRail Mock Service - API Tests
Tests cover both TestRail-compatible endpoints and legacy compat endpoints.
"""

import base64
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app import app
from storage import get_database
from models import Base, Project, Section, Template, TestCase, TestResult

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_database():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_database] = override_get_database


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    # Run migrations on test DB too
    migrations = [
        "ALTER TABLE cases ADD COLUMN suite_id INTEGER DEFAULT 1",
        "ALTER TABLE cases ADD COLUMN milestone_id INTEGER",
        "ALTER TABLE cases ADD COLUMN refs VARCHAR(500)",
        "ALTER TABLE cases ADD COLUMN estimate VARCHAR(50)",
        "ALTER TABLE results ADD COLUMN run_id INTEGER",
        "ALTER TABLE results ADD COLUMN defects VARCHAR(500)",
        "ALTER TABLE results ADD COLUMN version VARCHAR(100)",
        "ALTER TABLE results ADD COLUMN assignedto_id INTEGER",
        "ALTER TABLE runs ADD COLUMN suite_id INTEGER DEFAULT 1",
        "ALTER TABLE runs ADD COLUMN refs VARCHAR(500)",
        "ALTER TABLE runs ADD COLUMN milestone_id INTEGER",
        "ALTER TABLE runs ADD COLUMN assignedto_id INTEGER",
        "ALTER TABLE runs ADD COLUMN include_all BOOLEAN DEFAULT 1",
        "ALTER TABLE runs ADD COLUMN completed_on DATETIME",
        "ALTER TABLE runs ADD COLUMN created_by INTEGER DEFAULT 1",
        "ALTER TABLE projects ADD COLUMN announcement TEXT",
        "ALTER TABLE projects ADD COLUMN show_announcement BOOLEAN DEFAULT 0",
        "ALTER TABLE projects ADD COLUMN is_completed BOOLEAN DEFAULT 0",
        "ALTER TABLE sections ADD COLUMN depth INTEGER DEFAULT 0",
        "ALTER TABLE sections ADD COLUMN display_order INTEGER DEFAULT 1",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass

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
    """Both Basic Auth and Bearer should work."""
    token = base64.b64encode(b"user@example.com:test-api-key").decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture
def sample_project(db_session):
    project = Project(name="Test Project", description="Test project")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def sample_section(db_session, sample_project):
    section = Section(project_id=sample_project.id, name="Test Section", description="Test section")
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
        steps=[{"content": "Step 1", "expected": "Expected 1"}, {"content": "Step 2", "expected": "Expected 2"}],
        expected_result="Test should pass",
        preconditions="System is running",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestAuthentication:
    def test_api_with_basic_auth(self, client, auth_headers, sample_project):
        response = client.get(f"/index.php/api/v2/get_project/{sample_project.id}", headers=auth_headers)
        assert response.status_code == 200

    def test_api_with_bearer_token(self, client, sample_project):
        response = client.get(
            f"/index.php/api/v2/get_project/{sample_project.id}",
            headers={"Authorization": "Bearer any-token"},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

class TestProjects:
    def test_get_projects(self, client, auth_headers, sample_project):
        response = client.get("/index.php/api/v2/get_projects", headers=auth_headers)
        assert response.status_code == 200
        projects = response.json()
        assert isinstance(projects, list)
        assert any(p["name"] == sample_project.name for p in projects)

    def test_get_project_by_id(self, client, auth_headers, sample_project):
        response = client.get(f"/index.php/api/v2/get_project/{sample_project.id}", headers=auth_headers)
        assert response.status_code == 200
        project = response.json()
        assert project["name"] == sample_project.name
        assert project["id"] == sample_project.id

    def test_get_nonexistent_project(self, client, auth_headers):
        # TestRail returns 400 for invalid/unknown entities
        response = client.get("/index.php/api/v2/get_project/999", headers=auth_headers)
        assert response.status_code == 400

    def test_create_project(self, client, auth_headers):
        response = client.post(
            "/index.php/api/v2/add_project",
            json={"name": "New Test Project", "description": "Created via API"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        project = response.json()
        assert project["name"] == "New Test Project"
        assert "id" in project

    # Compat routes
    def test_compat_get_projects(self, client, auth_headers, sample_project):
        response = client.get("/api/v2/projects", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_compat_get_project(self, client, auth_headers, sample_project):
        response = client.get(f"/api/v2/project/{sample_project.id}", headers=auth_headers)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

class TestSections:
    def test_get_sections(self, client, auth_headers, sample_section):
        response = client.get(
            f"/index.php/api/v2/get_sections/{sample_section.project_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "sections" in data
        assert any(s["name"] == sample_section.name for s in data["sections"])

    def test_get_section_by_id(self, client, auth_headers, sample_section):
        response = client.get(f"/index.php/api/v2/get_section/{sample_section.id}", headers=auth_headers)
        assert response.status_code == 200
        section = response.json()
        assert section["name"] == sample_section.name
        assert section["id"] == sample_section.id

    def test_create_section(self, client, auth_headers, sample_project):
        response = client.post(
            f"/index.php/api/v2/add_section/{sample_project.id}",
            json={"name": "New Section", "description": "Created via API"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        section = response.json()
        assert section["name"] == "New Section"
        assert section["project_id"] == sample_project.id

    def test_get_nonexistent_section(self, client, auth_headers):
        response = client.get("/index.php/api/v2/get_section/999", headers=auth_headers)
        assert response.status_code == 400

    # Compat
    def test_compat_get_sections_paginated(self, client, auth_headers, sample_section):
        response = client.get(f"/api/v2/sections/{sample_section.project_id}", headers=auth_headers)
        assert response.status_code == 200
        # Compat now returns paginated dict too
        data = response.json()
        assert "sections" in data


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------

class TestCases:
    def test_get_cases(self, client, auth_headers, sample_case):
        project_id = sample_case.section.project_id
        response = client.get(f"/index.php/api/v2/get_cases/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "cases" in data
        assert "offset" in data
        assert "limit" in data
        assert "_links" in data
        assert any(c["title"] == sample_case.title for c in data["cases"])

    def test_get_cases_by_section(self, client, auth_headers, sample_case):
        project_id = sample_case.section.project_id
        section_id = sample_case.section_id
        response = client.get(
            f"/index.php/api/v2/get_cases/{project_id}?section_id={section_id}", headers=auth_headers
        )
        assert response.status_code == 200
        cases = response.json()["cases"]
        assert all(c["section_id"] == section_id for c in cases)

    def test_get_case_by_id(self, client, auth_headers, sample_case):
        response = client.get(f"/index.php/api/v2/get_case/{sample_case.id}", headers=auth_headers)
        assert response.status_code == 200
        case = response.json()
        assert case["title"] == sample_case.title
        assert case["id"] == sample_case.id
        # TestRail-style fields
        assert "created_on" in case
        assert isinstance(case["created_on"], int)  # UNIX timestamp
        assert "custom_preconds" in case
        assert "custom_expected" in case
        assert "suite_id" in case

    def test_create_case(self, client, auth_headers, sample_section, sample_template):
        response = client.post(
            f"/index.php/api/v2/add_case/{sample_section.id}",
            json={
                "title": "New Test Case",
                "template_id": sample_template.id,
                "type_id": 1,
                "priority_id": 2,
                "custom_preconds": "System ready",
                "custom_expected": "Test passes",
                "custom_steps_separated": [{"content": "Do step", "expected": "See result"}],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        case = response.json()
        assert case["title"] == "New Test Case"
        assert case["section_id"] == sample_section.id
        assert case["custom_preconds"] == "System ready"

    def test_update_case(self, client, auth_headers, sample_case):
        response = client.post(
            f"/index.php/api/v2/update_case/{sample_case.id}",
            json={"title": "Updated Test Case", "type_id": 2, "priority_id": 1},
            headers=auth_headers,
        )
        assert response.status_code == 200
        case = response.json()
        assert case["title"] == "Updated Test Case"
        assert case["type_id"] == 2

    def test_delete_case(self, client, auth_headers, db_session, sample_section, sample_template):
        case = TestCase(
            section_id=sample_section.id, title="To Delete", template_id=sample_template.id,
            type_id=1, priority_id=2,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)

        response = client.post(f"/index.php/api/v2/delete_case/{case.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == {}

    def test_get_nonexistent_case(self, client, auth_headers):
        response = client.get("/index.php/api/v2/get_case/999", headers=auth_headers)
        assert response.status_code == 400

    def test_filter_by_priority(self, client, auth_headers, sample_case):
        project_id = sample_case.section.project_id
        response = client.get(
            f"/index.php/api/v2/get_cases/{project_id}?priority_id={sample_case.priority_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    # Compat routes
    def test_compat_get_case(self, client, auth_headers, sample_case):
        response = client.get(f"/api/v2/case/{sample_case.id}", headers=auth_headers)
        assert response.status_code == 200

    def test_compat_get_cases_paginated(self, client, auth_headers, sample_case):
        project_id = sample_case.section.project_id
        response = client.get(f"/api/v2/cases/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "cases" in data

    def test_compat_cases_pagination(self, client, auth_headers, sample_case):
        project_id = sample_case.section.project_id
        response = client.get(f"/api/v2/cases/{project_id}?limit=1&offset=0", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["cases"]) <= 1


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

class TestResults:
    def test_add_result(self, client, auth_headers, sample_case):
        response = client.post(
            f"/index.php/api/v2/add_result/{sample_case.id}",
            json={"status_id": 1, "comment": "Test passed", "elapsed": "2m 30s"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result["status_id"] == 1
        assert result["test_id"] == sample_case.id
        assert isinstance(result["created_on"], int)

    def test_get_results(self, client, auth_headers, sample_case):
        # Add a result first
        client.post(
            f"/index.php/api/v2/add_result/{sample_case.id}",
            json={"status_id": 5, "comment": "Failed"},
            headers=auth_headers,
        )
        response = client.get(f"/index.php/api/v2/get_results/{sample_case.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) >= 1

    def test_add_result_invalid_status(self, client, auth_headers, sample_case):
        response = client.post(
            f"/index.php/api/v2/add_result/{sample_case.id}",
            json={"status_id": 999},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_add_result_for_case(self, client, auth_headers, db_session, sample_case):
        # Need a run first
        run = pytest.importorskip("models").TestRun
        from models import TestRun, RunEntry
        r = TestRun(project_id=sample_case.section.project_id, name="TR Run", suite_id=1)
        db_session.add(r)
        db_session.commit()
        db_session.refresh(r)
        db_session.add(RunEntry(run_id=r.id, case_id=sample_case.id, status_id=3))
        db_session.commit()

        response = client.post(
            f"/index.php/api/v2/add_result_for_case/{r.id}/{sample_case.id}",
            json={"status_id": 1, "comment": "Passed", "defects": "BUG-1"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result["status_id"] == 1
        assert result["defects"] == "BUG-1"
        assert result["run_id"] == r.id

    def test_bulk_add_results_for_cases(self, client, auth_headers, db_session, sample_case):
        from models import TestRun, RunEntry
        r = TestRun(project_id=sample_case.section.project_id, name="Bulk Run", suite_id=1)
        db_session.add(r)
        db_session.commit()
        db_session.refresh(r)
        db_session.add(RunEntry(run_id=r.id, case_id=sample_case.id, status_id=3))
        db_session.commit()

        response = client.post(
            f"/index.php/api/v2/add_results_for_cases/{r.id}",
            json={"results": [{"case_id": sample_case.id, "status_id": 5, "comment": "Failed"}]},
            headers=auth_headers,
        )
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert results[0]["status_id"] == 5

    # Compat
    def test_compat_get_results(self, client, auth_headers, sample_case):
        response = client.get(f"/api/v2/results/{sample_case.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------

class TestRuns:
    def test_add_run(self, client, auth_headers, sample_project):
        response = client.post(
            f"/index.php/api/v2/add_run/{sample_project.id}",
            json={"name": "Sprint Run", "description": "Test run via API", "include_all": False, "case_ids": []},
            headers=auth_headers,
        )
        assert response.status_code == 200
        run = response.json()
        assert run["name"] == "Sprint Run"
        assert run["project_id"] == sample_project.id
        assert "passed_count" in run
        assert "failed_count" in run
        assert "untested_count" in run

    def test_get_run(self, client, auth_headers, db_session, sample_project):
        from models import TestRun
        r = TestRun(project_id=sample_project.id, name="Get Run Test", suite_id=1)
        db_session.add(r)
        db_session.commit()
        db_session.refresh(r)

        response = client.get(f"/index.php/api/v2/get_run/{r.id}", headers=auth_headers)
        assert response.status_code == 200
        run = response.json()
        assert run["name"] == "Get Run Test"
        assert run["id"] == r.id

    def test_get_runs(self, client, auth_headers, sample_project):
        response = client.get(f"/index.php/api/v2/get_runs/{sample_project.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "runs" in data

    def test_update_run(self, client, auth_headers, db_session, sample_project):
        from models import TestRun
        r = TestRun(project_id=sample_project.id, name="Update Run Test", suite_id=1)
        db_session.add(r)
        db_session.commit()
        db_session.refresh(r)

        response = client.post(
            f"/index.php/api/v2/update_run/{r.id}",
            json={"description": "Updated description"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        run = response.json()
        assert run["description"] == "Updated description"

    def test_close_run(self, client, auth_headers, db_session, sample_project):
        from models import TestRun
        r = TestRun(project_id=sample_project.id, name="Close Run Test", suite_id=1)
        db_session.add(r)
        db_session.commit()
        db_session.refresh(r)

        response = client.post(f"/index.php/api/v2/close_run/{r.id}", headers=auth_headers)
        assert response.status_code == 200
        run = response.json()
        assert run["is_completed"] is True

    def test_delete_run(self, client, auth_headers, db_session, sample_project):
        from models import TestRun
        r = TestRun(project_id=sample_project.id, name="Delete Run Test", suite_id=1)
        db_session.add(r)
        db_session.commit()
        db_session.refresh(r)

        response = client.post(f"/index.php/api/v2/delete_run/{r.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == {}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

class TestUtilityEndpoints:
    def test_get_statuses(self, client, auth_headers):
        response = client.get("/index.php/api/v2/get_statuses", headers=auth_headers)
        assert response.status_code == 200
        statuses = response.json()
        assert len(statuses) == 5
        names = [s["name"] for s in statuses]
        assert "Passed" in names
        assert "Failed" in names

    def test_get_case_types(self, client, auth_headers):
        response = client.get("/index.php/api/v2/get_case_types", headers=auth_headers)
        assert response.status_code == 200
        types = response.json()
        assert any(t["name"] == "Functional" for t in types)

    def test_get_priorities(self, client, auth_headers):
        response = client.get("/index.php/api/v2/get_priorities", headers=auth_headers)
        assert response.status_code == 200
        priorities = response.json()
        assert any(p["name"] == "High" for p in priorities)

    def test_get_templates(self, client, auth_headers, sample_template):
        response = client.get(f"/index.php/api/v2/get_templates/1", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()
        assert any(t["name"] == sample_template.name for t in templates)

    # Compat aliases
    def test_compat_statuses(self, client, auth_headers):
        assert client.get("/api/v2/statuses", headers=auth_headers).status_code == 200

    def test_compat_types(self, client, auth_headers):
        assert client.get("/api/v2/types", headers=auth_headers).status_code == 200

    def test_compat_priorities(self, client, auth_headers):
        assert client.get("/api/v2/priorities", headers=auth_headers).status_code == 200

    def test_compat_templates(self, client, auth_headers):
        assert client.get("/api/v2/templates", headers=auth_headers).status_code == 200


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# UI Endpoints
# ---------------------------------------------------------------------------

class TestUIEndpoints:
    def test_root_redirects(self, client):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (307, 302)
        assert "/ui" in response.headers.get("location", "")

    def test_dashboard_loads(self, client):
        response = client.get("/ui")
        assert response.status_code == 200
        assert "TestRail" in response.text

    def test_cases_list_loads(self, client):
        response = client.get("/ui/cases")
        assert response.status_code == 200
        assert "Test Cases" in response.text

    def test_runs_list_loads(self, client):
        response = client.get("/ui/runs")
        assert response.status_code == 200

    def test_create_case_form_loads(self, client):
        response = client.get("/ui/cases/create")
        assert response.status_code == 200

    def test_create_run_form_loads(self, client):
        response = client.get("/ui/runs/create")
        assert response.status_code == 200
