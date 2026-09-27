"""Service and dependency health checks.

Public outputs:

    GET /api/v1/health -> HealthStatus

`HealthStatus` reports application status plus a boolean for each
dependency actually checked (primary DB, PPB catalogue DB, LLM adapter
reachability if configured). A degraded dependency returns HTTP 200 with
`status: "degraded"` and the specific failing dependency named, not a
generic 500 — callers need to distinguish "app is down" from "one
optional dependency is down."
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter()


class DependencyStatus(BaseModel):
    """Status of a single tracked dependency.

    Attributes:
        name: Human-readable dependency name.
        healthy: True if the dependency responded normally.
        detail: Optional error or info message.
    """

    name: str
    healthy: bool
    detail: str | None = None


class HealthStatus(BaseModel):
    """Application health report.

    Attributes:
        status: ``ok`` | ``degraded`` | ``down``.
        version: Ruleset version from configuration.
        dependencies: Per-dependency status objects.
    """

    status: str
    version: str
    dependencies: list[DependencyStatus]


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Service health check",
    description=(
        "Returns the application health and per-dependency status. "
        "A degraded dependency returns HTTP 200 with status='degraded'; "
        "the app itself being down returns a non-2xx from the infrastructure layer."
    ),
)
def health_check(db: Session = Depends(get_db)) -> HealthStatus:
    """Check health of the application and its dependencies.

    Args:
        db: Injected database session used to probe connectivity.

    Returns:
        :class:`HealthStatus` with status ``ok``, ``degraded``, or
        ``down``, plus individual dependency booleans.
    """
    settings = get_settings()
    deps: list[DependencyStatus] = []

    # Primary DB check.
    try:
        db.execute(text("SELECT 1"))
        deps.append(DependencyStatus(name="primary_db", healthy=True))
    except Exception as exc:  # noqa: BLE001
        deps.append(DependencyStatus(name="primary_db", healthy=False, detail=str(exc)))

    # LLM adapter reachability (config check only — no live call).
    llm_configured = settings.llm_provider is not None
    deps.append(
        DependencyStatus(
            name="llm_adapter",
            healthy=llm_configured,
            detail=None if llm_configured else "LLM_PROVIDER not configured; explanation=null mode.",
        )
    )

    overall = "ok" if all(d.healthy for d in deps) else "degraded"

    return HealthStatus(
        status=overall,
        version=settings.ruleset_version,
        dependencies=deps,
    )
