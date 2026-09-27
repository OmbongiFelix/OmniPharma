"""Persistence abstraction so business logic does not depend directly
on SQL statements or the SQLAlchemy session API.

Every rule-table read (interaction rules, pregnancy warnings,
condition-drug contraindications, allergy cross-reactivity) goes
through a repository function here so `app.services.*` and `app.rules.*`
never import `sqlalchemy` directly.

Imports/dependencies: sqlalchemy, app.db.models.

Public outputs: one repository class or function set per model, e.g.
`PatientRepository`, `get_active_interaction_rules()`,
`get_active_pregnancy_warnings()`,
`get_active_condition_contraindications()`,
`get_active_allergy_cross_reactivity()`.
"""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import (
    Allergy,
    AllergyCrossReactivity,
    Condition,
    ConditionDrugContraindication,
    Inventory,
    InteractionRule,
    Medication,
    MedicationHistory,
    Patient,
    PregnancyDrugWarning,
    Prescription,
    ScreeningAudit,
)


# ---------------------------------------------------------------------------
# Patient repository
# ---------------------------------------------------------------------------


class PatientRepository:
    """Persistence operations for :class:`~app.db.models.Patient` records.

    Args:
        db: An active SQLAlchemy session. Injected by callers; never
            opened inside this class.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, patient_id: int) -> Patient | None:
        """Return a single patient by primary key, or ``None`` if not found.

        Args:
            patient_id: Surrogate integer primary key.

        Returns:
            The :class:`Patient` ORM object, or ``None``.
        """
        return self._db.get(Patient, patient_id)

    def list_all(self) -> list[Patient]:
        """Return every patient in insertion order.

        Returns:
            List of all :class:`Patient` rows.
        """
        return self._db.query(Patient).order_by(Patient.id).all()

    def search(self, query: str) -> list[Patient]:
        """Search patients by name or patient code (case-insensitive substring).

        Args:
            query: Substring to search within ``name`` or ``patient_code``.

        Returns:
            Matching :class:`Patient` rows, ordered by id.
        """
        term = f"%{query.lower()}%"
        return (
            self._db.query(Patient)
            .filter(
                or_(
                    Patient.name.ilike(term),
                    Patient.patient_code.ilike(term),
                )
            )
            .order_by(Patient.id)
            .all()
        )

    def get_conditions(self, patient_id: int) -> list[Condition]:
        """Return all condition rows for a given patient.

        Args:
            patient_id: Surrogate integer primary key.

        Returns:
            List of :class:`Condition` rows, all statuses included.
        """
        return (
            self._db.query(Condition)
            .filter(Condition.patient_id == patient_id)
            .all()
        )

    def get_allergies(self, patient_id: int) -> list[Allergy]:
        """Return all allergy rows for a given patient.

        Args:
            patient_id: Surrogate integer primary key.

        Returns:
            List of :class:`Allergy` rows.
        """
        return (
            self._db.query(Allergy)
            .filter(Allergy.patient_id == patient_id)
            .all()
        )

    def get_active_prescriptions(self, patient_id: int) -> list[Prescription]:
        """Return active prescriptions for a given patient.

        Args:
            patient_id: Surrogate integer primary key.

        Returns:
            List of :class:`Prescription` rows with ``status == 'ACTIVE'``.
        """
        return (
            self._db.query(Prescription)
            .filter(
                Prescription.patient_id == patient_id,
                Prescription.status == "ACTIVE",
            )
            .all()
        )

    def get_medication_history(self, patient_id: int) -> list[MedicationHistory]:
        """Return medication history for a given patient.

        Args:
            patient_id: Surrogate integer primary key.

        Returns:
            List of :class:`MedicationHistory` rows ordered by start_date
            descending.
        """
        return (
            self._db.query(MedicationHistory)
            .filter(MedicationHistory.patient_id == patient_id)
            .order_by(MedicationHistory.start_date.desc())
            .all()
        )


# ---------------------------------------------------------------------------
# Medication / catalogue repository
# ---------------------------------------------------------------------------


class MedicationRepository:
    """Persistence operations for :class:`~app.db.models.Medication` records.

    Args:
        db: An active SQLAlchemy session.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, medication_id: int) -> Medication | None:
        """Return a medication by primary key.

        Args:
            medication_id: Surrogate integer primary key.

        Returns:
            :class:`Medication` ORM object or ``None``.
        """
        return self._db.get(Medication, medication_id)

    def search(self, query: str, limit: int = 20) -> list[Medication]:
        """Search the catalogue for medications matching the query string.

        Results are ranked: exact canonical-name match first, then exact
        INN match, then trade-name match, then substring match.

        Args:
            query: Free-text search term.
            limit: Maximum number of results to return.

        Returns:
            Up to ``limit`` :class:`Medication` rows.
        """
        term = f"%{query.lower()}%"
        exact_canonical = (
            self._db.query(Medication)
            .filter(Medication.canonical_name == query.lower())
            .limit(limit)
            .all()
        )
        if len(exact_canonical) >= limit:
            return exact_canonical

        fuzzy = (
            self._db.query(Medication)
            .filter(
                or_(
                    Medication.canonical_name.ilike(term),
                    Medication.inn.ilike(term),
                    Medication.trade_name.ilike(term),
                )
            )
            .order_by(Medication.canonical_name)
            .limit(limit)
            .all()
        )
        # Deduplicate while preserving order.
        seen_ids = {m.id for m in exact_canonical}
        combined = list(exact_canonical)
        for m in fuzzy:
            if m.id not in seen_ids:
                combined.append(m)
                seen_ids.add(m.id)
        return combined[:limit]

    def resolve(self, name: str) -> Medication | None:
        """Try to resolve a free-text name to a canonical medication record.

        Attempts exact canonical-name match, then INN match, then
        trade-name match (all case-insensitive).

        Args:
            name: Drug name as entered by a user or from a request body.

        Returns:
            The best-matching :class:`Medication`, or ``None`` if nothing
            matches above the confidence threshold (no fuzzy match is
            returned silently).
        """
        lower = name.lower().strip()

        # Exact canonical match
        med = (
            self._db.query(Medication)
            .filter(Medication.canonical_name == lower)
            .first()
        )
        if med:
            return med

        # Exact INN match
        med = (
            self._db.query(Medication)
            .filter(Medication.inn == lower)
            .first()
        )
        if med:
            return med

        # Exact trade-name match (case-insensitive)
        med = (
            self._db.query(Medication)
            .filter(Medication.trade_name.ilike(lower))
            .first()
        )
        return med

    def list_by_indication(self, indication: str, limit: int = 30) -> list[Medication]:
        """Return candidate medications for a given clinical indication.

        Currently delegates to substring search across canonical name and
        trade name; a real implementation would join a therapeutic-class
        table.

        Args:
            indication: Free-text clinical indication.
            limit: Maximum results.

        Returns:
            Up to ``limit`` :class:`Medication` rows.
        """
        return self.search(indication, limit=limit)

    def get_inventory(self, medication_id: int) -> list[Inventory]:
        """Return inventory rows for a medication.

        Args:
            medication_id: Surrogate integer primary key.

        Returns:
            List of :class:`Inventory` rows.
        """
        return (
            self._db.query(Inventory)
            .filter(Inventory.medication_id == medication_id)
            .all()
        )

    def list_all(self, limit: int = 200) -> list[Medication]:
        """Return up to ``limit`` medications from the catalogue.

        Args:
            limit: Maximum results.

        Returns:
            List of :class:`Medication` rows ordered by canonical name.
        """
        return (
            self._db.query(Medication)
            .order_by(Medication.canonical_name)
            .limit(limit)
            .all()
        )


# ---------------------------------------------------------------------------
# Rule table readers (stateless functions)
# ---------------------------------------------------------------------------


def get_active_interaction_rules(db: Session) -> list[InteractionRule]:
    """Return all drug-drug interaction rule rows.

    Args:
        db: Active SQLAlchemy session.

    Returns:
        All :class:`InteractionRule` rows ordered by id.
    """
    return db.query(InteractionRule).order_by(InteractionRule.id).all()


def get_active_pregnancy_warnings(db: Session) -> list[PregnancyDrugWarning]:
    """Return all pregnancy drug warning rows.

    Args:
        db: Active SQLAlchemy session.

    Returns:
        All :class:`PregnancyDrugWarning` rows ordered by drug_name.
    """
    return db.query(PregnancyDrugWarning).order_by(PregnancyDrugWarning.drug_name).all()


def get_active_condition_contraindications(
    db: Session,
) -> list[ConditionDrugContraindication]:
    """Return all condition-drug contraindication rule rows.

    Args:
        db: Active SQLAlchemy session.

    Returns:
        All :class:`ConditionDrugContraindication` rows ordered by
        condition_code then drug_name.
    """
    return (
        db.query(ConditionDrugContraindication)
        .order_by(
            ConditionDrugContraindication.condition_code,
            ConditionDrugContraindication.drug_name,
        )
        .all()
    )


def get_active_allergy_cross_reactivity(db: Session) -> list[AllergyCrossReactivity]:
    """Return all allergy cross-reactivity rule rows.

    Args:
        db: Active SQLAlchemy session.

    Returns:
        All :class:`AllergyCrossReactivity` rows ordered by allergen.
    """
    return (
        db.query(AllergyCrossReactivity)
        .order_by(AllergyCrossReactivity.allergen)
        .all()
    )


# ---------------------------------------------------------------------------
# Audit repository
# ---------------------------------------------------------------------------


def save_screening_audit(db: Session, audit: ScreeningAudit) -> None:
    """Persist a screening audit record.

    Args:
        db: Active SQLAlchemy session.
        audit: Populated :class:`ScreeningAudit` instance to persist.

    Returns:
        None
    """
    db.add(audit)
    db.commit()
