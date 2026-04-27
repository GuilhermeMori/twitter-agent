"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.config import settings
from src.core.logging_config import setup_logging, get_logger
from src.api.middleware.request_logging import RequestLoggingMiddleware
from src.api.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)

# Setup logging
setup_logging(log_level="DEBUG" if settings.debug else "INFO")
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events"""
    # Startup
    logger.info("Starting Twitter Scraping SaaS Platform API")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info(f"API Version: {settings.app_version}")
    logger.info(f"Supabase URL: {settings.supabase_url}")
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Twitter Scraping SaaS Platform API")
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Backend API for Twitter scraping campaigns with automated execution",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API status"""
    return {
        "status": "ok",
        "message": "Twitter Scraping SaaS Platform API",
        "version": settings.app_version,
        "docs": "/api/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production",
    }


@app.get("/api/health", tags=["Health"])
async def api_health():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "api_version": settings.app_version,
        "services": {
            "database": "configured",  # Will be enhanced with actual health checks
            "redis": "configured",
            "celery": "configured",
        },
    }


# API route registration
from src.api.routes import configuration, campaigns, tweet_analysis, tweet_comments, assistants, communication_styles

app.include_router(configuration.router, prefix="/api", tags=["Configuration"])
app.include_router(campaigns.router, prefix="/api", tags=["Campaigns"])
app.include_router(assistants.router, prefix="/api", tags=["Assistants"])
app.include_router(communication_styles.router, prefix="/api", tags=["Communication Styles"])
app.include_router(tweet_analysis.router, prefix="/api", tags=["Tweet Analysis"])
app.include_router(tweet_comments.router, prefix="/api", tags=["Tweet Comments"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
