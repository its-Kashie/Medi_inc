"""
HealthLink360 Backend Core - Healthcare Operations
FastAPI application for real-time healthcare service delivery
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time

from shared.config import settings
from shared.logger import app_logger

# Import routers (will be created)
# from backend_core.routers import auth, patients, emergency, maternal, mental, pharmacy, criminal, waste


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    app_logger.info("🚀 HealthLink360 Backend Core starting...")
    app_logger.info(f"Environment: {settings.environment}")
    app_logger.info(f"Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    app_logger.info("🛑 HealthLink360 Backend Core shutting down...")


# Create FastAPI application
app = FastAPI(
    title="HealthLink360 - Backend Core",
    description="Healthcare Operations API - Real-time patient care, emergency response, and clinical services",
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
        "service": "HealthLink360 Backend Core",
        "version": "1.0.0",
        "environment": settings.environment
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": "HealthLink360 Backend Core API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health"
    }


# Include routers
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients"])
# app.include_router(emergency.router, prefix="/api/v1/emergency", tags=["Emergency"])
# app.include_router(maternal.router, prefix="/api/v1/maternal", tags=["Maternal Health"])
# app.include_router(mental.router, prefix="/api/v1/mental", tags=["Mental Health"])
# app.include_router(pharmacy.router, prefix="/api/v1/pharmacy", tags=["Pharmacy"])
# app.include_router(criminal.router, prefix="/api/v1/criminal", tags=["Criminal Cases"])
# app.include_router(waste.router, prefix="/api/v1/waste", tags=["Waste Management"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend:app",
        host=settings.backend_core_host,
        port=settings.backend_core_port,
        reload=settings.debug
    )
