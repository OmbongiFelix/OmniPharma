"""FastAPI application entry point for OmniPharma.

Registers all API routers under `/api/v1`, configures CORS from
`app.core.config.Settings`, attaches request-ID and structured-logging
middleware, and exposes startup/shutdown hooks that open and close the
database engine. This module contains no business logic: it wires
together `app.api.*` routers and `app.core.config`.

Imports/dependencies: fastapi, app.api.health, app.api.patients,
app.api.screening, app.api.medications, app.core.config, app.core.logging.

Public outputs: `app`, the FastAPI ASGI application object served by
uvicorn (`uvicorn app.main:app`).
"""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import health, medications, patients, screening
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import create_all_tables

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage application startup and shutdown events.

    On startup: configure logging and create any missing DB tables.
    On shutdown: no explicit teardown needed for SQLite.

    Args:
        application: The FastAPI application instance.

    Yields:
        None; resumes after the application shuts down.
    """
    configure_logging()
    logger.info("OmniPharma backend starting up.")
    create_all_tables()
    logger.info("Database tables verified/created.")
    yield
    logger.info("OmniPharma backend shutting down.")


settings = get_settings()

app = FastAPI(
    title="OmniPharma API",
    description=(
        "Agentic pharmacist/clinical decision-support API. "
        "Provides patient-context-aware medication safety screening, "
        "drug-drug interaction checks, and Kenya-specific medicine recommendations."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request-ID middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Inject a unique X-Request-ID into each request and response.

    Args:
        request: Incoming HTTP request.
        call_next: Next middleware or route handler.

    Returns:
        HTTP response with ``X-Request-ID`` header attached.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ---------------------------------------------------------------------------
# Structured request logging middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every incoming request and its response status code.

    Args:
        request: Incoming HTTP request.
        call_next: Next middleware or route handler.

    Returns:
        The HTTP response after logging.
    """
    logger.info(
        "Incoming request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": str(request.client),
        },
    )
    response = await call_next(request)
    logger.info(
        "Request completed",
        extra={"status_code": response.status_code, "path": request.url.path},
    )
    return response


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
_PREFIX = "/api/v1"

app.include_router(health.router, prefix=_PREFIX, tags=["Health"])
app.include_router(patients.router, prefix=_PREFIX, tags=["Patients"])
app.include_router(medications.router, prefix=_PREFIX, tags=["Medications"])
app.include_router(screening.router, prefix=_PREFIX, tags=["Screening"])


@app.get("/", include_in_schema=False)
async def root():
    """Redirect-style root endpoint.

    Returns:
        A JSON object pointing to the API documentation.
    """
    return {"message": "OmniPharma API — see /docs for the OpenAPI spec."}
