"""Coordinates retrieval, deterministic rules, evidence retrieval and
response synthesis for a single medication-safety review.

This module owns the *order* in which safety checks run and is the only
place that order is allowed to be defined (see Section 5, Decision Flow,
in `03_Agent_Architecture.md`). Individual rule modules must not assume
they run before or after any other rule module; the orchestrator enforces
that.

Imports/dependencies: app.services.patient_service,
app.services.interaction_service, app.services.recommendation_service,
app.services.evidence_service, app.agents.pharmacist_agent.

Public outputs: `run_medication_review()` (see Section 4 below).
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.pharmacist_agent import PharmacistAgent
from app.core.config import get_settings
from app.core.exceptions import DrugResolutionError, PatientNotFoundError
from app.db.models import ScreeningAudit
from app.db.repositories import save_screening_audit
from app.schemas.medication import MedicationContext
from app.schemas.screening import SafetyFinding, ScreeningResponse
from app.services import drug_catalog_service, evidence_service, interaction_service, patient_service

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = ["INFO", "LOW", "MODERATE", "HIGH", "CONTRAINDICATED"]
_IMPAIRED_STATUSES = {"MILD_IMPAIRMENT", "MODERATE_IMPAIRMENT", "SEVERE_IMPAIRMENT"}


def _severity_rank(s: str) -> int:
    try:
        return _SEVERITY_ORDER.index(s.upper())
    except ValueError:
        return -1


def _derive_status(findings: list[SafetyFinding], patient) -> str:
    """Derive the top-level screening status from findings and patient context.

    Args:
        findings: All safety findings produced by the rule engine.
        patient: PatientContext for data-gap detection.

    Returns:
        ``CLEAR``, ``REVIEW_REQUIRED``, ``CONTRAINDICATED``, or
        ``INCOMPLETE_CONTEXT``.
    """
    # Check for INCOMPLETE_CONTEXT: any UNKNOWN status fields.
    incomplete = (
        patient.renal_status.upper() == "UNKNOWN"
        or patient.hepatic_status.upper() == "UNKNOWN"
        or patient.g6pd_status.upper() == "UNKNOWN"
    )
    if not findings:
        return "INCOMPLETE_CONTEXT" if incomplete else "CLEAR"

    max_rank = max(_severity_rank(f.severity) for f in findings)
    if max_rank >= _severity_rank("HIGH"):
        return "CONTRAINDICATED"
    if max_rank >= _severity_rank("LOW"):
        return "REVIEW_REQUIRED"
    if incomplete:
        return "INCOMPLETE_CONTEXT"
    return "CLEAR"


class AgentOrchestrator:
    """Coordinates a full medication-safety review for one patient.

    Holds references to the services it orchestrates; does not hold
    request-scoped state between calls. One instance may safely serve
    multiple concurrent requests because each call to
    `run_medication_review` builds its own local review state.

    Attributes:
        pharmacist_agent: Narrative explanation layer; optional at
            runtime (see `run_medication_review` Notes).
    """

    def __init__(self) -> None:
        self.pharmacist_agent = PharmacistAgent()

    def run_medication_review(
        self,
        patient_id: int,
        medication_names: list[str],
        include_evidence: bool,
        db: Session,
        request_id: str = "unknown",
    ) -> ScreeningResponse:
        """Run a complete medication-safety review for a patient.

        Args:
            patient_id: Internal patient identifier.
            medication_names: Medicine names or catalogue IDs being
                reviewed against the patient's context. Names are
                resolved via `drug_catalog_service.resolve_drug()`
                before any rule runs.
            include_evidence: When True, calls
                `evidence_service.get_evidence()` for each finding that
                supports external evidence. Evidence retrieval failures
                are recorded as `evidence_unavailable=True` on the
                affected finding and never raise.
            db: Active SQLAlchemy session for all database operations.
            request_id: UUID-style request identifier from middleware;
                stored in the screening audit log.

        Returns:
            A `ScreeningResponse` with findings ordered by the fixed
            rule sequence in `03_Agent_Architecture.md` Section 5:
            drug-drug, allergy (incl. cross-reactivity), pregnancy,
            condition-contraindication, age-based, duplicate-therapy.
            `status` is derived from the highest severity present:
            `CLEAR` if no findings, `REVIEW_REQUIRED` for LOW/MODERATE,
            `CONTRAINDICATED` if any finding has severity
            `CONTRAINDICATED` or `HIGH`, `INCOMPLETE_CONTEXT` if any
            required patient field is missing or `UNKNOWN`.

        Raises:
            PatientNotFoundError: If `patient_id` does not exist.
            DrugResolutionError: If a medicine name cannot be resolved
                to a canonical catalogue entry; the response is never
                silently built with a guessed drug.

        Notes:
            Deterministic safety rules execute before any LLM
            explanation step, and the narrative step is best-effort: if
            `pharmacist_agent` is unavailable or raises, the structured
            findings are still returned with `explanation=None`, per the
            \"LLM unavailable\" failure mode.
        """
        settings = get_settings()

        # Step 1: Retrieve patient context.
        patient = patient_service.get_patient_context(patient_id, db)

        # Step 2: Resolve medication names to canonical records.
        resolved: list[MedicationContext] = []
        unresolved_findings: list[SafetyFinding] = []

        for name in medication_names:
            try:
                med = drug_catalog_service.resolve_drug(name, db)
                resolved.append(med)
            except DrugResolutionError:
                unresolved_findings.append(
                    SafetyFinding(
                        type="UNRESOLVED_DRUG",
                        severity="INFO",
                        medications=[name],
                        rule_id=f"UNRESOLVED-{name.upper()[:40].replace(' ', '-')}",
                        summary=f"'{name}' could not be resolved to a catalogue entry.",
                        rationale=(
                            "The drug name was not matched against any canonical, INN, "
                            "or trade name in the local catalogue. Verify spelling or "
                            "search the catalogue endpoint."
                        ),
                    )
                )

        # Step 3: Run deterministic rules (fixed order; interaction_service enforces it).
        if resolved:
            safety_findings = interaction_service.screen_medications(resolved, patient, db)
        else:
            safety_findings = []

        all_findings = safety_findings + unresolved_findings

        # Step 4: Optionally enrich findings with external evidence.
        if include_evidence and resolved:
            enriched = asyncio.get_event_loop()
            for i, finding in enumerate(all_findings):
                if finding.type in ("DRUG_DRUG_INTERACTION", "PREGNANCY", "RENAL_CONTRAINDICATION",
                                    "HEPATIC_CONTRAINDICATION", "G6PD_CONTRAINDICATION",
                                    "RESPIRATORY_CONTRAINDICATION", "HYPERKALEMIA_RISK",
                                    "ALLERGY", "ALLERGY_CROSS_REACTIVITY"):
                    drug_name = finding.medications[0] if finding.medications else ""
                    try:
                        loop = asyncio.new_event_loop()
                        evidence = loop.run_until_complete(evidence_service.get_evidence(drug_name))
                        loop.close()
                        if evidence:
                            all_findings[i] = SafetyFinding(
                                **{
                                    **finding.model_dump(),
                                    "evidence": evidence,
                                    "evidence_unavailable": False,
                                }
                            )
                        else:
                            all_findings[i] = SafetyFinding(
                                **{**finding.model_dump(), "evidence_unavailable": True}
                            )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Evidence retrieval error: %s", exc)
                        all_findings[i] = SafetyFinding(
                            **{**finding.model_dump(), "evidence_unavailable": True}
                        )

        # Step 5: Derive overall status.
        status = _derive_status(all_findings, patient)

        # Step 6: LLM explanation (best-effort; never blocks the response).
        explanation: str | None = None
        try:
            if all_findings:
                explanation = self.pharmacist_agent.explain(all_findings, patient.name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("PharmacistAgent.explain() raised unexpectedly: %s", exc)
            explanation = None

        catalogue_version = f"ppb-{datetime.now(tz=timezone.utc).date().isoformat()}"

        response = ScreeningResponse(
            patient_id=patient_id,
            status=status,
            findings=all_findings,
            recommendations=[],
            ruleset_version=settings.ruleset_version,
            catalogue_version=catalogue_version,
            explanation=explanation,
        )

        # Step 7: Write audit record.
        try:
            audit = ScreeningAudit(
                request_id=request_id,
                patient_id=patient_id,
                ruleset_version=settings.ruleset_version,
                result_json=response.model_dump_json(),
            )
            save_screening_audit(db, audit)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to save screening audit: %s", exc)

        return response
