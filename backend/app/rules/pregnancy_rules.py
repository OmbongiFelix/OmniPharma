"""Checks pregnancy status against configured medicine warnings.

Sibling module to `contraindication_rules.py`; kept separate because
pregnancy status is a patient-row field (`patients.pregnancy_status`),
not a `conditions` table row, and because pregnancy warnings can carry
trimester scope, which condition-drug contraindications do not.

Imports/dependencies: app.schemas only.

Public outputs: `evaluate_pregnancy()`.
"""

from app.schemas.medication import MedicationContext, PregnancyWarningRow
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


def evaluate_pregnancy(
    medications: list[MedicationContext],
    patient: PatientContext,
    rules: list[PregnancyWarningRow],
) -> list[SafetyFinding]:
    """Evaluate medicines against pregnancy-specific warnings.

    Args:
        medications: Canonicalized medicines being reviewed.
        patient: Must include `pregnancy_status`.
        rules: All currently active rows from `pregnancy_drug_warnings`.

    Returns:
        An empty list immediately if `patient.pregnancy_status` is not
        `"PREGNANT"` — this function performs no work for
        `NOT_PREGNANT`, `NOT_APPLICABLE`, or unset values. Otherwise,
        one `SafetyFinding` (type=`PREGNANCY`) per matching drug, at the
        rule's configured severity.

    Notes:
        `trimester_scope="ALL"` matches regardless of gestational week;
        the synthetic dataset does not currently track gestational week,
        so `FIRST`/`SECOND`/`THIRD`-scoped rules are matched
        conservatively (treated as matching) until gestational week is
        added to the patient model — this is a documented limitation,
        not a silent gap.
    """
    if (patient.pregnancy_status or "").upper() != "PREGNANT":
        return []

    # Build lookup: drug_name -> list of rules.
    rule_map: dict[str, list[PregnancyWarningRow]] = {}
    for rule in rules:
        rule_map.setdefault(rule.drug_name.lower(), []).append(rule)

    findings: list[SafetyFinding] = []

    for med in medications:
        med_name = med.canonical_name.lower()
        matched = rule_map.get(med_name, [])
        for rule in matched:
            # trimester_scope: ALL always matches; FIRST/SECOND/THIRD are
            # conservatively treated as matching because gestational week
            # is not tracked in the current data model.
            findings.append(
                SafetyFinding(
                    type="PREGNANCY",
                    severity=rule.severity,
                    medications=[med.canonical_name],
                    rule_id=f"PREG-{rule.id}",
                    summary=(
                        f"{med.canonical_name} has a pregnancy warning "
                        f"(trimester scope: {rule.trimester_scope})."
                    ),
                    rationale=rule.mechanism,
                )
            )

    findings.sort(key=lambda f: _severity_rank(f.severity), reverse=True)
    return findings
