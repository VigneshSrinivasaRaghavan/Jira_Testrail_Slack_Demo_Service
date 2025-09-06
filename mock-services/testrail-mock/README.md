# TestRail Mock Service

Enhanced TestRail-like test case management and execution tracking system built with FastAPI.

## 🚀 Features

### Enhanced TestRail Functionality
- **Projects & Sections**: Hierarchical organization of test cases
- **Test Templates**: Flexible test case structures
- **Step-by-step Instructions**: Detailed test execution guidance
- **Execution History**: Complete audit trail of test results
- **Test Runs**: Grouped test execution management
- **Realistic UI**: TestRail-like web interface with navigation

### API Capabilities
- **Clean REST API** with TestRail v2 compatibility
- **Comprehensive CRUD** operations for all entities
- **Advanced Filtering** and pagination
- **Statistics & Reporting** endpoints
- **Authentication** with Bearer tokens
- **OpenAPI/Swagger** documentation

### Technical Features
- **SQLite Database** with SQLAlchemy ORM
- **Jinja2 Templates** for responsive UI
- **Docker Support** with health checks
- **Comprehensive Tests** with pytest
- **Postman Collection** for API testing

## 🏗️ Architecture

```
testrail-mock/
├── app.py              # FastAPI application & UI routes
├── models.py           # Database models & Pydantic schemas
├── routes.py           # API routes & endpoints
├── storage.py          # Database setup & seed data
├── templates/          # Jinja2 HTML templates
│   ├── base.html       # Base template with styling
│   ├── index.html      # Dashboard view
│   ├── testcase_detail.html  # Test case details
│   └── cases_list.html # Test cases listing
├── tests/              # Pytest test suite
├── static/             # Static assets (CSS, JS)
├── shared/             # Seed data
│   └── seed/
│       └── sample_testcases.json
├── postman/            # API collection
│   └── Mock-TestRail.postman_collection.json
├── start-testrail.sh   # Docker start scripts
├── start-testrail.bat  # (Windows, Linux, PowerShell)
├── start.sh            # Local development scripts
├── start.bat           # (Windows, Linux)
├── Dockerfile          # Container configuration
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## 📊 Database Schema

### Enhanced Schema
```sql
-- Projects (top-level organization)
projects (id, name, description, created_on)

-- Sections (folders for organizing test cases)  
sections (id, project_id, name, description, parent_id, created_on)

-- Test case templates
templates (id, name, is_default)

-- Test cases (enhanced with steps)
cases (id, section_id, title, template_id, type_id, priority_id, 
       steps, expected_result, preconditions, created_on, updated_on)

-- Test results (execution history)
results (id, case_id, status_id, comment, elapsed, created_on, created_by)

-- Test runs (group executions)
runs (id, project_id, name, description, created_on, is_completed)

-- Run entries (link cases to runs)
run_entries (id, run_id, case_id, status_id, comment, elapsed)
```

## 🔌 API Endpoints

### Core REST API (Clean Paths)
```
# Projects
GET    /api/v2/projects              # List all projects
GET    /api/v2/project/{id}          # Get project by ID
POST   /api/v2/projects              # Create project

# Sections  
GET    /api/v2/sections/{project_id} # Get sections for project
GET    /api/v2/section/{id}          # Get section by ID
POST   /api/v2/sections/{project_id} # Create section

# Test Cases
GET    /api/v2/cases/{project_id}    # Get cases (with filtering)
GET    /api/v2/case/{id}             # Get case by ID
POST   /api/v2/cases/{section_id}    # Create case
PUT    /api/v2/case/{id}             # Update case

# Test Results
GET    /api/v2/results/{case_id}     # Get results for case
POST   /api/v2/results/{case_id}     # Add test result

# Test Runs
GET    /api/v2/runs/{project_id}     # Get runs for project
GET    /api/v2/run/{id}              # Get run by ID
POST   /api/v2/runs/{project_id}     # Create test run

# Utilities
GET    /api/v2/statuses              # Available statuses
GET    /api/v2/types                 # Available types
GET    /api/v2/priorities            # Available priorities
GET    /api/v2/templates             # Available templates
GET    /api/v2/stats/{project_id}    # Project statistics
```

### Legacy TestRail Compatibility
```
POST   /index.php?section_id={id}    # Create case (legacy)
POST   /index.php?case_id={id}       # Add result (legacy)
GET    /index.php?case_id={id}       # Get case (legacy)
```

### UI Routes
```
GET    /ui                           # Dashboard
GET    /ui/cases                     # Test cases list
GET    /ui/case/{id}                 # Test case detail
GET    /ui/section/{id}              # Section view
POST   /ui/case/{id}/execute         # Execute test case
```

## 🎯 Status Mapping

| ID | Status | Description |
|----|--------|-------------|
| 1  | Passed | Test executed successfully |
| 2  | Blocked | Test cannot be executed |
| 3  | Untested | Test not yet executed |
| 4  | Retest | Test needs re-execution |
| 5  | Failed | Test execution failed |

## 🏷️ Type & Priority Mapping

### Test Types
- 1: Functional
- 2: Regression  
- 3: Smoke
- 4: Performance
- 5: Security

### Priorities
- 1: Critical
- 2: High
- 3: Medium
- 4: Low

## 🚀 Quick Start

### Using Docker (Recommended)
```bash
# Build and start the service
docker-compose up -d --build testrail-mock

# Check service health
curl http://localhost:4002/health

# Access the UI
open http://localhost:4002/ui

# View API documentation
open http://localhost:4002/docs
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py

# Run tests
pytest tests/

# Format code
black . && ruff check .
```

## 📝 Usage Examples

### Creating a Test Case with Steps
```bash
curl -X POST "http://localhost:4002/api/v2/cases/1" \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Login Test with Steps",
    "template_id": 2,
    "type_id": 1,
    "priority_id": 1,
    "steps": [
      {
        "step": "Navigate to login page",
        "expected": "Login form is displayed"
      },
      {
        "step": "Enter valid credentials", 
        "expected": "Credentials are accepted"
      },
      {
        "step": "Click login button",
        "expected": "User is redirected to dashboard"
      }
    ],
    "expected_result": "User successfully logs in",
    "preconditions": "User account exists and is active"
  }'
```

### Adding Test Result
```bash
curl -X POST "http://localhost:4002/api/v2/results/1" \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "status_id": 1,
    "comment": "Test passed successfully",
    "elapsed": "2m 30s"
  }'
```

### Getting Project Statistics
```bash
curl -H "Authorization: Bearer test-token" \
  "http://localhost:4002/api/v2/stats/1"
```

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test class
pytest tests/test_api.py::TestCases -v
```

### Test Categories
- **Authentication Tests**: Bearer token validation
- **CRUD Operations**: Create, read, update operations
- **Error Handling**: 401, 404, 400 responses
- **Data Validation**: Pydantic schema validation
- **UI Integration**: Template rendering tests

## 📊 Postman Collection

Import the Postman collection from `./postman/Mock-TestRail.postman_collection.json`:

**Collection Features:**
- Complete API coverage
- Environment variables
- Authentication setup
- Error testing scenarios
- Legacy endpoint compatibility

**Variables:**
- `base_url`: http://localhost:4002
- `auth_token`: test-token-123
- `project_id`: 1
- `section_id`: 1
- `case_id`: 1

## 🔧 Configuration

### Environment Variables
```bash
MOCK_AUTH_REQUIRED=true          # Enable/disable authentication
ENABLE_RATE_LIMIT=false          # Enable rate limiting
TESTRAIL_PROJECT_ID=1            # Default project ID
```

### Database Configuration
- **Development**: SQLite (`testrail.db`)
- **Testing**: In-memory SQLite (`test.db`)
- **Docker**: Persistent volume (`testrail_db`)

## 🎨 UI Features

### Dashboard
- Project overview with statistics
- Recent test results
- Test run status
- Section navigation

### Test Case Management
- Hierarchical section organization
- Advanced filtering (section, type, priority)
- Pagination support
- Bulk operations (planned)

### Test Execution
- Step-by-step execution guidance
- Result history tracking
- Quick execution modal
- Status visualization

## 🔄 Real TestRail Mapping

| Mock Feature | Real TestRail Equivalent |
|--------------|-------------------------|
| Projects | Projects |
| Sections | Sections/Suites |
| Test Cases | Test Cases |
| Test Steps | Test Steps |
| Test Results | Test Results |
| Test Runs | Test Runs |
| Templates | Case Templates |
| Status IDs | Result Status |

## 🚨 Limitations & Notes

### Current Limitations
- No user management (single mock user)
- No file attachments (planned)
- No custom fields (uses fixed schema)
- No email notifications
- No advanced reporting

### Mock vs Real TestRail
- **Authentication**: Simple Bearer token vs OAuth/Basic Auth
- **Permissions**: No role-based access control
- **Integrations**: No Jira/Jenkins integrations
- **Customization**: Fixed fields vs custom fields
- **Scale**: SQLite vs enterprise databases

## 🛠️ Development

### Adding New Features
1. Update `models.py` for database changes
2. Add routes in `routes.py`
3. Update UI templates if needed
4. Add tests in `tests/`
5. Update Postman collection

### Code Style
```bash
# Format code
black .

# Lint code  
ruff check .

# Type checking
mypy .
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:4002/docs
- **ReDoc**: http://localhost:4002/redoc
- **OpenAPI JSON**: http://localhost:4002/openapi.json

## 🤝 Integration Examples

### Python Agent Integration
```python
import requests

class TestRailMockClient:
    def __init__(self, base_url="http://localhost:4002", token="test-token"):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def create_test_case(self, section_id, title, steps=None):
        data = {"title": title, "template_id": 2}
        if steps:
            data["steps"] = steps
        
        response = requests.post(
            f"{self.base_url}/api/v2/cases/{section_id}",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def add_test_result(self, case_id, status_id, comment=None):
        data = {"status_id": status_id}
        if comment:
            data["comment"] = comment
            
        response = requests.post(
            f"{self.base_url}/api/v2/results/{case_id}",
            json=data,
            headers=self.headers
        )
        return response.json()
```

## 📞 Support

For issues, questions, or contributions:
- Check the API documentation at `/docs`
- Review test cases in `tests/`
- Use Postman collection for API exploration
- Check Docker logs: `docker-compose logs testrail-mock`

---

**Built for Agentic AI Workshops** - Realistic TestRail simulation for training and development.
