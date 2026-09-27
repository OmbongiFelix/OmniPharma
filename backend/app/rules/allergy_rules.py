"""Checks medicine ingredients/classes against recorded allergies,
including cross-reactive drug classes.

Imports/dependencies: app.schemas only.

Public outputs: `evaluate_allergies()`.
"""

from app.schemas.medication import AllergyCrossReactivityRow, MedicationContext
from app.schemas.patient import PatientContext
from app.schemas.screening import SafetyFinding

_SEVERITY_ORDER = ["INFO", "LOW", "MODERATE", "HIGH", "CONTRAINDICATED"]


def _severity_rank(s: str) -> int:
    """Return an integer rank for a severity string.

    Args:
        s: Severity string.

    Returns:
        Integer rank; higher means more severe.
    """
    try:
        return _SEVERITY_ORDER.index(s.upper())
    except ValueError:
        return -1


def evaluate_allergies(
    medications: list[MedicationContext],
    patient: PatientContext,
    cross_reactivity_rules: list[AllergyCrossReactivityRow],
) -> list[SafetyFinding]:
    """Evaluate medicines against a patient's recorded allergies.

    Args:
        medications: Canonicalized medicines being reviewed.
        patient: Must include `allergies` (allergen, reaction, severity).
        cross_reactivity_rules: All currently active rows from
            `allergy_cross_reactivity` (e.g. penicillin -> amoxicillin).

    Returns:
        A `SafetyFinding` with `type="ALLERGY"` for a direct allergen
        match, or `type="ALLERGY_CROSS_REACTIVITY"` when the medicine is
        not the recorded allergen itself but matches a cross-reactive
        drug for that allergen class.

    Notes:
        A patient allergy row with `allergen="none"` (as used in the
        synthetic dataset to represent "no known allergies") is treated
        as no allergy and never matched against any rule.
    """
    # Collect non-trivial allergens.
    allergens: set[str] = set()
    for allergy in patient.allergies:
        if allergy.allergen.lower() not in ("none", "", "nil", "nkda"):
            allergens.add(allergy.allergen.lower())

    if not allergens:
        return []

    # Build cross-reactivity lookup: allergen -> list of rows.
    cross_map: dict[str, list[AllergyCrossReactivityRow]] = {}
    for rule in cross_reactivity_rules:
        cross_map.setdefault(rule.allergen.lower(), []).append(rule)

    findings: list[SafetyFinding] = []

    for med in medications:
        med_name = med.canonical_name.lower()
        trade_lower = (med.trade_name or "").lower()

        for allergen in allergens:
            # Direct allergen match — the medication IS the allergen.
            if med_name == allergen or (trade_lower and trade_lower == allergen):
                findings.append(
                    SafetyFinding(
                        type="ALLERGY",
                        severity="CONTRAINDICATED",
                        medications=[med.canonical_name],
                        rule_id=f"ALLERGY-DIRECT-{allergen.upper()}",
                        summary=(
                            f"Patient has a recorded allergy to {allergen}; "
                            f"{med.canonical_name} is contraindicated."
                        ),
                        rationale=(
                            f"Direct allergen match: patient allergy record lists "
                            f"'{allergen}' and the prescribed drug is '{med.canonical_name}'."
                        ),
                    )
                )
                continue  # Skip cross-reactivity check for same drug.

            # Cross-reactivity check: look up what drugs are cross-reactive
            # with this allergen and see if the current med is among them.
            for rule in cross_map.get(allergen, []):
                if rule.cross_reactive_drug.lower() == med_name:
                    findings.append(
                        SafetyFinding(
                            type="ALLERGY_CROSS_REACTIVITY",
                            severity=rule.severity,
                            medications=[med.canonical_name],
                            rule_id=f"ALLERGY-CROSS-{rule.id}",
                            summary=(
                                f"Cross-reactivity risk: patient is allergic to {allergen}; "
                                f"{med.canonical_name} may trigger a cross-reactive response."
                            ),
                            rationale=rule.mechanism,
                        )
                    )

    # Sort by descending severity.
    findings.sort(key=lambda f: _severity_rank(f.severity), reverse=True)
    return findings
