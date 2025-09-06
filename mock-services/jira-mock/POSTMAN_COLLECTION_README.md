# Jira Mock API - Postman Collection

## 📋 Overview

This Postman collection provides comprehensive testing for all Jira Mock API endpoints. It mimics the Jira Cloud REST API v3 for educational purposes and agent integration testing.

## 📁 Files

- **`Jira_Mock_API.postman_collection.json`** - Main collection with all API endpoints
- **`Jira_Mock_Environment.postman_environment.json`** - Environment variables for local testing
- **`POSTMAN_COLLECTION_README.md`** - This documentation file

## 🚀 Quick Start

### 1. Import Collection & Environment

1. Open Postman
2. Click **Import** button
3. Import both files:
   - `Jira_Mock_API.postman_collection.json`
   - `Jira_Mock_Environment.postman_environment.json`

### 2. Set Environment

1. Select **"Jira Mock - Local"** environment from the dropdown
2. Verify the `base_url` is set to `http://localhost:4001`
3. Verify the `auth_token` is set to `test-token-123`

### 3. Start Jira Mock Service

```bash
# Navigate to jira-mock directory
cd mock-services/jira-mock

# Start the service
./start.sh
# OR
source .venv/bin/activate && python -m uvicorn app:app --host 0.0.0.0 --port 4001 --reload
```

### 4. Test Health Check

Run the **"Health Check"** request to verify the service is running.

## 📚 Collection Structure

### 🏥 Health Check
- **GET** `/health` - Service health verification

### 🎫 Issue Management
- **POST** `/rest/api/3/issue` - Create Issue (Bug, Task, Story)
- **GET** `/rest/api/3/issue/{key}` - Get specific issue
- **DELETE** `/rest/api/3/issue/{key}` - Delete issue

### 🔍 Issue Search & Listing
- **GET** `/rest/api/3/search` - Search all issues
- **GET** `/rest/api/3/search?startAt=0&maxResults=10` - Search with pagination
- **GET** `/rest/api/3/search?jql=project = QA` - Search with JQL

### 🔧 Admin Operations
- **POST** `/admin/reset` - Reset database to initial state

### 🧪 Test Scenarios
- **Complete Issue Workflow** - End-to-end testing scenario
- **Error Scenarios** - Testing error handling

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `base_url` | `http://localhost:4001` | Jira Mock service URL |
| `auth_token` | `test-token-123` | Bearer token for authentication |
| `issue_key` | `QA-1` | Default issue key for testing |
| `created_issue_key` | `` | Key of newly created issue |

## 🔐 Authentication

All API endpoints (except `/health` and `/ui/*`) require authentication:

```
Authorization: Bearer <token>
```

The mock service accepts **any token value** for testing purposes. Use the `{{auth_token}}` variable in requests.

## 📋 Issue Reference

### Issue Types
- **Bug** - Software defects and errors
- **Task** - General work items
- **Story** - User stories and features
- **Epic** - Large work items
- **Subtask** - Sub-items of other issues

### Priority Levels
- **Low** - Minor issues
- **Medium** - Standard priority
- **High** - Important issues
- **Critical** - Urgent, blocking issues

### Project Information
- **Key**: `QA`
- **Name**: `QA Project`

### Status Values
- **To Do** - Not started
- **In Progress** - Currently being worked on
- **Done** - Completed

## 🔍 Example Requests

### Create Issue (Full Example)
```json
POST /rest/api/3/issue
Authorization: Bearer test-token-123
Content-Type: application/json

{
    "fields": {
        "project": {
            "key": "QA"
        },
        "summary": "Login page not loading",
        "description": "When clicking the login button, page shows 404 error",
        "issuetype": {
            "name": "Bug"
        },
        "priority": {
            "name": "High"
        },
        "assignee": "john.doe",
        "reporter": "jane.smith",
        "labels": ["ui", "critical", "login"],
        "components": ["frontend", "authentication"]
    }
}
```

### Create Issue (Minimal)
```json
POST /rest/api/3/issue
Authorization: Bearer test-token-123
Content-Type: application/json

{
    "fields": {
        "summary": "Simple test issue",
        "issuetype": {
            "name": "Bug"
        }
    }
}
```

### Search Issues
```bash
GET /rest/api/3/search?startAt=0&maxResults=10
Authorization: Bearer test-token-123
```

## 🧪 Testing Workflows

### Basic Issue Management
1. **Health Check** - Verify service is running
2. **Create Issue** - Create a new bug or task
3. **Get Issue** - Retrieve the created issue
4. **Search Issues** - List all issues
5. **Delete Issue** - Clean up test data

### Agent Integration Workflow
1. **Create Issue - Bug** - Create a critical bug
2. **Fetch Created Issue** - Verify issue data
3. **Search for Issues** - Find the issue in search results
4. **Delete Test Issue** - Clean up

### Error Testing
1. **Missing Authorization** - Test 401 error
2. **Invalid Issue Key** - Test 404 error
3. **Invalid Issue Creation** - Test validation errors

## 🚨 Troubleshooting

### Service Not Running
- Verify Jira Mock service is running on port 4001
- Check health endpoint: `GET http://localhost:4001/health`

### 401 Unauthorized
- Ensure `Authorization: Bearer <token>` header is present
- Any token value is accepted by the mock service

### 404 Not Found
- Verify issue keys exist (QA-1, QA-2, QA-3 are pre-seeded)
- Use search endpoint to see available issues

### 400 Bad Request
- Check required fields: `summary` and `issuetype.name`
- Ensure JSON payload is properly formatted

## 📖 API Compatibility

This mock service implements a subset of the Jira Cloud REST API v3:

### Supported Endpoints
✅ **POST** `/rest/api/3/issue` - Create issue  
✅ **GET** `/rest/api/3/issue/{issueIdOrKey}` - Get issue  
✅ **DELETE** `/rest/api/3/issue/{issueIdOrKey}` - Delete issue  
✅ **GET** `/rest/api/3/search` - Search issues  

### Supported Fields
✅ `summary`, `description`, `issuetype`  
✅ `assignee`, `reporter`, `priority`  
✅ `labels` (array), `components` (array)  
✅ `project`, `status` (fixed values)  
✅ `created`, `updated` (auto-managed)  

### Not Implemented
❌ Issue updates/editing  
❌ Comments and attachments  
❌ Workflows and transitions  
❌ Custom fields  
❌ Advanced JQL filtering  

## 🎯 Agent Integration Tips

1. **Start with Health Check** - Always verify service availability
2. **Use Bearer Authentication** - Include `Authorization: Bearer <token>` header
3. **Handle Status Codes** - Check for 200/201 success responses
4. **Required Fields** - Always include `summary` and `issuetype.name`
5. **Test Error Cases** - Handle 401, 404, and 400 errors gracefully
6. **Use Search Endpoint** - List issues to get available keys
7. **Clean Up** - Delete test issues to keep database clean

## 🔄 Database Reset

Use the **Admin → Reset Database** endpoint to restore the database to its initial state with sample data:

```json
POST /admin/reset
Authorization: Bearer test-token-123
Content-Type: application/json

{
    "confirm": true
}
```

This will:
- Delete all existing issues
- Recreate the database schema
- Insert 3 sample issues (QA-1, QA-2, QA-3)

## 📊 Sample Data

After reset, the database contains:

1. **QA-1** - Sample Bug Issue (High priority)
2. **QA-2** - Sample Task Issue (Medium priority)  
3. **QA-3** - Sample Story Issue (Low priority)

## 🌐 Web UI

The service also provides a web interface:
- **Dashboard**: `GET http://localhost:4001/ui`
- **Issue Detail**: `GET http://localhost:4001/ui/issue/{key}`

No authentication required for UI endpoints.

---

**Happy Testing! 🚀**

The Jira Mock API is ready for comprehensive agent integration testing and educational demonstrations.
