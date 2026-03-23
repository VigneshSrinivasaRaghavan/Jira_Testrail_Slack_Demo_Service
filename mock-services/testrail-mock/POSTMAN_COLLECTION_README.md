# TestRail Mock – Postman Collection

## 📁 Files

The Postman collection and environment live in the shared **`postman-collections/`** folder at the project root:

| File | Description |
|------|-------------|
| `postman-collections/TestRail_Mock.postman_collection.json` | Full collection — 41 requests across 8 folders |
| `postman-collections/TestRail_Mock.postman_environment.json` | Environment with fixed credentials and dynamic ID variables |

---

## 🚀 Quick Start

1. Open Postman → **Import**
2. Import both files from `postman-collections/`:
   - `TestRail_Mock.postman_collection.json`
   - `TestRail_Mock.postman_environment.json`
3. Select the **"TestRail Mock – Local"** environment from the top-right dropdown
4. Make sure the mock is running on `http://localhost:4002`
5. Run **Health Check** to verify, then follow the request order below

---

## 🔑 Authentication

All requests use **HTTP Basic Auth** — the same mechanism as real TestRail.

| Field | Value |
|-------|-------|
| **Email (username)** | `admin@testrail.mock` |
| **API Key (password)** | `MockAPI@123` |
| **Pre-built header** | `Authorization: Basic YWRtaW5AdGVzdHJhaWwubW9jazpNb2NrQVBJQDEyMw==` |

Already configured in the environment. The collection-level auth uses `{{email}}` and `{{api_key}}` automatically.

> Bearer token shortcut also accepted: `Authorization: Bearer MockAPI@123`

---

## 📚 Collection Structure

### 🏥 System
- `GET /health` — verify service is up (no auth required)

### 🔧 Utilities
- `GET /index.php?/api/v2/get_statuses`
- `GET /index.php?/api/v2/get_case_types`
- `GET /index.php?/api/v2/get_priorities`
- `GET /index.php?/api/v2/get_templates/{{project_id}}`

### 🏗️ Projects
- Get All Projects ← auto-saves `project_id`
- Get Project
- Add Project ← auto-saves `project_id`
- Update Project
- Delete Project

### 📂 Sections
- Get Sections ← auto-saves `section_id`
- Get Section
- Add Section ← auto-saves `section_id`
- Update Section
- Delete Section

### 📝 Test Cases
- Get Cases ← auto-saves `case_id`
- Get Cases (filtered by section)
- Get Case
- Add Case ← auto-saves `case_id`
- Update Case
- Delete Case
- Delete Cases (bulk)
- Copy Cases to Section
- Move Cases to Section

### 🏃 Test Runs
- Get Runs ← auto-saves `run_id`
- Get Run
- Add Run (specific cases) ← auto-saves `run_id`
- Add Run (include all cases)
- Update Run
- Close Run
- Delete Run

### ✅ Test Results
- Get Results (by case)
- Get Results for Case in Run
- Get Results for Run
- Add Result (for test/case)
- Add Result for Case in Run
- Add Results — bulk by `test_id`
- Add Results for Cases — bulk by `case_id` ⭐ most common for automation

### 🔐 Auth Examples
- Basic Auth via pre-computed header
- Bearer token shortcut
- Wrong credentials → expect 401

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `base_url` | `http://localhost:4002` | Service base URL |
| `email` | `admin@testrail.mock` | Fixed auth email |
| `api_key` | `MockAPI@123` | Fixed API key / Bearer token |
| `basic_token` | `YWRtaW5A...` | Pre-computed base64 token |
| `project_id` | `1` | Auto-updated by Add Project / Get All Projects |
| `section_id` | `1` | Auto-updated by Add Section / Get Sections |
| `case_id` | `1` | Auto-updated by Add Case / Get Cases |
| `run_id` | `1` | Auto-updated by Add Run / Get Runs |

---

## 📋 Status Reference

| ID | Status |
|----|--------|
| 1 | Passed ✅ |
| 2 | Blocked ⛔ |
| 3 | Untested ❓ |
| 4 | Retest 🔄 |
| 5 | Failed ❌ |

## Type IDs

| ID | Type |
|----|------|
| 1 | Other / Functional |
| 2 | Automated |
| 3 | Functionality |
| 4 | Regression |
| 5 | Smoke |

## Priority IDs

| ID | Priority |
|----|----------|
| 1 | Low |
| 2 | Medium |
| 3 | High |
| 4 | Critical |

---

## 🧪 Recommended Workflow

Run requests in this order for a complete end-to-end flow:

1. **Health Check** — verify service
2. **Get All Projects** — sets `project_id`
3. **Add Section** — sets `section_id`
4. **Add Case** — sets `case_id`
5. **Add Run** — sets `run_id` (include `case_id` in `case_ids`)
6. **Add Result for Case in Run** — records execution result
7. **Get Results for Run** — verify results recorded

---

## 🔍 Example curl

```bash
# Add a test result for a case inside a run
curl -X POST "http://localhost:4002/index.php?/api/v2/add_result_for_case/1/1" \
  -u "admin@testrail.mock:MockAPI@123" \
  -H "Content-Type: application/json" \
  -d '{"status_id": 1, "comment": "Passed", "elapsed": "30s"}'
```

---

## 🚨 Troubleshooting

| Problem | Fix |
|---------|-----|
| `401 Unauthorized` | Use exactly `admin@testrail.mock` / `MockAPI@123` |
| `400 Bad Request` | ID doesn't exist — create the resource first |
| `422 Validation Error` | Missing required field or wrong data type |
| Service not responding | Run `curl http://localhost:4002/health` to check |
