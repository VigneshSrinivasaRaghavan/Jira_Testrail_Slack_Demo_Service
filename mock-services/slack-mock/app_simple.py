"""
Slack Mock Service - Simplified Version

A FastAPI-based mock service that simulates Slack's chat.postMessage and conversations.history APIs
for testing and development purposes.
"""

import logging
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import time

from routes import api_router, ui_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app (without lifespan for now)
app = FastAPI(
    title="Slack Mock API",
    description="Mock Slack API for testing and development",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    client_host = request.client.host if request.client else "unknown"
    logger.info("%s %s - %s", request.method, request.url.path, client_host)
    
    try:
        # Process request
        response = await call_next(request)
        
        # Log response time
        process_time = time.time() - start_time
        logger.info("Request completed in %.3fs", process_time)
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error("Request failed in %.3fs: %s", process_time, e)
        raise

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

# Favicon handler
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return empty response for favicon requests."""
    from fastapi.responses import Response
    return Response(status_code=204)

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
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):  # noqa: ARG001
    """Handle 404 errors."""
    return {"error": "Not found", "detail": exc.detail, "status_code": 404}

@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):  # noqa: ARG001
    """Handle 401 errors."""
    return {"error": "Unauthorized", "detail": exc.detail, "status_code": 401}

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):  # noqa: ARG001
    """Handle 500 errors."""
    logger.error("Internal server error: %s", exc)
    return {"error": "Internal server error", "detail": str(exc), "status_code": 500}
