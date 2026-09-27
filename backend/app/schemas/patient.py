"""Pydantic request/response contracts for patient endpoints.

Imports/dependencies: pydantic.

Public outputs: `PatientSummary`, `AllergyRecord`, `ConditionRecord`,
`PrescriptionRecord`, `MedicationHistoryRecord`, `PatientContext`,
`PatientMedications`.
"""

from pydantic import BaseModel, Field


class AllergyRecord(BaseModel):
    """A single recorded allergen/reaction pair.

    Attributes:
        allergen: Name of the allergen; ``none`` means no known allergies.
        reaction: Free-text description of the allergic reaction.
        severity: ``NONE | MILD | MODERATE | SEVERE | LIFE_THREATENING``.
    """

    allergen: str
    reaction: str | None = None
    severity: str = "UNKNOWN"


class ConditionRecord(BaseModel):
    """A diagnosed condition for a patient.

    Attributes:
        condition_code: ICD-10 or synthetic code.
        condition_name: Human-readable name.
        status: ``ACTIVE | RESOLVED | CHRONIC``.
        onset_date: ISO-8601 date string.
    """

    condition_code: str
    condition_name: str
    status: str = "ACTIVE"
    onset_date: str | None = None


class PrescriptionRecord(BaseModel):
    """A current or past prescription entry.

    Attributes:
        medication_id: FK to the medication table.
        medication_name: Canonical drug name (joined for display).
        dose: Dose string, e.g. ``500 mg``.
        frequency: Dosing frequency, e.g. ``twice daily``.
        route: Administration route.
        start_date: ISO-8601 start date.
        end_date: ISO-8601 end date; ``None`` if ongoing.
        status: ``ACTIVE | DISCONTINUED | COMPLETED``.
    """

    medication_id: int
    medication_name: str
    dose: str | None = None
    frequency: str | None = None
    route: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str = "ACTIVE"


class MedicationHistoryRecord(BaseModel):
    """A historical medication entry.

    Attributes:
        medication_id: FK to the medication table.
        medication_name: Canonical drug name (joined for display).
        dose: Dose string at time of use.
        frequency: Frequency at time of use.
        start_date: ISO-8601 start date.
        end_date: ISO-8601 end date.
        outcome: Free-text outcome description.
        notes: Additional clinical notes.
    """

    medication_id: int
    medication_name: str
    dose: str | None = None
    frequency: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    outcome: str | None = None
    notes: str | None = None


class PatientSummary(BaseModel):
    """Lightweight patient record for list/search responses.

    Attributes:
        id: Internal patient identifier.
        patient_code: Human-readable code, e.g. ``OMNI-001``.
        name: Full display name.
        sex: ``M`` or ``F``.
        pregnancy_status: ``PREGNANT | NOT_PREGNANT | NOT_APPLICABLE``.
        renal_status: Renal impairment status.
        hepatic_status: Hepatic impairment status.
        g6pd_status: G6PD enzyme status.
        date_of_birth: ISO-8601 date of birth string.
    """

    id: int
    patient_code: str
    name: str
    sex: str
    pregnancy_status: str
    renal_status: str
    hepatic_status: str
    g6pd_status: str
    date_of_birth: str


class PatientContext(BaseModel):
    """Full clinical context for a patient, used by rule modules.

    Attributes:
        id: Internal patient identifier.
        patient_code: Human-readable identifier.
        name: Full display name.
        date_of_birth: ISO-8601 date of birth; used to derive age in rule
            modules.
        sex: ``M`` or ``F``.
        pregnancy_status: ``PREGNANT | NOT_PREGNANT | NOT_APPLICABLE``.
        renal_status: ``NORMAL | MILD_IMPAIRMENT | MODERATE_IMPAIRMENT |
            SEVERE_IMPAIRMENT | UNKNOWN``.
        hepatic_status: ``NORMAL | MILD_IMPAIRMENT | MODERATE_IMPAIRMENT |
            SEVERE_IMPAIRMENT | UNKNOWN``.
        g6pd_status: ``NORMAL | DEFICIENT | UNKNOWN``.
        allergies: All recorded allergen records.
        conditions: All diagnosed conditions (all statuses).
        current_prescriptions: Active prescriptions at time of retrieval.
        medication_history: Past medication entries.
    """

    id: int
    patient_code: str
    name: str
    date_of_birth: str
    sex: str
    pregnancy_status: str
    renal_status: str
    hepatic_status: str
    g6pd_status: str
    allergies: list[AllergyRecord] = Field(default_factory=list)
    conditions: list[ConditionRecord] = Field(default_factory=list)
    current_prescriptions: list[PrescriptionRecord] = Field(default_factory=list)
    medication_history: list[MedicationHistoryRecord] = Field(default_factory=list)


class PatientMedications(BaseModel):
    """Current and historical medication data for a patient.

    Attributes:
        patient_id: The patient identifier.
        current_prescriptions: Active prescriptions.
        medication_history: Past medication entries.
    """

    patient_id: int
    current_prescriptions: list[PrescriptionRecord] = Field(default_factory=list)
    medication_history: list[MedicationHistoryRecord] = Field(default_factory=list)
