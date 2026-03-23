"""
TestRail Mock Service - Storage Layer
SQLAlchemy setup, database initialization, seed data and migrations.
"""

import json
import os
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from models import (
    Base, Project, Section, Template, TestCase, TestResult, TestRun, RunEntry,
)


class TestRailStorage:
    def __init__(self, database_url: str = "sqlite:///./testrail.db"):
        self.engine = create_engine(database_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self._migrate()
        self._seed()

    # ------------------------------------------------------------------
    # Schema migrations — safe to run on every startup (idempotent)
    # ------------------------------------------------------------------

    def _migrate(self):
        """Add new columns introduced after initial release."""
        migrations = [
            # TestCase new columns
            "ALTER TABLE cases ADD COLUMN suite_id INTEGER DEFAULT 1",
            "ALTER TABLE cases ADD COLUMN milestone_id INTEGER",
            "ALTER TABLE cases ADD COLUMN refs VARCHAR(500)",
            "ALTER TABLE cases ADD COLUMN estimate VARCHAR(50)",
            # TestResult new columns
            "ALTER TABLE results ADD COLUMN run_id INTEGER REFERENCES runs(id)",
            "ALTER TABLE results ADD COLUMN defects VARCHAR(500)",
            "ALTER TABLE results ADD COLUMN version VARCHAR(100)",
            "ALTER TABLE results ADD COLUMN assignedto_id INTEGER",
            # created_by type change not needed – keep as is
            # TestRun new columns
            "ALTER TABLE runs ADD COLUMN suite_id INTEGER DEFAULT 1",
            "ALTER TABLE runs ADD COLUMN refs VARCHAR(500)",
            "ALTER TABLE runs ADD COLUMN milestone_id INTEGER",
            "ALTER TABLE runs ADD COLUMN assignedto_id INTEGER",
            "ALTER TABLE runs ADD COLUMN include_all BOOLEAN DEFAULT 1",
            "ALTER TABLE runs ADD COLUMN completed_on DATETIME",
            "ALTER TABLE runs ADD COLUMN created_by INTEGER DEFAULT 1",
            # Project new columns
            "ALTER TABLE projects ADD COLUMN announcement TEXT",
            "ALTER TABLE projects ADD COLUMN show_announcement BOOLEAN DEFAULT 0",
            "ALTER TABLE projects ADD COLUMN is_completed BOOLEAN DEFAULT 0",
            # Section new columns
            "ALTER TABLE sections ADD COLUMN depth INTEGER DEFAULT 0",
            "ALTER TABLE sections ADD COLUMN display_order INTEGER DEFAULT 1",
        ]
        with self.engine.connect() as conn:
            for sql in migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception:
                    # Column already exists – ignore
                    pass

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------

    def _seed(self):
        db = self.SessionLocal()
        try:
            if db.query(Project).first():
                return  # Already seeded

            print("Seeding initial data…")

            templates = [
                Template(id=1, name="Test Case (Text)", is_default=True),
                Template(id=2, name="Test Case (Steps)", is_default=False),
                Template(id=3, name="Exploratory Session", is_default=False),
            ]
            for t in templates:
                db.add(t)

            project = Project(
                id=1,
                name="Demo Project",
                description="Sample project for TestRail mock service",
            )
            db.add(project)

            sections = [
                Section(id=1, project_id=1, name="Authentication",    description="Login and authentication tests"),
                Section(id=2, project_id=1, name="User Management",   description="User creation, editing, and deletion"),
                Section(id=3, project_id=1, name="API Tests",         description="REST API endpoint testing"),
                Section(id=4, project_id=1, name="UI Tests",          description="User interface testing"),
                Section(id=5, project_id=1, name="Integration",       description="Integration and end-to-end tests"),
            ]
            for s in sections:
                db.add(s)
            db.commit()

            self._seed_cases(db)
        except Exception as e:
            db.rollback()
            print(f"Seed error: {e}")
        finally:
            db.close()

    def _seed_cases(self, db: Session):
        # Try JSON seed file first
        seed_file = "./shared/seed/sample_testcases.json"
        if os.path.exists(seed_file):
            try:
                with open(seed_file) as f:
                    data = json.load(f)
                for c in data.get("test_cases", []):
                    db.add(TestCase(
                        section_id=c.get("section_id", 1),
                        title=c["title"],
                        template_id=c.get("template_id", 1),
                        type_id=c.get("type_id", 1),
                        priority_id=c.get("priority_id", 2),
                        steps=c.get("steps"),
                        expected_result=c.get("expected_result"),
                        preconditions=c.get("preconditions"),
                    ))
                db.commit()
                return
            except Exception as e:
                print(f"JSON seed error: {e}")

        # Inline fallback seed
        sample_cases = [
            dict(section_id=1, title="Login with valid credentials", template_id=2, type_id=1, priority_id=1,
                 steps=[{"content": "Navigate to login page", "expected": "Login form is displayed"},
                        {"content": "Enter valid username and password", "expected": "Credentials accepted"},
                        {"content": "Click login button", "expected": "Redirected to dashboard"}],
                 expected_result="User successfully logs in", preconditions="User account exists"),
            dict(section_id=1, title="Login with invalid credentials", template_id=2, type_id=1, priority_id=2,
                 steps=[{"content": "Navigate to login page", "expected": "Login form displayed"},
                        {"content": "Enter invalid credentials", "expected": "Error message shown"}],
                 expected_result="Login fails with error message"),
            dict(section_id=2, title="Create new user account", template_id=2, type_id=1, priority_id=2,
                 steps=[{"content": "Go to User Management", "expected": "User list displayed"},
                        {"content": "Click Add User", "expected": "Creation form opens"},
                        {"content": "Fill in user details and submit", "expected": "User created"}],
                 expected_result="New user appears in user list", preconditions="Admin is logged in"),
            dict(section_id=3, title="GET /api/users returns user list", template_id=1, type_id=1, priority_id=2,
                 expected_result="200 with JSON array of users"),
            dict(section_id=3, title="POST /api/users creates new user", template_id=2, type_id=1, priority_id=2,
                 steps=[{"content": "POST to /api/users with valid payload", "expected": "Request processed"},
                        {"content": "Verify 201 status", "expected": "Returns 201 Created"}],
                 expected_result="User object returned with ID"),
            dict(section_id=4, title="Navigation menu visible on all pages", template_id=1, type_id=1, priority_id=3,
                 expected_result="All nav items visible and clickable"),
            dict(section_id=5, title="End-to-end registration and login", template_id=2, type_id=2, priority_id=2,
                 steps=[{"content": "Register new account", "expected": "Registration succeeds"},
                        {"content": "Login with new credentials", "expected": "Login succeeds"}],
                 expected_result="Full onboarding flow works"),
        ]

        cases = []
        for i, c in enumerate(sample_cases, 1):
            tc = TestCase(**c)
            db.add(tc)
            cases.append(tc)
        db.commit()
        for tc in cases:
            db.refresh(tc)

        # Sample results
        for case_id, status_id, comment in [
            (cases[0].id, 1, "Passed – credentials accepted"),
            (cases[1].id, 1, "Error message displayed correctly"),
            (cases[2].id, 5, "Form validation failed"),
            (cases[3].id, 1, "API response correct"),
            (cases[4].id, 4, "Retest with updated payload"),
        ]:
            db.add(TestResult(case_id=case_id, status_id=status_id, comment=comment, created_by=1))

        # Sample run
        run = TestRun(project_id=1, name="Sprint 1 Regression", description="Regression for Sprint 1", suite_id=1)
        db.add(run)
        db.commit()
        db.refresh(run)

        for case, status, comment in [
            (cases[0], 1, "Passed"),
            (cases[1], 1, "Passed"),
            (cases[2], 5, "Failed – needs investigation"),
            (cases[3], 3, "Not yet tested"),
            (cases[4], 3, "Not yet tested"),
        ]:
            db.add(RunEntry(run_id=run.id, case_id=case.id, status_id=status, comment=comment))

        db.commit()
        print("Seed data created.")

    def get_db(self) -> Generator[Session, None, None]:
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

storage = TestRailStorage()


def get_database() -> Generator[Session, None, None]:
    db = storage.SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
