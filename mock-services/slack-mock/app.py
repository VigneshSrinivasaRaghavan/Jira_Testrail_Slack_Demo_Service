"""
Slack Mock Service

A FastAPI-based mock service that simulates Slack's chat.postMessage and conversations.history APIs
for testing and development purposes.

Features:
- Chat message posting and retrieval
- File upload simulation
- Channel management
- Simple web UI for viewing channels and messages
- Bearer token authentication
- SQLite storage with seed data

Endpoints:
- POST /api/chat.postMessage - Send messages to channels
- GET /api/conversations.history - Get channel message history  
- POST /api/files.upload - Upload files (optional)
- GET /ui - Web interface for channels
- GET /ui/channel/{name} - Channel view
- GET /docs - Swagger documentation
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.openapi.utils import get_openapi
import time

from storage import init_db
from routes import api_router, ui_router, SlackAuthError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan manager."""
    try:
        logger.info("Starting Slack Mock Service...")
        
        # Initialize database
        init_db()
        logger.info("Database initialized with seed data")
        
        yield
        
    except Exception as e:
        logger.error("Error during startup: %s", e)
        raise
    finally:
        logger.info("Shutting down Slack Mock Service...")


API_DESCRIPTION = """
## 🔐 Authentication — Required for every API call

All API endpoints require a **Bearer token** in the `Authorization` header.

### ✅ Use this token for all requests:

```
Authorization: Bearer xoxb-mock-bot-token
```

### How to authenticate in this Swagger UI:
1. Click the **🔒 Authorize** button at the top-right of this page
2. In the **BearerAuth** field, enter: `xoxb-mock-bot-token`
3. Click **Authorize**, then **Close**
4. All requests you send from this page will now include the correct header automatically

---

### Token format rules (same as real Slack)
| Token prefix | Type | Example |
|---|---|---|
| `xoxb-` | Bot token | `xoxb-mock-bot-token` |
| `xoxp-` | User token | `xoxp-mock-user-token` |
| `demo-token` | Dev shortcut | `demo-token` |
| `test-token` | Dev shortcut | `test-token` |

> Any string starting with `xoxb-` or `xoxp-` is accepted — the value after the prefix does not matter in this mock.

---

## 📡 Key Endpoints

| Method | Endpoint | What it does |
|---|---|---|
| `POST` | `/api/chat.postMessage` | **Send a message to a channel** |
| `GET` | `/api/conversations.list` | List all channels |
| `GET` | `/api/conversations.history` | Get messages in a channel |
| `GET` | `/api/auth.test` | Validate your token |
| `GET` | `/api/users.list` | List all users |
| `POST` | `/api/conversations.create` | Create a new channel |
| `POST` | `/api/chat.update` | Edit a message |
| `POST` | `/api/chat.delete` | Delete a message |
| `POST` | `/api/reactions.add` | Add an emoji reaction |

---

## 🚀 Quick Example — Send a message

```bash
curl -X POST http://localhost:4003/api/chat.postMessage \\
  -H "Authorization: Bearer xoxb-mock-bot-token" \\
  -H "Content-Type: application/json" \\
  -d '{"channel": "qa-reports", "text": "Hello from the API!"}'
```

Every response follows Slack's format: `{"ok": true, ...}` on success or `{"ok": false, "error": "..."}` on failure.
"""

# Create FastAPI app
app = FastAPI(
    title="Slack Mock API",
    description=API_DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    # Log request
    logger.info("%s %s - %s", request.method, request.url.path, request.client.host if request.client else "unknown")
    
    # Process request
    response = await call_next(request)
    
    # Log response time
    process_time = time.time() - start_time
    logger.info("Request completed in %.3fs", process_time)
    
    return response


# Include routers
app.include_router(api_router, tags=["Slack API"])
app.include_router(ui_router, tags=["Web UI"])

# Static files (if any)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Root redirect
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to UI."""
    return RedirectResponse(url="/ui")


# Health check
@app.get("/health", tags=["System"])
async def health():
    """Service health check."""
    return {
        "status": "healthy",
        "service": "slack-mock",
        "version": "1.0.0",
        "timestamp": time.time()
    }


# Error handlers
@app.exception_handler(SlackAuthError)
async def slack_auth_error_handler(request: Request, exc: SlackAuthError):  # noqa: ARG001
    """Return Slack-style auth error: {"ok": false, "error": "..."}."""
    return JSONResponse(status_code=200, content={"ok": False, "error": exc.error_code})


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):  # noqa: ARG001
    """Handle 404 errors."""
    return JSONResponse(status_code=404, content={"error": "Not found", "detail": exc.detail})


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):  # noqa: ARG001
    """Handle 500 errors."""
    logger.error("Internal server error: %s", exc)
    return JSONResponse(status_code=500, content={"error": "Internal server error", "detail": str(exc)})


def custom_openapi():
    """Inject BearerAuth security scheme and pre-fill the default token."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add BearerAuth security scheme
    schema.setdefault("components", {})
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "Slack bot token  (e.g. xoxb-mock-bot-token)",
            "description": (
                "Enter your Slack-style bearer token.\n\n"
                "**Use this value:** `xoxb-mock-bot-token`\n\n"
                "Any token starting with `xoxb-` or `xoxp-` is accepted."
            ),
        }
    }

    # Apply security globally to every operation
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "tags" in operation:
                if "Slack API" in operation.get("tags", []):
                    operation.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "4003"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info("Starting Slack Mock Service on %s:%s", host, port)
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
