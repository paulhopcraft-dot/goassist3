"""GoAssist v3.0 - FastAPI Application Entry Point.

Speech-to-speech conversational agent with optional digital human avatar.

Reference:
- TMF v3.0: Architecture contracts
- PRD v3.0: Product requirements
- Ops-Runbook v3.0: Deployment configuration
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src import __version__
from src.api.routes import health
from src.api.routes import sessions
from src.config.settings import Settings, get_settings
from src.observability.logging import init_logging

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown of components.
    """
    settings = get_settings()
    logger.info(
        "goassist_starting",
        version=__version__,
        environment=settings.environment,
        port=settings.api_port,
    )

    # Startup: Initialize components
    try:
        # Initialize structured logging
        init_logging(json_format=settings.environment == "production")

        # Mark components as initializing
        health.set_component_health("vad", True)
        health.set_component_health("session_manager", True)
        health.set_component_health("webrtc_gateway", True)

        # Initialize session manager
        session_manager = sessions.get_session_manager()
        logger.info("session_manager_initialized", max_sessions=session_manager._max_sessions)

        # Initialize WebRTC gateway
        webrtc_gateway = sessions.get_webrtc_gateway()
        logger.info("webrtc_gateway_initialized")

        # TODO: Initialize remaining components
        # - ASR (deepgram/faster-whisper)
        # - TTS (streaming)
        # - LLM (vLLM client)

        # Brief delay for any async initialization
        await asyncio.sleep(0.1)

        # Mark service as ready
        health.set_ready(True)
        logger.info("goassist_ready", components=health.get_component_health())

    except Exception as e:
        logger.error("goassist_startup_failed", error=str(e))
        raise

    yield  # Application runs here

    # Shutdown: Cleanup components
    logger.info("goassist_shutting_down")
    health.set_ready(False)

    # End all active sessions
    session_manager = sessions.get_session_manager()
    ended_count = await session_manager.end_all_sessions(reason="shutdown")
    logger.info("sessions_ended", count=ended_count)

    # Close WebRTC connections
    webrtc_gateway = sessions.get_webrtc_gateway()
    await webrtc_gateway.close_all()
    logger.info("webrtc_connections_closed")

    logger.info("goassist_shutdown_complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="GoAssist",
        description="Speech-to-speech conversational agent with optional digital human avatar",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(sessions.router)

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    log_level = settings.log_level.lower()

    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level),
    )

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=log_level,
        reload=settings.environment == "development",
    )
