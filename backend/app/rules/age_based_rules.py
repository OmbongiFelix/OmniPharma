"""Age-based prescribing caution, in the spirit of Beers-criteria-style
guidance: certain drug classes carry additional caution in older adults
regardless of any recorded condition.

This module has no backing database table by design — it derives age
from `patient.date_of_birth` at evaluation time and compares against a
small, explicit constant table defined in this module. Age is a patient
attribute, not a condition or a drug-catalogue fact, so it does not fit
`condition_drug_contraindications`.

Imports/dependencies: app.schemas only; Python's `datetime` for age
calculation.

Public outputs: `evaluate_age_based_caution()`.
"""

from datetime import date, datetime

from app.schemas.medication import MedicationContext
from app.schemas.patient import PatientContext
from app.schemas.screening import SafetyFinding

# Age threshold in years, matching common Beers-criteria usage.
_AGE_THRESHOLD = 65

# Beers-criteria-style constant table.
# Each entry: (canonical_name_prefix_or_exact, finding_severity, summary_suffix, rationale)
# drug_class_keywords is a set of lowercase substrings matched against canonical_name.
# severity is capped at HIGH (never CONTRAINDICATED) per the spec.
_AGE_CAUTION_TABLE: list[dict] = [
    {
        "drug_class_keywords": {"diazepam", "lorazepam", "alprazolam", "clonazepam",
                                 "nitrazepam", "temazepam", "oxazepam", "midazolam"},
        "severity": "MODERATE",
        "class_label": "benzodiazepine",
        "rationale": (
            "Benzodiazepines increase the risk of cognitive impairment, delirium, "
            "falls, fractures and motor vehicle accidents in older adults. "
            "Beers criteria recommend avoiding benzodiazepines (any type) in adults "
            "≥65 years."
        ),
    },
    {
        "drug_class_keywords": {"amitriptyline", "imipramine", "doxepin", "clomipramine",
                                 "nortriptyline", "trimipramine"},
        "severity": "MODERATE",
        "class_label": "tricyclic antidepressant",
        "rationale": (
            "Tricyclic antidepressants are highly anticholinergic; older adults are at "
            "increased risk of confusion, urinary retention, dry mouth, and orthostatic "
            "hypotension. Beers criteria recommend avoiding TCAs in older adults."
        ),
    },
    {
        "drug_class_keywords": {"chlorphenamine", "promethazine", "diphenhydramine",
                                 "hydroxyzine", "cyproheptadine"},
        "severity": "MODERATE",
        "class_label": "first-generation antihistamine",
        "rationale": (
            "First-generation antihistamines are strongly anticholinergic; risk of "
            "sedation, confusion and falls is markedly higher in older adults. "
            "Prefer second-generation (non-sedating) alternatives."
        ),
    },
    {
        "drug_class_keywords": {"glibenclamide", "glipizide", "glyburide", "chlorpropamide"},
        "severity": "MODERATE",
        "class_label": "long-acting sulfonylurea",
        "rationale": (
            "Long-acting sulfonylureas carry a prolonged hypoglycaemia risk in older "
            "adults with reduced renal clearance. Shorter-acting agents are preferred. "
            "Beers criteria recommend avoiding glibenclamide (glyburide) in older adults."
        ),
    },
    {
        "drug_class_keywords": {"naproxen", "indomethacin", "ketoprofen", "piroxicam",
                                 "meloxicam"},
        "severity": "MODERATE",
        "class_label": "NSAID",
        "rationale": (
            "NSAIDs increase the risk of gastrointestinal bleeding and peptic ulcer "
            "disease in older adults, particularly those with prior GI history or taking "
            "corticosteroids. Beers criteria recommend using with caution or avoiding "
            "if possible."
        ),
    },
]


def _calculate_age(date_of_birth: str) -> int | None:
    """Calculate age in whole years from an ISO-8601 date-of-birth string.

    Args:
        date_of_birth: Date string in ``YYYY-MM-DD`` format.

    Returns:
        Age in whole years, or ``None`` if the date string cannot be parsed.
    """
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age


def evaluate_age_based_caution(
    medications: list[MedicationContext],
    patient: PatientContext,
) -> list[SafetyFinding]:
    """Evaluate medicines against age-based prescribing caution.

    Args:
        medications: Canonicalized medicines being reviewed.
        patient: Must include `date_of_birth`.

    Returns:
        One `SafetyFinding` (type=`AGE_BASED_CAUTION`, severity
        `MODERATE` unless documented otherwise for a specific drug
        class) per medicine that matches an age-caution class for a
        patient at or above the configured age threshold (65, matching
        common Beers-criteria usage). Returns an empty list for patients
        under the threshold.

    Notes:
        This is a caution signal, not a contraindication — it must
        never be assigned severity `CONTRAINDICATED`, since Beers-style
        guidance is "use with caution / consider alternative," not
        "never use."
    """
    age = _calculate_age(patient.date_of_birth)
    if age is None or age < _AGE_THRESHOLD:
        return []

    findings: list[SafetyFinding] = []

    for med in medications:
        med_name = med.canonical_name.lower()
        for entry in _AGE_CAUTION_TABLE:
            if any(keyword in med_name for keyword in entry["drug_class_keywords"]):
                # Never assign CONTRAINDICATED — cap at HIGH per spec.
                severity = entry["severity"]
                if severity.upper() == "CONTRAINDICATED":
                    severity = "HIGH"
                findings.append(
                    SafetyFinding(
                        type="AGE_BASED_CAUTION",
                        severity=severity,
                        medications=[med.canonical_name],
                        rule_id=f"AGE-{entry['class_label'].upper().replace(' ', '-')}-{age}Y",
                        summary=(
                            f"Age-based caution: {med.canonical_name} is a "
                            f"{entry['class_label']} and the patient is {age} years old "
                            f"(threshold: {_AGE_THRESHOLD}+ years)."
                        ),
                        rationale=entry["rationale"],
                    )
                )
                break  # One finding per medication per evaluation pass.

    return findings
