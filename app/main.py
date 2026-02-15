from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.config import (
    API_TITLE, API_DESCRIPTION, API_VERSION,
    ALLOWED_ORIGINS
)
from app.routes import generate_router, styles_router
from app.services.queue_service import queue_service
import logging
import httpx
import asyncio
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keep-alive task reference
_keep_alive_task = None


async def keep_alive():
    """Self-ping every 10 minutes to prevent Render from sleeping"""
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if not render_url:
        logger.info("RENDER_EXTERNAL_URL not set, keep-alive disabled (local dev)")
        return

    health_url = f"{render_url}/health"
    logger.info(f"Keep-alive started: pinging {health_url} every 10 min")

    while True:
        await asyncio.sleep(600)  # 10 minutes
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(health_url)
                logger.info(f"Keep-alive ping: {response.status_code}")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global _keep_alive_task
    # Startup: Start queue workers
    logger.info("Starting queue workers...")
    await queue_service.start_workers()
    logger.info("Queue workers started (max concurrent: 3)")
    # Start keep-alive
    _keep_alive_task = asyncio.create_task(keep_alive())
    yield
    # Shutdown: cleanup
    logger.info("Shutting down...")
    if _keep_alive_task:
        _keep_alive_task.cancel()


# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration - Use configured origins, not wildcard in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],  # Only needed methods
    allow_headers=["Content-Type", "X-Requested-With"],
    max_age=3600,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors with request body for debugging"""
    try:
        body = await request.body()
        body_str = body.decode('utf-8', errors='ignore')[:500]  # Limit log size
        logger.error(f"Validation error on {request.url} - Body: {body_str}")
    except Exception as e:
        logger.error(f"Could not read request body: {e}")

    # Format errors in user-friendly way
    formatted_errors = []
    for error in exc.errors()[:5]:  # Limit to 5 errors
        field = error.get('loc', ['unknown'])[-1]
        msg = error.get('msg', 'Invalid value')
        formatted_errors.append(f"{field}: {msg}")

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": formatted_errors
        }
    )


# Include routers
app.include_router(generate_router, prefix=f"/api/{API_VERSION}")
app.include_router(styles_router, prefix=f"/api/{API_VERSION}")


@app.get("/health")
async def health_check():
    """Health check endpoint with dependency validation"""
    health_status = {"status": "healthy", "services": {}}

    # Check Pollinations.ai connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head("https://gen.pollinations.ai/image/models")
            health_status["services"]["pollinations"] = "ok" if response.status_code < 500 else "degraded"
    except Exception as e:
        logger.warning(f"Pollinations health check failed: {e}")
        health_status["services"]["pollinations"] = "unreachable"
        health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health"
    }
