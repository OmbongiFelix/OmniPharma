"""Duplicate therapy detection for OmniPharma screening.

Identifies cases where two or more medicines in the screened list are
likely to belong to the same pharmacological class, increasing toxicity
risk without additional therapeutic benefit.

Pure functions only: no I/O, no database session, no randomness.

Imports/dependencies: app.schemas only.

Public outputs: `evaluate_duplicate_therapy()`.
"""

from app.schemas.medication import MedicationContext
from app.schemas.screening import SafetyFinding

# Simple class-grouping constant table.
# Each entry maps a class label to a set of canonical-name substrings.
_DRUG_CLASSES: list[dict] = [
    {
        "class": "ACE inhibitor",
        "keywords": {"lisinopril", "enalapril", "ramipril", "perindopril",
                      "captopril", "fosinopril", "quinapril", "trandolapril"},
    },
    {
        "class": "NSAID",
        "keywords": {"ibuprofen", "naproxen", "diclofenac", "indomethacin",
                      "ketoprofen", "piroxicam", "meloxicam", "celecoxib"},
    },
    {
        "class": "statin",
        "keywords": {"atorvastatin", "simvastatin", "rosuvastatin", "pravastatin",
                      "lovastatin", "fluvastatin", "pitavastatin"},
    },
    {
        "class": "benzodiazepine",
        "keywords": {"diazepam", "lorazepam", "alprazolam", "clonazepam",
                      "nitrazepam", "temazepam", "oxazepam", "midazolam"},
    },
    {
        "class": "beta-blocker",
        "keywords": {"metoprolol", "atenolol", "propranolol", "bisoprolol",
                      "carvedilol", "labetalol", "nebivolol"},
    },
    {
        "class": "sulfonylurea",
        "keywords": {"glibenclamide", "glipizide", "gliclazide", "glimepiride",
                      "tolbutamide", "chlorpropamide"},
    },
    {
        "class": "proton pump inhibitor",
        "keywords": {"omeprazole", "lansoprazole", "pantoprazole", "rabeprazole",
                      "esomeprazole"},
    },
]


def _get_class(med: MedicationContext) -> str | None:
    """Return the drug class label for a medication, or None if unclassified.

    Args:
        med: Canonical medication context.

    Returns:
        Class label string or ``None``.
    """
    name_lower = med.canonical_name.lower()
    for entry in _DRUG_CLASSES:
        if any(kw in name_lower for kw in entry["keywords"]):
            return entry["class"]
    return None


def evaluate_duplicate_therapy(
    medications: list[MedicationContext],
) -> list[SafetyFinding]:
    """Detect duplicate therapy: two or more drugs from the same class.

    Args:
        medications: Canonicalized medicines being reviewed.

    Returns:
        One `SafetyFinding` (type=`DUPLICATE_THERAPY`, severity=`MODERATE`)
        per drug class that has more than one representative in the
        reviewed list. The finding lists all class members.

    Notes:
        Pure function: identical inputs always produce identical output.
    """
    class_members: dict[str, list[str]] = {}
    for med in medications:
        cls = _get_class(med)
        if cls:
            class_members.setdefault(cls, []).append(med.canonical_name)

    findings: list[SafetyFinding] = []
    for cls, members in class_members.items():
        if len(members) > 1:
            findings.append(
                SafetyFinding(
                    type="DUPLICATE_THERAPY",
                    severity="MODERATE",
                    medications=members,
                    rule_id=f"DUP-{cls.upper().replace(' ', '-')}",
                    summary=(
                        f"Duplicate therapy detected: multiple {cls}s prescribed "
                        f"simultaneously ({', '.join(members)})."
                    ),
                    rationale=(
                        f"Using more than one drug from the {cls} class at the same "
                        "time typically increases toxicity risk without additional "
                        "therapeutic benefit. Review and rationalise to a single agent."
                    ),
                )
            )

    return findings
