# backend/app/main.py
"""
Main FastAPI application entry point.

This file creates and configures the FastAPI application with:
- API routes
- Middleware (CORS, error handling, etc.)
- Database initialization
- Documentation
- Health checks

Think of this as the "main" function for your web server.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

# Import your configuration and database
from app.core.config import settings
from app.core.database import init_db, close_db

# Import API routers
from app.api.v1.leads import router as leads_router
from app.api.v1.campaigns import router as campaigns_router
# from app.api.v1.agents import router as agents_router        # We'll add this later
# from app.api.v1.auth import router as auth_router            # We'll add this later

# Set up logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    This function runs code when the application starts up and shuts down.
    It's the modern way to handle startup/shutdown events in FastAPI.
    
    Startup tasks:
    - Initialize database connections
    - Set up monitoring
    - Warm up caches
    
    Shutdown tasks:
    - Close database connections
    - Clean up resources
    """
    
    # Startup
    logger.info("🚀 Starting Sales Automation SaaS API")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'Not configured'}")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # TODO: Add other startup tasks here:
        # - Initialize MCP connections
        # - Set up background tasks
        # - Warm up AI models
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down Sales Automation SaaS API")
    try:
        await close_db()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    🚀 **Sales Automation SaaS API**
    
    A modern sales automation platform that uses AI agents to:
    - Generate and manage leads
    - Automate email outreach campaigns  
    - Integrate with external services via MCP (Model Context Protocol)
    - Provide multi-tenant SaaS functionality
    
    ## Features
    
    * **Lead Management**: Create, update, and track leads with scoring
    * **AI Agents**: Customize email generation and outreach automation
    * **Multi-tenant**: Secure data isolation per company
    * **MCP Integration**: Connect to Gmail, Apollo, and other services
    * **Rate Limiting**: Built-in protection against abuse
    
    ## Authentication
    
    All endpoints (except health checks) require JWT authentication.
    Include your token in the Authorization header:
    
    ```
    Authorization: Bearer your-jwt-token-here
    ```
    """,
    docs_url="/docs" if settings.debug else None,  # Hide docs in production
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Middleware Configuration
# Order matters! Middleware runs in the order it's added.

# 1. Trusted Host Middleware (security)
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]  # Update for production
    )

# 2. CORS Middleware (for your React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# 3. Custom middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all API requests and their response times.
    
    This is invaluable for debugging and monitoring your API performance.
    In production, you'd send this data to a monitoring service.
    """
    
    start_time = time.time()
    
    # Log incoming request
    logger.info(
        f"🌐 {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'Unknown'}"
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"✅ {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # Add timing header (useful for frontend performance monitoring)
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Exception Handlers
# These catch specific types of errors and return user-friendly responses

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors with detailed messages.
    
    When a user sends invalid data, this returns a clear explanation
    of what went wrong instead of a generic error.
    """
    
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    """
    Handle unexpected server errors gracefully.
    
    In production, you'd log the full error details but only return
    a generic message to users for security.
    """
    
    logger.error(f"Internal server error on {request.url.path}: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred",
            "request_id": str(time.time())  # Help users report issues
        }
    )

# API Routes
# We organize routes by version for future API evolution

# Health check endpoint (no authentication required)
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns basic system status. In production, you'd add checks for:
    - Database connectivity
    - External service health
    - Memory/CPU usage
    """
    
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": time.time()
    }

# API v1 routes
app.include_router(leads_router, prefix="/api/v1")
app.include_router(campaigns_router, prefix="/api/v1")
# app.include_router(agents_router, prefix="/api/v1")     # Coming next!
# app.include_router(auth_router, prefix="/api/v1")       # Coming next!

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with basic API information.
    
    This is what users see when they visit your API base URL.
    """
    
    return {
        "message": "🚀 Sales Automation SaaS API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation not available in production",
        "health": "/health"
    }

# Development helpers
if settings.debug:
    @app.get("/debug/settings", tags=["Debug"])
    async def debug_settings():
        """Debug endpoint to check configuration (development only)."""
        
        return {
            "debug": settings.debug,
            "database_configured": bool(settings.database_url),
            "database_url": settings.database_url.split('@')[1] if '@' in settings.database_url else settings.database_url,
            "cors_origins": settings.allowed_origins,
            "rate_limits": {
                "api_per_minute": settings.rate_limit_per_minute,
                "email_per_hour": settings.email_rate_limit_per_hour
            }
        }
    
    @app.get("/debug/test-db", tags=["Debug"])
    async def test_database():
        """Test database connection."""
        try:
            from app.core.database import get_db
            async for db in get_db():
                # Try a simple query
                from sqlalchemy import text
                result = await db.execute(text("SELECT 1"))
                await result.fetchone()
                return {"status": "Database connection successful"}
        except Exception as e:
            return {"status": "Database connection failed", "error": str(e)}

# Application startup message
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🔧 Starting development server...")
    logger.info("📝 API Documentation: http://localhost:8000/docs")
    logger.info("🏥 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )