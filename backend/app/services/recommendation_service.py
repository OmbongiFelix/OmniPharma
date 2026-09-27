"""Produces and safety-filters candidate alternative medicines.

Imports/dependencies: app.services.drug_catalog_service,
app.services.interaction_service, app.db.repositories.

Public outputs: `recommend_alternatives()`.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import DrugResolutionError
from app.core.config import get_settings
from app.db.repositories import MedicationRepository
from app.schemas.medication import MedicationContext
from app.schemas.patient import PatientContext
from app.schemas.screening import Recommendation, SafetyFinding
from app.services import interaction_service

_SEVERITY_ORDER = ["INFO", "LOW", "MODERATE", "HIGH", "CONTRAINDICATED"]


def _severity_rank(s: str) -> int:
    try:
        return _SEVERITY_ORDER.index(s.upper())
    except ValueError:
        return -1


def _exclusion_reason(findings: list[SafetyFinding]) -> str | None:
    """Return a machine-readable exclusion reason from a list of findings.

    Args:
        findings: Safety findings produced by screening a candidate drug.

    Returns:
        A short string describing the highest-severity finding, or
        ``None`` if there are no disqualifying findings.
    """
    if not findings:
        return None
    worst = max(findings, key=lambda f: _severity_rank(f.severity))
    return f"{worst.type}:{worst.severity} — {worst.summary}"


def recommend_alternatives(
    patient: PatientContext,
    target_medication: MedicationContext,
    indication: str | None,
    db: Session,
) -> list[Recommendation]:
    """Generate and safety-filter alternative medicines.

    Candidates come from the configured Kenya drug catalogue/inventory
    and are screened against the same patient-specific rules as the
    target drug (see `screen_medications`). The function does not
    prescribe or automatically substitute medication; every returned
    item is a candidate for pharmacist review.

    Args:
        patient: The patient the alternative is being considered for.
        target_medication: The medicine being replaced or reconsidered.
        indication: Optional free-text clinical indication used to
            narrow catalogue candidates before filtering; does not
            affect the safety-filtering step.
        db: Active SQLAlchemy session.

    Returns:
        A list of `Recommendation` objects. Each included candidate
        carries `included_reason`. Each excluded candidate is *also*
        returned, with `excluded=True` and `excluded_reason` set to the
        specific rule/finding that removed it — callers must not drop
        excluded candidates silently, so a pharmacist can see why an
        option isn't offered.

    Raises:
        DrugResolutionError: If `target_medication` cannot be resolved
            to a canonical catalogue entry.

    Notes:
        Candidates unavailable in `inventory` are excluded with reason
        `"OUT_OF_STOCK"` only when inventory-aware mode is enabled in
        `Settings`; otherwise stock status is informational only and
        does not exclude a candidate.
    """
    settings = get_settings()
    repo = MedicationRepository(db)

    # Retrieve candidates from catalogue.
    query_term = indication or target_medication.canonical_name
    candidate_meds = repo.list_by_indication(query_term, limit=30)

    recommendations: list[Recommendation] = []

    for med in candidate_meds:
        # Skip the target drug itself.
        if med.id == target_medication.id or med.canonical_name == target_medication.canonical_name:
            continue

        candidate = MedicationContext(
            id=med.id,
            canonical_name=med.canonical_name,
            inn=med.inn,
            trade_name=med.trade_name,
            dosage_form=med.dosage_form,
            strength=med.strength,
            source=med.source,
        )

        # Screen the candidate against the patient's safety constraints.
        findings = interaction_service.screen_medications([candidate], patient, db)

        # Determine inventory status if applicable.
        inventory = repo.get_inventory(med.id)
        total_qty = sum(i.quantity for i in inventory)
        availability = "IN_STOCK" if total_qty > 0 else "OUT_OF_STOCK"

        disqualifying_findings = [
            f for f in findings if _severity_rank(f.severity) >= _severity_rank("HIGH")
        ]

        # Inventory exclusion in inventory-aware mode.
        if settings.inventory_aware and total_qty == 0:
            recommendations.append(
                Recommendation(
                    drug_name=candidate.canonical_name,
                    excluded=True,
                    excluded_reason="OUT_OF_STOCK",
                    availability=availability,
                )
            )
            continue

        if disqualifying_findings:
            recommendations.append(
                Recommendation(
                    drug_name=candidate.canonical_name,
                    excluded=True,
                    excluded_reason=_exclusion_reason(disqualifying_findings),
                    availability=availability,
                )
            )
        else:
            recommendations.append(
                Recommendation(
                    drug_name=candidate.canonical_name,
                    excluded=False,
                    included_reason=(
                        f"No high-severity safety findings for this patient. "
                        f"Availability: {availability}."
                    ),
                    availability=availability,
                )
            )

    return recommendations
