"""SQLAlchemy ORM models for patients, conditions, allergies,
medications, prescriptions, medication history, inventory, and every
rule table (drug-drug interactions, pregnancy warnings,
condition-drug contraindications, allergy cross-reactivity).

Imports/dependencies: sqlalchemy.

Public outputs: `Patient`, `Condition`, `Allergy`, `Medication`,
`Prescription`, `MedicationHistory`, `Inventory`, `InteractionRule`,
`PregnancyDrugWarning`, `ConditionDrugContraindication`,
`AllergyCrossReactivity`, `ScreeningAudit`.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base class shared by all ORM models."""


class Patient(Base):
    """Represents a synthetic patient record.

    Attributes:
        id: Surrogate integer primary key.
        patient_code: Human-readable identifier, e.g. ``OMNI-001``.
        name: Full display name of the patient.
        date_of_birth: ISO-8601 date string (``YYYY-MM-DD``).
        sex: ``M`` or ``F``.
        pregnancy_status: ``PREGNANT | NOT_PREGNANT | NOT_APPLICABLE``.
        renal_status: ``NORMAL | MILD_IMPAIRMENT | MODERATE_IMPAIRMENT | SEVERE_IMPAIRMENT | UNKNOWN``.
        hepatic_status: ``NORMAL | MILD_IMPAIRMENT | MODERATE_IMPAIRMENT | SEVERE_IMPAIRMENT | UNKNOWN``.
        g6pd_status: ``NORMAL | DEFICIENT | UNKNOWN``.
        conditions: Joined conditions for this patient.
        allergies: Joined allergy records for this patient.
        prescriptions: Active and historical prescriptions.
        medication_history: Past medication entries.
    """

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    sex: Mapped[str] = mapped_column(String(1), nullable=False)  # M | F
    pregnancy_status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOT_APPLICABLE")
    renal_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNKNOWN")
    hepatic_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNKNOWN")
    g6pd_status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")

    conditions: Mapped[list["Condition"]] = relationship("Condition", back_populates="patient", lazy="select")
    allergies: Mapped[list["Allergy"]] = relationship("Allergy", back_populates="patient", lazy="select")
    prescriptions: Mapped[list["Prescription"]] = relationship("Prescription", back_populates="patient", lazy="select")
    medication_history: Mapped[list["MedicationHistory"]] = relationship(
        "MedicationHistory", back_populates="patient", lazy="select"
    )


class Condition(Base):
    """A diagnosed condition recorded for a patient.

    Attributes:
        id: Surrogate integer primary key.
        patient_id: Foreign key to :class:`Patient`.
        condition_code: ICD-10 or synthetic code, e.g. ``N18``.
        condition_name: Human-readable condition name.
        status: ``ACTIVE | RESOLVED | CHRONIC``.
        onset_date: ISO-8601 onset date string.
    """

    __tablename__ = "conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    condition_code: Mapped[str] = mapped_column(String(20), nullable=False)
    condition_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    onset_date: Mapped[str | None] = mapped_column(String(10), nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="conditions")

    __table_args__ = (Index("ix_conditions_patient_id", "patient_id"),)


class Allergy(Base):
    """A recorded drug or substance allergy for a patient.

    Attributes:
        id: Surrogate integer primary key.
        patient_id: Foreign key to :class:`Patient`.
        allergen: Allergen name; ``none`` indicates no known allergies.
        reaction: Free-text description of the allergic reaction.
        severity: ``NONE | MILD | MODERATE | SEVERE | LIFE_THREATENING``.
    """

    __tablename__ = "allergies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    allergen: Mapped[str] = mapped_column(String(200), nullable=False)
    reaction: Mapped[str | None] = mapped_column(String(500), nullable=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="UNKNOWN")

    patient: Mapped["Patient"] = relationship("Patient", back_populates="allergies")

    __table_args__ = (Index("ix_allergies_patient_id", "patient_id"),)


class Medication(Base):
    """A canonical drug/product record in the local catalogue.

    Attributes:
        id: Surrogate integer primary key.
        canonical_name: Normalised lowercase INN-based name used as the
            primary key for rule lookups.
        inn: International Non-proprietary Name (API).
        trade_name: Registered trade name.
        dosage_form: Tablet | Capsule | Syrup | Injection | etc.
        strength: e.g. ``500 mg``.
        source: Data provenance tag (``ppb-scraped`` | ``synthetic demo``).
    """

    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    inn: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    trade_name: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    dosage_form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)

    prescriptions: Mapped[list["Prescription"]] = relationship("Prescription", back_populates="medication")
    history_entries: Mapped[list["MedicationHistory"]] = relationship(
        "MedicationHistory", back_populates="medication"
    )
    inventory_entries: Mapped[list["Inventory"]] = relationship("Inventory", back_populates="medication")


class Prescription(Base):
    """An active or historical prescription linking a patient to a medication.

    Attributes:
        id: Surrogate integer primary key.
        patient_id: Foreign key to :class:`Patient`.
        medication_id: Foreign key to :class:`Medication`.
        dose: Prescribed dose string, e.g. ``500 mg``.
        frequency: Dosing frequency, e.g. ``twice daily``.
        route: Administration route, e.g. ``oral``.
        start_date: ISO-8601 start date.
        end_date: ISO-8601 end date; ``None`` for ongoing prescriptions.
        status: ``ACTIVE | DISCONTINUED | COMPLETED``.
        prescriber: Free-text prescriber name or facility.
    """

    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    medication_id: Mapped[int] = mapped_column(Integer, ForeignKey("medications.id"), nullable=False)
    dose: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    route: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    prescriber: Mapped[str | None] = mapped_column(String(200), nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="prescriptions")
    medication: Mapped["Medication"] = relationship("Medication", back_populates="prescriptions")

    __table_args__ = (
        Index("ix_prescriptions_patient_id", "patient_id"),
        Index("ix_prescriptions_medication_id", "medication_id"),
    )


class MedicationHistory(Base):
    """Past medication entry for a patient, outside current prescriptions.

    Attributes:
        id: Surrogate integer primary key.
        patient_id: Foreign key to :class:`Patient`.
        medication_id: Foreign key to :class:`Medication`.
        dose: Dose string at the time of use.
        frequency: Frequency at the time of use.
        start_date: ISO-8601 start date.
        end_date: ISO-8601 end date.
        outcome: Free-text outcome description.
        notes: Additional clinical notes.
    """

    __tablename__ = "medication_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    medication_id: Mapped[int] = mapped_column(Integer, ForeignKey("medications.id"), nullable=False)
    dose: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="medication_history")
    medication: Mapped["Medication"] = relationship("Medication", back_populates="history_entries")

    __table_args__ = (Index("ix_med_history_patient_id", "patient_id"),)


class Inventory(Base):
    """Current stock level for a medication at a facility.

    Attributes:
        id: Surrogate integer primary key.
        medication_id: Foreign key to :class:`Medication`.
        quantity: Current stock count (units).
        facility: Facility name or code.
        updated_at: ISO-8601 timestamp of the last stock update.
    """

    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    medication_id: Mapped[int] = mapped_column(Integer, ForeignKey("medications.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    facility: Mapped[str | None] = mapped_column(String(200), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    medication: Mapped["Medication"] = relationship("Medication", back_populates="inventory_entries")


class InteractionRule(Base):
    """A known drug-drug interaction rule row.

    Attributes:
        id: Surrogate integer primary key.
        drug_a: First drug in the interacting pair (canonical name).
        drug_b: Second drug in the interacting pair (canonical name).
        severity: ``INFO | LOW | MODERATE | HIGH | CONTRAINDICATED``.
        mechanism: Clinical mechanism of the interaction.
        recommendation: Recommended prescriber action.
        source: Data provenance tag.
        version: Ruleset version string.
    """

    __tablename__ = "interaction_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drug_a: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    drug_b: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    mechanism: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="demo-1.0")


class PregnancyDrugWarning(Base):
    """A pregnancy-specific drug warning row.

    Attributes:
        id: Surrogate integer primary key.
        drug_name: Canonical drug name.
        trimester_scope: ``ALL | FIRST | SECOND | THIRD``.
        severity: ``INFO | LOW | MODERATE | HIGH | CONTRAINDICATED``.
        mechanism: Clinical mechanism of teratogenicity or harm.
        recommendation: Prescriber guidance.
        source: Data provenance tag.
        version: Rule version string.
    """

    __tablename__ = "pregnancy_drug_warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drug_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    trimester_scope: Mapped[str] = mapped_column(String(10), nullable=False, default="ALL")
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    mechanism: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="demo-1.0")


class ConditionDrugContraindication(Base):
    """A condition–drug contraindication rule row.

    Covers renal, hepatic, hyperkalemia, G6PD and respiratory categories.
    ``condition_code`` is either a real ICD-10 code from the ``conditions``
    table (e.g. ``J45`` for asthma) or one of the three reserved
    pseudo-codes: ``RENAL-IMPAIRED``, ``HEPATIC-IMPAIRED``,
    ``G6PD-DEFICIENT``.

    Attributes:
        id: Surrogate integer primary key.
        condition_code: ICD-10 code or reserved pseudo-code.
        drug_name: Canonical drug name.
        finding_type: One of ``RENAL_CONTRAINDICATION``,
            ``HEPATIC_CONTRAINDICATION``, ``HYPERKALEMIA_RISK``,
            ``G6PD_CONTRAINDICATION``, ``RESPIRATORY_CONTRAINDICATION``.
        severity: ``INFO | LOW | MODERATE | HIGH | CONTRAINDICATED``.
        mechanism: Clinical mechanism text.
        recommendation: Prescriber guidance.
        source: Data provenance tag.
        version: Rule version string.
    """

    __tablename__ = "condition_drug_contraindications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    condition_code: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    drug_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    finding_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    mechanism: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="demo-1.0")


class AllergyCrossReactivity(Base):
    """Cross-reactivity rule linking an allergen to a cross-reactive drug.

    Attributes:
        id: Surrogate integer primary key.
        allergen: The recorded allergen (e.g. ``penicillin``).
        cross_reactive_drug: The drug that shares structural/class features
            with the allergen and may trigger a cross-reactive response.
        mechanism: Clinical mechanism of cross-reactivity.
        severity: Expected reaction severity.
        source: Data provenance tag.
        version: Rule version string.
    """

    __tablename__ = "allergy_cross_reactivity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    allergen: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    cross_reactive_drug: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    mechanism: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="demo-1.0")


class ScreeningAudit(Base):
    """Audit log entry for every completed screening request.

    Attributes:
        id: Surrogate integer primary key.
        request_id: UUID-style request identifier injected by middleware.
        patient_id: The patient screened.
        created_at: Timestamp of the screening request.
        ruleset_version: Version of the rule tables applied.
        result_json: Full JSON serialisation of the :class:`ScreeningResponse`.
    """

    __tablename__ = "screening_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    ruleset_version: Mapped[str] = mapped_column(String(20), nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
