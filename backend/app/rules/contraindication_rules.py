"""Deterministic condition–drug contraindication rules.

Covers renal, hepatic, hyperkalemia, G6PD and respiratory
contraindications — every category backed by the
`condition_drug_contraindications` table (see
`04_FastAPI_Backend_Design.md` Section 5). Pregnancy has its own
sibling module (`pregnancy_rules.py`) because pregnancy status lives on
the patient row rather than the `conditions` table, but the two modules
share an identical function contract.

Imports/dependencies: app.schemas only.

Public outputs: `evaluate_contraindications()`.
"""

from app.schemas.medication import ConditionContraindicationRow, MedicationContext
from app.schemas.patient import PatientContext
from app.schemas.screening import SafetyFinding
from app.core.exceptions import RuleConfigurationError

_SEVERITY_ORDER = ["INFO", "LOW", "MODERATE", "HIGH", "CONTRAINDICATED"]

# Reserved pseudo-codes used in condition_drug_contraindications that map
# to patient-row status fields rather than diagnosis rows.
_RENAL_PSEUDO = "RENAL-IMPAIRED"
_HEPATIC_PSEUDO = "HEPATIC-IMPAIRED"
_G6PD_PSEUDO = "G6PD-DEFICIENT"

# Status values that count as impaired for the renal/hepatic pseudo-codes.
_IMPAIRED_STATUSES = {"MILD_IMPAIRMENT", "MODERATE_IMPAIRMENT", "SEVERE_IMPAIRMENT"}


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


def _patient_matches_condition_code(code: str, patient: PatientContext) -> bool:
    """Return True if the given condition_code applies to this patient.

    Handles both real ICD-10 codes (matched against the patient's
    conditions rows) and the three reserved pseudo-codes derived from
    patient-row status fields.

    Args:
        code: ``condition_code`` value from a contraindication rule row.
        patient: The patient context to evaluate against.

    Returns:
        ``True`` if the patient matches this condition code.
    """
    code_upper = code.upper()

    if code_upper == _RENAL_PSEUDO:
        return patient.renal_status.upper() in _IMPAIRED_STATUSES

    if code_upper == _HEPATIC_PSEUDO:
        return patient.hepatic_status.upper() in _IMPAIRED_STATUSES

    if code_upper == _G6PD_PSEUDO:
        return patient.g6pd_status.upper() == "DEFICIENT"

    # Real ICD-10 / other condition code: match against patient's conditions.
    return any(c.condition_code.upper() == code_upper for c in patient.conditions)


def evaluate_contraindications(
    medications: list[MedicationContext],
    patient: PatientContext,
    rules: list[ConditionContraindicationRow],
) -> list[SafetyFinding]:
    """Evaluate medicines against the patient's active conditions.

    Args:
        medications: Canonicalized medicines being reviewed.
        patient: Must include `conditions` (active only) and
            `renal_status`/`hepatic_status`/`g6pd_status`.
        rules: All currently active rows from
            `condition_drug_contraindications`.

    Returns:
        One `SafetyFinding` per matching (condition, drug) pair. The
        finding's `type` is taken from the matched rule's
        `finding_type` column (`RENAL_CONTRAINDICATION`,
        `HEPATIC_CONTRAINDICATION`, `HYPERKALEMIA_RISK`,
        `G6PD_CONTRAINDICATION`, or `RESPIRATORY_CONTRAINDICATION`), so
        the same evaluator serves all five categories.

    Raises:
        RuleConfigurationError: If `rules` is empty when the caller
            expected an active ruleset to be loaded.

    Notes:
        A patient with `renal_status="UNKNOWN"` does not trigger a
        renal-category rule that requires `MODERATE_IMPAIRMENT` or
        worse — it instead surfaces as a data-gap warning upstream in
        `screen_medications`. This function only matches *recorded*
        status values.

        `condition_drug_contraindications.condition_code` matches
        against two different sources depending on its value: a real
        diagnosis code present in the patient's `conditions` rows (e.g.
        `J45` for asthma, feeding a `RESPIRATORY_CONTRAINDICATION`), or
        one of three reserved status pseudo-codes —
        `RENAL-IMPAIRED`, `HEPATIC-IMPAIRED`, `G6PD-DEFICIENT` — which
        this function derives directly from
        `patient.renal_status`/`hepatic_status`/`g6pd_status` rather
        than from a `conditions` row. `RENAL-IMPAIRED` and
        `HEPATIC-IMPAIRED` match `MILD_IMPAIRMENT`,
        `MODERATE_IMPAIRMENT` or `SEVERE_IMPAIRMENT`; `G6PD-DEFICIENT`
        matches `DEFICIENT` only. This keeps G6PD/renal/hepatic
        contraindications data-driven without requiring a duplicate
        row in `conditions` for something already captured on the
        patient record itself.
    """
    if not rules:
        raise RuleConfigurationError(
            "condition_drug_contraindications rule table is empty; "
            "cannot evaluate contraindications."
        )

    # Build lookup: drug_name -> list of rules (for O(n) medication scan).
    drug_rule_map: dict[str, list[ConditionContraindicationRow]] = {}
    for rule in rules:
        drug_rule_map.setdefault(rule.drug_name.lower(), []).append(rule)

    findings: list[SafetyFinding] = []

    for med in medications:
        med_name = med.canonical_name.lower()
        candidate_rules = drug_rule_map.get(med_name, [])

        for rule in candidate_rules:
            if _patient_matches_condition_code(rule.condition_code, patient):
                findings.append(
                    SafetyFinding(
                        type=rule.finding_type,
                        severity=rule.severity,
                        medications=[med.canonical_name],
                        rule_id=f"COND-{rule.id}",
                        summary=(
                            f"{rule.finding_type.replace('_', ' ').title()}: "
                            f"{med.canonical_name} flagged for condition code "
                            f"'{rule.condition_code}'."
                        ),
                        rationale=rule.mechanism,
                    )
                )

    findings.sort(key=lambda f: _severity_rank(f.severity), reverse=True)
    return findings
