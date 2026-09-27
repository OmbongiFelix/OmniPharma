"""HTTP endpoint for medication-safety screening and recommendation requests.

Validates `ScreeningRequest`, calls
`app.agents.orchestrator.run_medication_review()`, and returns
`ScreeningResponse`. Never runs a clinical rule directly — that would
duplicate the orchestrator's ordering guarantees (see
`AgentOrchestrator.run_medication_review`).

Imports/dependencies: fastapi, app.schemas.screening, app.agents.orchestrator.

Public outputs: route handlers registered under `/api/v1/screenings`.

    POST /api/v1/screenings/interaction -> ScreeningResponse
    POST /api/v1/recommendations        -> list[Recommendation]
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentOrchestrator
from app.core.exceptions import DrugResolutionError, PatientNotFoundError
from app.db.session import get_db
from app.schemas.screening import (
    Recommendation,
    RecommendationRequest,
    ScreeningRequest,
    ScreeningResponse,
)
from app.services import drug_catalog_service, recommendation_service

router = APIRouter()

# Single orchestrator instance (thread-safe: no mutable state per call).
_orchestrator = AgentOrchestrator()


@router.post(
    "/screenings/interaction",
    response_model=ScreeningResponse,
    summary="Run medication safety screening",
    description=(
        "Runs all deterministic safety checks (DDI, allergy, pregnancy, condition "
        "contraindications, age-based caution, duplicate therapy) against the patient's "
        "clinical context and returns structured findings."
    ),
)
def run_screening(
    payload: ScreeningRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ScreeningResponse:
    """Execute a full medication-safety review for a patient.

    Args:
        payload: :class:`~app.schemas.screening.ScreeningRequest` with
            patient_id, medications list and include_evidence flag.
        request: FastAPI request object used to extract the request ID
            injected by middleware.
        db: Injected database session.

    Returns:
        :class:`~app.schemas.screening.ScreeningResponse` with all
        findings, overall status, and optional LLM explanation.

    Raises:
        HTTPException: 404 if the patient does not exist.
        HTTPException: 422 if the medication list is empty.
    """
    if not payload.medications:
        raise HTTPException(status_code=422, detail="At least one medication must be provided.")

    request_id = request.headers.get("X-Request-ID", "unknown")

    try:
        return _orchestrator.run_medication_review(
            patient_id=payload.patient_id,
            medication_names=payload.medications,
            include_evidence=payload.include_evidence,
            db=db,
            request_id=request_id,
        )
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/recommendations",
    response_model=list[Recommendation],
    summary="Get medication recommendations",
    description=(
        "Generates a safety-filtered list of alternative medicine candidates from the "
        "local catalogue. Included and excluded candidates are both returned — excluded "
        "candidates carry a machine-readable exclusion reason."
    ),
)
def get_recommendations(
    payload: RecommendationRequest,
    db: Session = Depends(get_db),
) -> list[Recommendation]:
    """Generate and safety-filter alternative medicine candidates.

    Args:
        payload: :class:`~app.schemas.screening.RecommendationRequest`
            with patient_id, target_medication, and optional indication.
        db: Injected database session.

    Returns:
        List of :class:`~app.schemas.screening.Recommendation` objects,
        each marked included or excluded with a reason.

    Raises:
        HTTPException: 404 if the patient does not exist.
        HTTPException: 404 if ``target_medication`` cannot be resolved.
    """
    from app.services import patient_service

    try:
        patient = patient_service.get_patient_context(payload.patient_id, db)
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        target_med = drug_catalog_service.resolve_drug(payload.target_medication, db)
    except DrugResolutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return recommendation_service.recommend_alternatives(
        patient=patient,
        target_medication=target_med,
        indication=payload.indication,
        db=db,
    )
