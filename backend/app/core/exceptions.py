"""Domain exceptions raised by services and rule modules.

Mapped to HTTP status codes only inside `app.api.*` handlers — services
and rules must never import fastapi or construct an HTTPException
themselves, per the import/export rules in Section 5.

Imports/dependencies: none (stdlib only).

Public outputs: `PatientNotFoundError`, `DrugResolutionError`,
`RuleConfigurationError`.
"""


class PatientNotFoundError(Exception):
    """Raised when a requested patient_id does not exist."""


class DrugResolutionError(Exception):
    """Raised when a drug name cannot be resolved to a canonical record."""


class RuleConfigurationError(Exception):
    """Raised when a required rule table is missing, empty, or malformed
    at evaluation time."""
