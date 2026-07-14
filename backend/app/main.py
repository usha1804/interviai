from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import Base, engine
from app.routes import auth, interview, analytics, admin
from app.routes import resume as resume_router
from app.routes import webcam as webcam_router
from app.routes import coding as coding_router
from app.routes import proctor as proctor_router
from app.routes import rag as rag_router
from app.routes import career_coach as career_coach_router
from app.routes import enhanced_report as report_router
from app.routes import ats as ats_router
from app.routes import adaptive as adaptive_router
from app.routes import github_analyzer as github_router
from app.routes import system_design as system_design_router
from app.routes import voice_interview as voice_router
from app.routes import recruiter as recruiter_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    
    # Startup
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Global exception handler — must include CORS headers manually
# because Starlette's CORSMiddleware doesn't wrap unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Exception: {str(exc)}")
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in settings.CORS_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    # Surface the real error message in development
    detail = str(exc) if settings.DEBUG else "Internal server error"
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
        headers=headers,
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }


# API Info endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": f"Welcome to {settings.API_TITLE}",
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "documentation": "/docs"
    }


# Include routers
app.include_router(auth.router)
app.include_router(interview.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(resume_router.router)
app.include_router(webcam_router.router)
app.include_router(coding_router.router)
app.include_router(proctor_router.router)
app.include_router(rag_router.router)
app.include_router(career_coach_router.router)
app.include_router(report_router.router)
app.include_router(ats_router.router)
app.include_router(adaptive_router.router)
app.include_router(github_router.router)
app.include_router(system_design_router.router)
app.include_router(voice_router.router)
app.include_router(recruiter_router.router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
