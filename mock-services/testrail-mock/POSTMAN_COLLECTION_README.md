# TestRail Mock API - Postman Collection

## 📋 Overview

This Postman collection provides comprehensive testing for all TestRail Mock API endpoints. It includes examples, test scenarios, and proper documentation for agent integration testing.

## 📁 Files

- **`TestRail_Mock_API.postman_collection.json`** - Main collection with all API endpoints
- **`TestRail_Mock_Environment.postman_environment.json`** - Environment variables for local testing
- **`POSTMAN_COLLECTION_README.md`** - This documentation file

## 🚀 Quick Start

### 1. Import Collection & Environment

1. Open Postman
2. Click **Import** button
3. Import both files:
   - `TestRail_Mock_API.postman_collection.json`
   - `TestRail_Mock_Environment.postman_environment.json`

### 2. Set Environment

1. Select **"TestRail Mock - Local"** environment from the dropdown
2. Verify the `base_url` is set to `http://localhost:4002`

### 3. Start TestRail Mock Service

```bash
# Navigate to testrail-mock directory
cd mock-services/testrail-mock

# Start the service
./start.sh
# OR
source .venv/bin/activate && python -m uvicorn app:app --host 0.0.0.0 --port 4002 --reload
```

### 4. Test Health Check

Run the **"Health Check"** request to verify the service is running.

## 📚 Collection Structure

### 🏥 Health Check
- **GET** `/health` - Service health verification

### 🏗️ Projects
- **GET** `/api/v2/projects` - List all projects
- **GET** `/api/v2/project/{id}` - Get specific project

### 📂 Sections
- **GET** `/api/v2/sections/{project_id}` - Get project sections
- **POST** `/api/v2/sections/{project_id}` - Create new section

### 📝 Test Cases
- **GET** `/api/v2/cases/{project_id}` - Get all test cases
- **GET** `/api/v2/case/{case_id}` - Get specific test case
- **POST** `/api/v2/cases/{section_id}` - Create test case (simple)
- **POST** `/api/v2/cases/{section_id}` - Create test case (with steps)

### ✅ Test Results
- **GET** `/api/v2/results/{case_id}` - Get test case results
- **POST** `/api/v2/results/{case_id}` - Add result (Passed)
- **POST** `/api/v2/results/{case_id}` - Add result (Failed)
- **POST** `/api/v2/results/{case_id}` - Add result (Blocked)

### 🏃 Test Runs
- **GET** `/api/v2/runs/{project_id}` - Get project test runs
- **POST** `/api/v2/runs/{project_id}` - Create test run

### 📊 Templates & Metadata
- **GET** `/api/v2/templates` - Get available templates
- **GET** `/api/v2/stats/{project_id}` - Get project statistics

### 🔄 Legacy TestRail Endpoints
- **GET** `/index.php?case_id={id}` - Legacy get test case
- **POST** `/index.php?section_id={id}` - Legacy create test case

### 🎯 Test Scenarios
- **Complete Test Workflow** - End-to-end testing scenario

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `base_url` | `http://localhost:4002` | TestRail Mock service URL |
| `project_id` | `1` | Default project ID |
| `section_id` | `1` | Default section ID |
| `case_id` | `1` | Default test case ID |
| `created_case_id` | `` | ID of newly created test case |

## 📋 Status Reference

### Status IDs
- **1** = Passed ✅
- **2** = Blocked ⛔
- **3** = Untested ❓
- **4** = Retest 🔄
- **5** = Failed ❌

### Type IDs
- **1** = Functional
- **2** = Regression
- **3** = Smoke
- **4** = Performance
- **5** = Security

### Priority IDs
- **1** = Critical
- **2** = High
- **3** = Medium
- **4** = Low

### Template IDs
- **1** = Test Case (Text)
- **2** = Test Case (Steps)
- **3** = Exploratory Session

## 🧪 Testing Workflows

### Basic Test Case Creation
1. **Health Check** - Verify service is running
2. **Get All Projects** - List available projects
3. **Get Sections** - List sections in project
4. **Create Test Case** - Create a new test case
5. **Add Test Result** - Execute and record result

### Complete Agent Workflow
1. **Create Test Case (with Steps)** - Create detailed test case
2. **Execute Test (Pass)** - Add passing result
3. **Create Test Run** - Organize tests in a run
4. **Get Final Statistics** - View updated project stats

### Legacy Compatibility Testing
1. **Legacy - Add Test Case** - Test legacy endpoint
2. **Legacy - Get Test Case** - Retrieve via legacy endpoint

## 🔍 Example Requests

### Create Test Case with Steps
```json
POST /api/v2/cases/1
{
    "title": "Login Functionality Test",
    "template_id": 2,
    "type_id": 1,
    "priority_id": 1,
    "expected_result": "User should be able to login successfully",
    "preconditions": "User account exists",
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
    ]
}
```

### Add Test Result
```json
POST /api/v2/results/1
{
    "status_id": 1,
    "comment": "Test executed successfully. All steps passed.",
    "elapsed": "2m 30s"
}
```

## 🚨 Troubleshooting

### Service Not Running
- Verify TestRail Mock service is running on port 4002
- Check health endpoint: `GET http://localhost:4002/health`

### 404 Errors
- Ensure you're using the correct endpoint paths
- Verify IDs exist (project_id=1, section_id=1, etc.)

### 422 Validation Errors
- Check required fields in request body
- Verify data types match API expectations
- Ensure status_id, type_id, priority_id are valid integers

### Legacy Endpoint Issues
- Use query parameters: `?section_id=1` or `?case_id=1`
- Legacy endpoints expect different parameter format

## 📖 Additional Resources

- **API Documentation**: See main README.md in testrail-mock directory
- **Source Code**: Check routes.py for endpoint implementations
- **UI Interface**: Visit http://localhost:4002/ui for web interface

## 🎯 Agent Integration Tips

1. **Start with Health Check** - Always verify service availability
2. **Use Modern Endpoints** - Prefer `/api/v2/` over legacy endpoints
3. **Handle Status Codes** - Check for 200/201 success responses
4. **Validate Responses** - Ensure returned data matches expectations
5. **Test Error Cases** - Try invalid IDs and malformed requests
6. **Use Statistics** - Monitor project stats for test coverage

---

**Happy Testing! 🚀**

The TestRail Mock API is ready for comprehensive agent integration testing.
