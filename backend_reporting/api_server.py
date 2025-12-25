"""
HealthLink360 Backend Reporting - Analytics & Research
FastAPI application for reporting, analytics, and research coordination
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import settings
from shared.logger import app_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    app_logger.info("🚀 HealthLink360 Backend Reporting starting...")
    app_logger.info(f"Environment: {settings.environment}")
    app_logger.info(f"Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    app_logger.info("🛑 HealthLink360 Backend Reporting shutting down...")


# Create FastAPI application
app = FastAPI(
    title="HealthLink360 - Backend Reporting",
    description="Analytics & Research API - Department agents, orchestrators, and WHO/NIH reporting",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    app_logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": "Validation error occurred"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    app_logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "HealthLink360 Backend Reporting",
        "version": "1.0.0",
        "environment": settings.environment
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": "HealthLink360 Backend Reporting API",
        "version": "1.0.0",
        "description": "Analytics, Research & WHO/NIH Reporting",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health"
    }


# Agent status endpoint
@app.get("/agents/status", tags=["Agents"])
async def get_agents_status():
    """Get status of all AI agents"""
    return {
        "department_agents": {
            "cardiology": {"status": "active", "last_report": "2025-12-24"},
            "maternal_health": {"status": "active", "last_report": "2025-12-24"},
            "infectious_diseases": {"status": "active", "last_report": "2025-12-24"},
            "nutrition": {"status": "active", "last_report": "2025-12-24"},
            "mental_health": {"status": "active", "last_report": "2025-12-24"},
            "ncd": {"status": "active", "last_report": "2025-12-24"},
            "endocrinology": {"status": "active", "last_report": "2025-12-24"},
            "oncology": {"status": "active", "last_report": "2025-12-24"}
        },
        "orchestrator_agents": {
            "hospital_central": {"status": "active", "hospitals_managed": 15},
            "nih": {"status": "active", "reports_processed": 342},
            "rnd": {"status": "active", "active_trials": 23}
        },
        "mcp_servers": {
            "core_agents": {"status": "online", "port": settings.mcp_core_agents_port},
            "nih": {"status": "online", "port": settings.mcp_nih_port},
            "orchestrator": {"status": "online", "port": settings.mcp_orchestrator_port},
            "report_generation": {"status": "online", "port": settings.mcp_report_gen_port},
            "rnd": {"status": "online", "port": settings.mcp_rnd_port}
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host=settings.backend_reporting_host,
        port=settings.backend_reporting_port,
        reload=settings.debug
    )
