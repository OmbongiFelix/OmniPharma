"""Retrieves patient context from the patient database.

This is the only module allowed to assemble a full `PatientContext` from
raw rows across `patients`, `conditions`, `allergies`,
`medication_history`, and current `prescriptions`. Other modules must
depend on `PatientContext`, not on `db.repositories` directly.

Imports/dependencies: app.db.session, app.db.repositories,
app.schemas.patient.

Public outputs: `get_patient_context()`, `list_patients()`.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import PatientNotFoundError
from app.db.models import Medication, Prescription
from app.db.repositories import PatientRepository
from app.schemas.patient import (
    AllergyRecord,
    ConditionRecord,
    MedicationHistoryRecord,
    PatientContext,
    PatientMedications,
    PatientSummary,
    PrescriptionRecord,
)


def _medication_name(db: Session, medication_id: int) -> str:
    """Resolve a medication id to its canonical name.

    Args:
        db: Active SQLAlchemy session.
        medication_id: Medication primary key.

    Returns:
        Canonical name string, or a fallback placeholder if not found.
    """
    med = db.get(Medication, medication_id)
    return med.canonical_name if med else f"medication#{medication_id}"


def get_patient_context(patient_id: int, db: Session) -> PatientContext:
    """Retrieve a patient's full clinical context.

    Args:
        patient_id: Internal patient identifier.
        db: Active SQLAlchemy session (injected by the service caller).

    Returns:
        A `PatientContext` combining demographics, derived age,
        pregnancy status, renal status, hepatic status, g6pd status,
        allergies, active conditions, current prescriptions and
        medication history.

    Raises:
        PatientNotFoundError: If no patient with `patient_id` exists.

    Notes:
        Fields recorded as `UNKNOWN` (renal_status, hepatic_status,
        g6pd_status) are returned as `UNKNOWN`, never coerced to
        `NORMAL`. Downstream rule modules must treat `UNKNOWN` as a
        data-gap warning, not a negative result.
    """
    repo = PatientRepository(db)
    patient = repo.get_by_id(patient_id)
    if patient is None:
        raise PatientNotFoundError(f"Patient {patient_id} not found.")

    conditions = [
        ConditionRecord(
            condition_code=c.condition_code,
            condition_name=c.condition_name,
            status=c.status,
            onset_date=c.onset_date,
        )
        for c in repo.get_conditions(patient_id)
    ]

    allergies = [
        AllergyRecord(
            allergen=a.allergen,
            reaction=a.reaction,
            severity=a.severity,
        )
        for a in repo.get_allergies(patient_id)
    ]

    current_prescriptions = [
        PrescriptionRecord(
            medication_id=p.medication_id,
            medication_name=_medication_name(db, p.medication_id),
            dose=p.dose,
            frequency=p.frequency,
            route=p.route,
            start_date=p.start_date,
            end_date=p.end_date,
            status=p.status,
        )
        for p in repo.get_active_prescriptions(patient_id)
    ]

    history = [
        MedicationHistoryRecord(
            medication_id=h.medication_id,
            medication_name=_medication_name(db, h.medication_id),
            dose=h.dose,
            frequency=h.frequency,
            start_date=h.start_date,
            end_date=h.end_date,
            outcome=h.outcome,
            notes=h.notes,
        )
        for h in repo.get_medication_history(patient_id)
    ]

    return PatientContext(
        id=patient.id,
        patient_code=patient.patient_code,
        name=patient.name,
        date_of_birth=patient.date_of_birth,
        sex=patient.sex,
        pregnancy_status=patient.pregnancy_status,
        renal_status=patient.renal_status,
        hepatic_status=patient.hepatic_status,
        g6pd_status=patient.g6pd_status,
        conditions=conditions,
        allergies=allergies,
        current_prescriptions=current_prescriptions,
        medication_history=history,
    )


def list_patients(db: Session, query: str | None = None) -> list[PatientSummary]:
    """List or search synthetic patients for the patient-selection UI.

    Args:
        db: Active SQLAlchemy session.
        query: Optional case-insensitive substring match against
            `patient_code` or `name`. `None` returns all patients.

    Returns:
        Lightweight `PatientSummary` records (id, patient_code, name,
        sex, pregnancy_status) — not the full context, to keep the
        list endpoint cheap.
    """
    repo = PatientRepository(db)
    patients = repo.search(query) if query else repo.list_all()
    return [
        PatientSummary(
            id=p.id,
            patient_code=p.patient_code,
            name=p.name,
            sex=p.sex,
            pregnancy_status=p.pregnancy_status,
            renal_status=p.renal_status,
            hepatic_status=p.hepatic_status,
            g6pd_status=p.g6pd_status,
            date_of_birth=p.date_of_birth,
        )
        for p in patients
    ]


def get_patient_medications(patient_id: int, db: Session) -> PatientMedications:
    """Retrieve current prescriptions and history for a patient.

    Args:
        patient_id: Internal patient identifier.
        db: Active SQLAlchemy session.

    Returns:
        :class:`~app.schemas.patient.PatientMedications` with current
        prescriptions and medication history.

    Raises:
        PatientNotFoundError: If no patient with `patient_id` exists.
    """
    repo = PatientRepository(db)
    patient = repo.get_by_id(patient_id)
    if patient is None:
        raise PatientNotFoundError(f"Patient {patient_id} not found.")

    current = [
        PrescriptionRecord(
            medication_id=p.medication_id,
            medication_name=_medication_name(db, p.medication_id),
            dose=p.dose,
            frequency=p.frequency,
            route=p.route,
            start_date=p.start_date,
            end_date=p.end_date,
            status=p.status,
        )
        for p in repo.get_active_prescriptions(patient_id)
    ]

    history = [
        MedicationHistoryRecord(
            medication_id=h.medication_id,
            medication_name=_medication_name(db, h.medication_id),
            dose=h.dose,
            frequency=h.frequency,
            start_date=h.start_date,
            end_date=h.end_date,
            outcome=h.outcome,
            notes=h.notes,
        )
        for h in repo.get_medication_history(patient_id)
    ]

    return PatientMedications(
        patient_id=patient_id,
        current_prescriptions=current,
        medication_history=history,
    )
