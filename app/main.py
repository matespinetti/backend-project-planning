import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting up ProjectPlanning Proxy API...")
    logger.info("Proxy API ready - no local database initialization needed")
    logger.info(f"Cloud API URL: {settings.CLOUD_API_URL}")
    logger.info(f"Bonita URL: {settings.BONITA_URL}")

    yield

    # Shutdown
    logger.info("Shutting down ProjectPlanning Proxy API...")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="FastAPI Proxy API - Orchestrates between Next.js frontend, Bonita BPM, and Cloud Persistence API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "message": "ProjectPlanning Proxy API is running",
        "version": "2.0.0",
        "mode": "proxy",
        "services": {
            "bonita": settings.BONITA_URL,
            "cloud_api": settings.CLOUD_API_URL,
        },
        "docs_url": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "mode": "proxy"}
