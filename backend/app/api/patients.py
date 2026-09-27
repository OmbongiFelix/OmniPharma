"""HTTP endpoints for synthetic patient demographics and history.

Thin request/response layer only: every handler validates input with
Pydantic, delegates to `app.services.patient_service`, and maps service
exceptions to HTTP errors. Handlers must not query the database directly.

Imports/dependencies: fastapi, app.schemas.patient, app.services.patient_service.

Public outputs: route handlers registered under `/api/v1/patients`.

    GET  /api/v1/patients                       -> list[PatientSummary]
    GET  /api/v1/patients/{patient_id}           -> PatientContext
    GET  /api/v1/patients/{patient_id}/medications -> PatientMedications
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.exceptions import PatientNotFoundError
from app.db.session import get_db
from app.schemas.patient import PatientContext, PatientMedications, PatientSummary
from app.services import patient_service

router = APIRouter()


@router.get(
    "/patients",
    response_model=list[PatientSummary],
    summary="List synthetic patients",
    description="List all patients, or search by name/code.",
)
def list_patients(
    q: str | None = Query(default=None, description="Case-insensitive name/code substring search"),
    db: Session = Depends(get_db),
) -> list[PatientSummary]:
    """Return a list of patient summaries, optionally filtered by search term.

    Args:
        q: Optional search query substring matched against name or patient_code.
        db: Injected database session.

    Returns:
        List of lightweight :class:`~app.schemas.patient.PatientSummary` records.
    """
    return patient_service.list_patients(db, query=q)


@router.get(
    "/patients/{patient_id}",
    response_model=PatientContext,
    summary="Get patient context",
    description="Return full clinical context for a single patient.",
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
) -> PatientContext:
    """Return the full clinical context for a patient.

    Args:
        patient_id: Internal patient identifier.
        db: Injected database session.

    Returns:
        :class:`~app.schemas.patient.PatientContext` with demographics,
        conditions, allergies, prescriptions and history.

    Raises:
        HTTPException: 404 if the patient does not exist.
    """
    try:
        return patient_service.get_patient_context(patient_id, db)
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/patients/{patient_id}/medications",
    response_model=PatientMedications,
    summary="Get patient medications",
    description="Return current prescriptions and medication history for a patient.",
)
def get_patient_medications(
    patient_id: int,
    db: Session = Depends(get_db),
) -> PatientMedications:
    """Return current prescriptions and history for a patient.

    Args:
        patient_id: Internal patient identifier.
        db: Injected database session.

    Returns:
        :class:`~app.schemas.patient.PatientMedications` with active
        prescriptions and historical medication entries.

    Raises:
        HTTPException: 404 if the patient does not exist.
    """
    try:
        return patient_service.get_patient_medications(patient_id, db)
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
