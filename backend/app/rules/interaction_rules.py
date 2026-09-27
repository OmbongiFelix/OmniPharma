"""Deterministic drug-drug interaction rules for the hackathon's known
scenarios.

Pure functions only: no I/O, no database session, no randomness. Reads
already-loaded `interaction_rules` table rows passed in by the caller.

Imports/dependencies: app.schemas only.

Public outputs: `evaluate_drug_pairs()`.
"""

from itertools import combinations

from app.schemas.medication import InteractionRuleRow, MedicationContext
from app.schemas.screening import SafetyFinding

_SEVERITY_ORDER = ["INFO", "LOW", "MODERATE", "HIGH", "CONTRAINDICATED"]


def _severity_rank(s: str) -> int:
    """Return an integer rank for a severity string, for ordering.

    Args:
        s: Severity string.

    Returns:
        Integer rank; higher means more severe.
    """
    try:
        return _SEVERITY_ORDER.index(s.upper())
    except ValueError:
        return -1


def evaluate_drug_pairs(
    medications: list[MedicationContext],
    rules: list[InteractionRuleRow],
) -> list[SafetyFinding]:
    """Evaluate every unordered pair of medications against known rules.

    Args:
        medications: Canonicalized medicines being reviewed.
        rules: All currently active rows from `interaction_rules`.

    Returns:
        One `SafetyFinding` (type=`DRUG_DRUG_INTERACTION`) per matching
        pair, in descending severity order. A rule matches a pair
        regardless of which medicine is `drug_a` vs `drug_b` in the row.

    Notes:
        Pure function: identical inputs always produce identical
        output, and no OS/network/DB call ever happens here.
    """
    if len(medications) < 2:
        return []

    # Build a lookup from frozenset of (drug_a, drug_b) -> list of rules.
    rule_map: dict[frozenset, list[InteractionRuleRow]] = {}
    for rule in rules:
        key = frozenset([rule.drug_a.lower(), rule.drug_b.lower()])
        rule_map.setdefault(key, []).append(rule)

    findings: list[SafetyFinding] = []

    for med_a, med_b in combinations(medications, 2):
        key = frozenset([med_a.canonical_name.lower(), med_b.canonical_name.lower()])
        matched_rules = rule_map.get(key, [])
        for rule in matched_rules:
            findings.append(
                SafetyFinding(
                    type="DRUG_DRUG_INTERACTION",
                    severity=rule.severity,
                    medications=[med_a.canonical_name, med_b.canonical_name],
                    rule_id=f"DDI-{rule.id}",
                    summary=(
                        f"Potential interaction between {med_a.canonical_name} "
                        f"and {med_b.canonical_name}."
                    ),
                    rationale=rule.mechanism,
                )
            )

    # Sort by descending severity.
    findings.sort(key=lambda f: _severity_rank(f.severity), reverse=True)
    return findings
