#!/usr/bin/env python3
"""Simple startup script for Slack Mock Service."""

import os
import logging
import uvicorn
from storage import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Main startup function."""
    logger.info("🚀 Starting Slack Mock Service...")
    
    # Initialize database first
    try:
        init_db()
        logger.info("✅ Database initialized with seed data")
    except Exception as e:
        logger.error("❌ Database initialization failed: %s", e)
        return
    
    # Import app after database is ready
    try:
        from app_simple import app
        logger.info("✅ FastAPI app imported successfully")
    except Exception as e:
        logger.error("❌ App import failed: %s", e)
        return
    
    # Start server
    port = int(os.getenv("PORT", "4003"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info("🌐 Starting server on %s:%s", host, port)
    logger.info("📡 API will be available at: http://%s:%s", host, port)
    logger.info("🌐 Web UI will be available at: http://%s:%s/ui", host, port)
    logger.info("📚 API docs will be available at: http://%s:%s/docs", host, port)
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.error("❌ Server startup failed: %s", e)

if __name__ == "__main__":
    main()
