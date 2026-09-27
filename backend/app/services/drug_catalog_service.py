"""Searches normalized PPB registered products and maps trade/INN names
to canonical medication records.

Imports/dependencies: SQLAlchemy, app.db.repositories.

Public outputs: `search_drugs()`, `resolve_drug()`.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import DrugResolutionError
from app.db.repositories import MedicationRepository
from app.schemas.medication import DrugDetail, DrugSummary, MedicationContext


def resolve_drug(name: str, db: Session) -> MedicationContext:
    """Resolve a free-text drug name to a canonical medication record.

    Args:
        name: Trade name, INN, or common name as entered by a user or
            supplied in a screening request.
        db: Active SQLAlchemy session.

    Returns:
        The canonical `MedicationContext` (canonical_name, inn,
        trade_name, dosage_form, source).

    Raises:
        DrugResolutionError: If `name` does not match any catalogue
            entry after normalization (case-folding, whitespace
            collapse, common trade/INN alias lookup). The caller must
            surface this as an `UNRESOLVED_DRUG` finding rather than
            skipping the medicine.

    Notes:
        Never returns a best-guess partial match silently; a fuzzy
        match below the configured confidence threshold is treated as
        unresolved, not resolved.
    """
    normalised = " ".join(name.strip().lower().split())
    if not normalised:
        raise DrugResolutionError(f"Empty drug name cannot be resolved.")

    repo = MedicationRepository(db)
    med = repo.resolve(normalised)

    if med is None:
        raise DrugResolutionError(
            f"Drug '{name}' could not be resolved to a catalogue entry. "
            "Check the spelling or use the search endpoint to find the canonical name."
        )

    return MedicationContext(
        id=med.id,
        canonical_name=med.canonical_name,
        inn=med.inn,
        trade_name=med.trade_name,
        dosage_form=med.dosage_form,
        strength=med.strength,
        source=med.source,
    )


def search_drugs(query: str, db: Session, limit: int = 20) -> list[DrugSummary]:
    """Search the local catalogue for autocomplete/lookup use.

    Args:
        query: Free-text search term.
        db: Active SQLAlchemy session.
        limit: Maximum number of results (default 20).

    Returns:
        Up to a configured max number of `DrugSummary` matches ranked by
        relevance (exact trade-name match first, then INN match, then
        substring match).
    """
    repo = MedicationRepository(db)
    meds = repo.search(query, limit=limit)
    return [
        DrugSummary(
            id=m.id,
            canonical_name=m.canonical_name,
            inn=m.inn,
            trade_name=m.trade_name,
            dosage_form=m.dosage_form,
            strength=m.strength,
            source=m.source,
        )
        for m in meds
    ]


def get_drug_detail(drug_id: int, db: Session) -> DrugDetail:
    """Return full drug detail including stock status.

    Args:
        drug_id: Database primary key of the medication.
        db: Active SQLAlchemy session.

    Returns:
        :class:`~app.schemas.medication.DrugDetail` with inventory
        information appended.

    Raises:
        DrugResolutionError: If no medication with ``drug_id`` exists.
    """
    repo = MedicationRepository(db)
    med = repo.get_by_id(drug_id)
    if med is None:
        raise DrugResolutionError(f"Medication with id={drug_id} not found.")

    inventory = repo.get_inventory(drug_id)
    total_qty = sum(i.quantity for i in inventory)
    return DrugDetail(
        id=med.id,
        canonical_name=med.canonical_name,
        inn=med.inn,
        trade_name=med.trade_name,
        dosage_form=med.dosage_form,
        strength=med.strength,
        source=med.source,
        in_stock=total_qty > 0,
        total_quantity=total_qty,
    )
