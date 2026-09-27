"""Prompt templates for the PharmacistAgent LLM calls.

Keeps all prompt strings centralized so they can be reviewed and updated
without touching the PharmacistAgent business logic.  Every prompt in
this module explicitly instructs the model to restate only what is
present in the structured findings and never to add a new interaction,
drug, or severity level.

Imports/dependencies: none (string constants only).

Public outputs: `build_explanation_prompt()`.
"""


_SYSTEM_PROMPT = (
    "You are a clinical pharmacist assistant providing explanations of "
    "pre-computed, deterministic medication safety findings to a reviewing pharmacist. "
    "Your role is ONLY to summarise and explain the provided findings — you must NOT "
    "invent new interactions, change any severity level, add any drug not listed in the "
    "findings, or suggest a specific prescription or dose adjustment. "
    "If a finding carries severity CONTRAINDICATED or HIGH, clearly emphasise that "
    "pharmacist review is required before dispensing."
)


def build_explanation_prompt(findings_json: str, patient_name: str) -> tuple[str, str]:
    """Build the system and user prompt for a pharmacist explanation call.

    Args:
        findings_json: JSON-serialised list of ``SafetyFinding`` objects
            already produced by the deterministic rule engine.
        patient_name: Patient's display name, used only to personalise
            the explanation — no patient identifiers should appear in
            LLM logs.

    Returns:
        A ``(system_prompt, user_prompt)`` tuple suitable for passing
        directly to a chat-completion API call.  Both strings are
        already formatted; the caller should not modify them.
    """
    user_prompt = (
        f"The following safety findings were identified for a patient named {patient_name}. "
        "Please write a concise, professional explanation (3–6 sentences) that a reviewing "
        "pharmacist can read quickly.  Summarise each finding in plain language, note the "
        "severity, and state what action the pharmacist should consider.  "
        "Do not add any finding, drug, or severity that is not already present in the list "
        "below.  Do not suggest a specific dose.\n\n"
        f"Findings (JSON):\n{findings_json}"
    )
    return _SYSTEM_PROMPT, user_prompt
