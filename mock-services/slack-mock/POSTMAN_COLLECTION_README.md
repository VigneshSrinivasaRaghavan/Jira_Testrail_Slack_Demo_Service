# Slack Mock API - Postman Collection Guide

This guide explains how to use the Postman collection to test the Slack Mock Service.

## Files Included

- `Slack_Mock_API.postman_collection.json` - Main collection with all API endpoints
- `Slack_Mock_Environment.postman_environment.json` - Environment variables

## Quick Setup

1. **Import Collection**: Import `Slack_Mock_API.postman_collection.json` into Postman
2. **Import Environment**: Import `Slack_Mock_Environment.postman_environment.json`
3. **Select Environment**: Choose "Slack Mock Environment" in Postman
4. **Start Service**: Ensure the Slack mock service is running on `localhost:4003`

## Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:4003` | Service base URL |
| `auth_token` | `demo-token-12345` | Bearer token for authentication |
| `default_channel` | `qa-reports` | Primary test channel |
| `alternative_channel` | `general` | Secondary test channel |
| `test_username` | `PostmanTestUser` | Username for test messages |
| `last_message_ts` | _(auto-set)_ | Stores last message timestamp |

## Collection Structure

### 1. System Endpoints
- **Health Check** - Verify service is running

### 2. Chat API Endpoints
- **Post Message to Channel** - Send a basic message
- **Post Message with Thread** - Reply to a message in a thread
- **Get Conversation History** - Retrieve channel messages
- **Get Conversation History with Pagination** - Test pagination

### 3. File API Endpoints
- **Upload File** - Upload a file to a channel

### 4. Error Testing
- **Post Message - Missing Auth (401)** - Test authentication
- **Post Message - Invalid Channel (404)** - Test error handling
- **Post Message - Validation Error (422)** - Test input validation

## Usage Instructions

### Running the Full Collection

1. Start the Slack mock service
2. Select the "Slack Mock Environment"
3. Click "Run Collection" to execute all requests
4. Review the test results

### Individual Request Testing

#### 1. Health Check
- **Purpose**: Verify service is running
- **Expected**: 200 OK with health status

#### 2. Post Message
- **Purpose**: Send a message to a channel
- **Body**: 
  ```json
  {
    "channel": "qa-reports",
    "text": "Hello from Postman!",
    "username": "PostmanBot"
  }
  ```
- **Expected**: 200 OK with message details and timestamp

#### 3. Get Conversation History
- **Purpose**: Retrieve messages from a channel
- **Parameters**: 
  - `channel`: Channel name (e.g., "qa-reports")
  - `limit`: Number of messages to retrieve
- **Expected**: 200 OK with array of messages

#### 4. Upload File
- **Purpose**: Upload a file to a channel
- **Form Data**:
  - `channels`: Channel name
  - `title`: File title
  - `initial_comment`: Comment to post with file
  - `file`: File to upload
- **Expected**: 200 OK with file details

## Test Scenarios

### Scenario 1: Basic Message Flow
1. Run "Health Check" to verify service
2. Run "Post Message to Channel" to send a message
3. Run "Get Conversation History" to see the message
4. Verify the message appears in the history

### Scenario 2: Threading
1. Run "Post Message to Channel" (stores timestamp)
2. Run "Post Message with Thread" (uses stored timestamp)
3. Run "Get Conversation History" to see both messages
4. Verify the second message has `thread_ts` set

### Scenario 3: File Upload
1. Select a test file in the "Upload File" request
2. Run the request
3. Check the response for file details
4. Optionally check the channel for the file message

### Scenario 4: Error Handling
1. Run "Missing Auth" test - should return 401
2. Run "Invalid Channel" test - should return 404
3. Run "Validation Error" test - should return 422

## Automated Tests

Each request includes automated tests that verify:

- **Status Codes**: Correct HTTP response codes
- **Response Structure**: Required fields are present
- **Data Validation**: Response data matches expectations
- **Performance**: Response time under 2 seconds

### Test Results Interpretation

- ✅ **Green**: Test passed
- ❌ **Red**: Test failed - check response or service status
- ⚠️ **Yellow**: Warning - usually performance related

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure Slack mock service is running on port 4003
   - Check `base_url` environment variable

2. **401 Unauthorized**
   - Verify `auth_token` is set in environment
   - Check if `MOCK_AUTH_REQUIRED` is enabled in service

3. **404 Channel Not Found**
   - Ensure using correct channel names: "qa-reports" or "general"
   - Check service logs for available channels

4. **File Upload Issues**
   - Ensure a file is selected in the form-data
   - Check file size limits (if any)

### Debug Steps

1. Check service health: Run "Health Check" request
2. Verify environment: Check all variables are set
3. Check service logs: Look for error messages
4. Test with curl: Try direct API calls

## API Mapping

This collection tests endpoints that simulate real Slack APIs:

| Mock Endpoint | Real Slack API | Purpose |
|---------------|----------------|---------|
| `POST /api/chat.postMessage` | `chat.postMessage` | Send messages |
| `GET /api/conversations.history` | `conversations.history` | Get message history |
| `POST /api/files.upload` | `files.upload` | Upload files |

## Advanced Usage

### Custom Variables

You can add custom environment variables:

```json
{
  "key": "custom_message",
  "value": "My custom test message",
  "enabled": true
}
```

### Pre-request Scripts

The collection includes pre-request scripts that:
- Set default values if variables are missing
- Generate dynamic data (timestamps, etc.)

### Test Scripts

Each request has test scripts that:
- Validate response structure
- Store data for subsequent requests
- Check performance metrics

## Integration with CI/CD

You can run this collection in automated pipelines:

```bash
# Using Newman (Postman CLI)
newman run Slack_Mock_API.postman_collection.json \
  -e Slack_Mock_Environment.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

This enables automated testing of the Slack mock service in your deployment pipeline.
