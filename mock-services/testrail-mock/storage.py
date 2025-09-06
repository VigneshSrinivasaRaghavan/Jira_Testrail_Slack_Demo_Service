"""
TestRail Mock Service - Storage Layer
SQLAlchemy setup, database initialization, and seed data loading
"""

import json
import os
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from models import (
    Base, Project, Section, Template, TestCase, TestResult, TestRun, RunEntry,
    STATUS_NAMES, TYPE_NAMES, PRIORITY_NAMES
)

class TestRailStorage:
    def __init__(self, database_url: str = "sqlite:///./testrail.db"):
        self.engine = create_engine(database_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables and seed data"""
        Base.metadata.create_all(bind=self.engine)
        self.seed_initial_data()
    
    def get_db(self) -> Session:
        """Get database session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def seed_initial_data(self):
        """Load initial seed data"""
        db = next(self.get_db())
        try:
            # Check if data already exists
            if db.query(Project).first():
                return
            
            # Create default templates
            templates = [
                Template(id=1, name="Test Case (Text)", is_default=True),
                Template(id=2, name="Test Case (Steps)", is_default=False),
                Template(id=3, name="Exploratory Session", is_default=False)
            ]
            for template in templates:
                db.add(template)
            
            # Create default project
            project = Project(
                id=1,
                name="Demo Project",
                description="Sample project for TestRail mock service"
            )
            db.add(project)
            
            # Create sections
            sections = [
                Section(id=1, project_id=1, name="Authentication", description="Login and authentication tests"),
                Section(id=2, project_id=1, name="User Management", description="User creation, editing, and deletion"),
                Section(id=3, project_id=1, name="API Tests", description="REST API endpoint testing"),
                Section(id=4, project_id=1, name="UI Tests", description="User interface testing"),
                Section(id=5, project_id=1, name="Integration", description="Integration and end-to-end tests")
            ]
            for section in sections:
                db.add(section)
            
            db.commit()
            
            # Load seed data from JSON if available
            self.load_seed_data_from_json(db)
            
        except Exception as e:
            db.rollback()
            print(f"Error seeding data: {e}")
        finally:
            db.close()
    
    def load_seed_data_from_json(self, db: Session):
        """Load seed data from JSON files"""
        try:
            # Try to load from shared seed directory
            seed_file = "./shared/seed/sample_testcases.json"
            if not os.path.exists(seed_file):
                # Create sample data directly
                self.create_sample_test_cases(db)
                return
            
            with open(seed_file, 'r') as f:
                seed_data = json.load(f)
            
            # Process test cases from seed data
            for case_data in seed_data.get('test_cases', []):
                test_case = TestCase(
                    section_id=case_data.get('section_id', 1),
                    title=case_data['title'],
                    template_id=case_data.get('template_id', 1),
                    type_id=case_data.get('type_id', 1),
                    priority_id=case_data.get('priority_id', 2),
                    steps=case_data.get('steps'),
                    expected_result=case_data.get('expected_result'),
                    preconditions=case_data.get('preconditions')
                )
                db.add(test_case)
            
            db.commit()
            
        except Exception as e:
            print(f"Error loading seed data from JSON: {e}")
            self.create_sample_test_cases(db)
    
    def create_sample_test_cases(self, db: Session):
        """Create sample test cases directly"""
        sample_cases = [
            {
                "section_id": 1,
                "title": "Login with valid credentials",
                "template_id": 2,
                "type_id": 1,
                "priority_id": 1,
                "steps": [
                    {"step": "Navigate to login page", "expected": "Login form is displayed"},
                    {"step": "Enter valid username and password", "expected": "Credentials are accepted"},
                    {"step": "Click login button", "expected": "User is redirected to dashboard"}
                ],
                "expected_result": "User successfully logs in and sees dashboard",
                "preconditions": "User account exists and is active"
            },
            {
                "section_id": 1,
                "title": "Login with invalid credentials",
                "template_id": 2,
                "type_id": 1,
                "priority_id": 2,
                "steps": [
                    {"step": "Navigate to login page", "expected": "Login form is displayed"},
                    {"step": "Enter invalid username or password", "expected": "Invalid credentials entered"},
                    {"step": "Click login button", "expected": "Error message is shown"}
                ],
                "expected_result": "Login fails with appropriate error message",
                "preconditions": "Login page is accessible"
            },
            {
                "section_id": 2,
                "title": "Create new user account",
                "template_id": 2,
                "type_id": 1,
                "priority_id": 2,
                "steps": [
                    {"step": "Navigate to user management page", "expected": "User list is displayed"},
                    {"step": "Click 'Add User' button", "expected": "User creation form opens"},
                    {"step": "Fill in required user details", "expected": "Form accepts valid data"},
                    {"step": "Submit the form", "expected": "User is created successfully"}
                ],
                "expected_result": "New user account is created and appears in user list",
                "preconditions": "Admin user is logged in"
            },
            {
                "section_id": 3,
                "title": "GET /api/users endpoint returns user list",
                "template_id": 1,
                "type_id": 1,
                "priority_id": 2,
                "expected_result": "API returns 200 status with JSON array of users",
                "preconditions": "API service is running and users exist in database"
            },
            {
                "section_id": 3,
                "title": "POST /api/users creates new user",
                "template_id": 2,
                "type_id": 1,
                "priority_id": 2,
                "steps": [
                    {"step": "Send POST request to /api/users with valid user data", "expected": "Request is processed"},
                    {"step": "Check response status code", "expected": "Returns 201 Created"},
                    {"step": "Verify response body contains user data", "expected": "User object returned with ID"}
                ],
                "expected_result": "New user is created via API and returns user object",
                "preconditions": "API authentication token is valid"
            },
            {
                "section_id": 4,
                "title": "Navigation menu displays all sections",
                "template_id": 1,
                "type_id": 1,
                "priority_id": 3,
                "expected_result": "All navigation menu items are visible and clickable",
                "preconditions": "User is logged in to the application"
            },
            {
                "section_id": 5,
                "title": "End-to-end user registration and login flow",
                "template_id": 2,
                "type_id": 2,
                "priority_id": 2,
                "steps": [
                    {"step": "Register new user account", "expected": "Registration successful"},
                    {"step": "Verify email confirmation", "expected": "Email received and confirmed"},
                    {"step": "Login with new credentials", "expected": "Login successful"},
                    {"step": "Access protected resources", "expected": "User can access all features"}
                ],
                "expected_result": "Complete user onboarding flow works end-to-end",
                "preconditions": "Email service is configured and working"
            }
        ]
        
        for case_data in sample_cases:
            test_case = TestCase(**case_data)
            db.add(test_case)
        
        # Add some sample test results
        sample_results = [
            {"case_id": 1, "status_id": 1, "comment": "Test passed successfully", "elapsed": "2m 15s"},
            {"case_id": 2, "status_id": 1, "comment": "Error message displayed correctly", "elapsed": "1m 30s"},
            {"case_id": 3, "status_id": 5, "comment": "Form validation failed", "elapsed": "3m 45s"},
            {"case_id": 4, "status_id": 1, "comment": "API response correct", "elapsed": "45s"},
            {"case_id": 5, "status_id": 4, "comment": "Need to retest with updated data", "elapsed": "2m 00s"}
        ]
        
        for result_data in sample_results:
            result = TestResult(**result_data)
            db.add(result)
        
        # Create a sample test run
        test_run = TestRun(
            project_id=1,
            name="Sprint 1 Regression Tests",
            description="Regression testing for Sprint 1 features"
        )
        db.add(test_run)
        db.commit()
        
        # Add run entries
        run_entries = [
            {"run_id": 1, "case_id": 1, "status_id": 1, "comment": "Passed"},
            {"run_id": 1, "case_id": 2, "status_id": 1, "comment": "Passed"},
            {"run_id": 1, "case_id": 3, "status_id": 5, "comment": "Failed - needs investigation"},
            {"run_id": 1, "case_id": 4, "status_id": 3, "comment": "Not yet tested"},
            {"run_id": 1, "case_id": 5, "status_id": 3, "comment": "Not yet tested"}
        ]
        
        for entry_data in run_entries:
            entry = RunEntry(**entry_data)
            db.add(entry)
        
        db.commit()

# Global storage instance
storage = TestRailStorage()

def get_database():
    """Dependency to get database session"""
    return next(storage.get_db())
