**OmniPharma — Backend Developer Reference & Docstring Contract**

_Python/FastAPI module contracts, responsibilities, imports, outputs and full docstrings. This file is the single source of truth for the backend build. `05_Antigravity_Backend_Prompt.md` references this file directly — every module and public function Antigravity generates must carry a docstring that matches the contract given here, not a paraphrase of it._

# 1. Package Layout

```
OmniPharma/backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── patients.py
│   │   ├── screening.py
│   │   ├── medications.py
│   │   └── health.py
│   ├── agents/
│   │   ├── pharmacist_agent.py
│   │   ├── orchestrator.py
│   │   └── prompts.py
│   ├── services/
│   │   ├── patient_service.py
│   │   ├── interaction_service.py
│   │   ├── recommendation_service.py
│   │   ├── drug_catalog_service.py
│   │   └── evidence_service.py
│   ├── rules/
│   │   ├── interaction_rules.py
│   │   ├── contraindication_rules.py
│   │   ├── allergy_rules.py
│   │   ├── pregnancy_rules.py
│   │   └── age_based_rules.py          (new)
│   ├── db/
│   │   ├── session.py
│   │   ├── models.py
│   │   └── repositories.py
│   ├── schemas/
│   │   ├── patient.py
│   │   ├── medication.py
│   │   └── screening.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py               (new)
├── scraper/
│   ├── ppb_scraper.py
│   ├── parser.py
│   └── database.py
└── tests/
```

# 2. Docstring Standard

Every Python module uses a module-level docstring describing its purpose, boundaries, key dependencies and public API. Public classes and functions use full Google-style docstrings with `Args`, `Returns`, `Raises`, and `Notes` where relevant. Every field of a Pydantic schema and SQLAlchemy model gets an inline comment or `Field(..., description=...)` rather than being left bare. Do not document implementation details that are not part of the public contract. A module or function with no docstring, or a docstring that only restates its name, does not satisfy this contract — every entry below is the minimum bar, not a template to shorten.

# 3. Module Reference

## `app/main.py`

```python
"""FastAPI application entry point for OmniPharma.

Registers all API routers under `/api/v1`, configures CORS from
`app.core.config.Settings`, attaches request-ID and structured-logging
middleware, and exposes startup/shutdown hooks that open and close the
database engine. This module contains no business logic: it wires
together `app.api.*` routers and `app.core.config`.

Imports/dependencies: fastapi, app.api.health, app.api.patients,
app.api.screening, app.api.medications, app.core.config, app.core.logging.

Public outputs: `app`, the FastAPI ASGI application object served by
uvicorn (`uvicorn app.main:app`).
"""
```

## `app/api/patients.py`

```python
"""HTTP endpoints for synthetic patient demographics and history.

Thin request/response layer only: every handler validates input with
Pydantic, delegates to `app.services.patient_service`, and maps service
exceptions to HTTP errors. Handlers must not query the database directly.

Imports/dependencies: fastapi, app.schemas.patient, app.services.patient_service.

Public outputs: route handlers registered under `/api/v1/patients`.

    GET  /api/v1/patients                       -> list[PatientSummary]
    GET  /api/v1/patients/{patient_id}           -> PatientContext
    GET  /api/v1/patients/{patient_id}/medications -> PatientMedications
"""
```

## `app/api/screening.py`

```python
"""HTTP endpoint for medication-safety screening and recommendation requests.

Validates `ScreeningRequest`, calls
`app.agents.orchestrator.run_medication_review()`, and returns
`ScreeningResponse`. Never runs a clinical rule directly — that would
duplicate the orchestrator's ordering guarantees (see
`AgentOrchestrator.run_medication_review`).

Imports/dependencies: fastapi, app.schemas.screening, app.agents.orchestrator.

Public outputs: route handlers registered under `/api/v1/screenings`.

    POST /api/v1/screenings/interaction -> ScreeningResponse
    POST /api/v1/recommendations        -> list[Recommendation]
"""
```

## `app/api/medications.py`

```python
"""Drug catalogue lookup/search endpoints.

Imports/dependencies: fastapi, app.services.drug_catalog_service.

Public outputs: route handlers registered under `/api/v1/medications`.

    GET /api/v1/medications/search?q=... -> list[DrugSummary]
    GET /api/v1/medications/{drug_id}    -> DrugDetail
"""
```

## `app/api/health.py`

```python
"""Service and dependency health checks.

Public outputs:

    GET /api/v1/health -> HealthStatus

`HealthStatus` reports application status plus a boolean for each
dependency actually checked (primary DB, PPB catalogue DB, LLM adapter
reachability if configured). A degraded dependency returns HTTP 200 with
`status: "degraded"` and the specific failing dependency named, not a
generic 500 — callers need to distinguish "app is down" from "one
optional dependency is down."
"""
```

## `app/agents/orchestrator.py`

```python
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


class AgentOrchestrator:
    """Coordinates a full medication-safety review for one patient.

    Holds references to the services it orchestrates; does not hold
    request-scoped state between calls. One instance may safely serve
    multiple concurrent requests because each call to
    `run_medication_review` builds its own local review state.

    Attributes:
        patient_service: Retrieves patient context. Never mutated after
            construction.
        interaction_service: Runs all deterministic rule categories,
            drug-drug and patient-constraint alike.
        recommendation_service: Generates and filters alternative
            candidates when a review requests them.
        evidence_service: Retrieves optional supporting evidence from
            external sources; failures here must never block a review.
        pharmacist_agent: Narrative explanation layer; optional at
            runtime (see `run_medication_review` Notes).
    """

    def run_medication_review(
        self,
        patient_id: int,
        medication_ids: list[str],
        include_evidence: bool = False,
    ) -> "ScreeningResponse":
        """Run a complete medication-safety review for a patient.

        Args:
            patient_id: Internal patient identifier.
            medication_ids: Medicine names or catalogue IDs being
                reviewed against the patient's context. Names are
                resolved via `drug_catalog_service.resolve_drug()`
                before any rule runs.
            include_evidence: When True, calls
                `evidence_service.get_evidence()` for each finding that
                supports external evidence. Evidence retrieval failures
                are recorded as `evidence_unavailable=True` on the
                affected finding and never raise.

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
            "LLM unavailable" failure mode.
        """
```

## `app/agents/pharmacist_agent.py`

```python
"""LLM-facing agent wrapper.

Converts a list of structured `SafetyFinding` objects into a concise,
pharmacist-facing prose explanation. This module must not invent safety
facts, change a severity, add an interaction that isn't in the input
findings, or suggest a prescription — it summarizes what the
deterministic layer already decided.

Imports/dependencies: an LLM SDK (provider-agnostic via
`app.core.config.Settings.llm_provider`), app.schemas.screening,
app.agents.prompts.

Public outputs: `PharmacistAgent` (see below).
"""


class PharmacistAgent:
    """Summarizes structured safety findings into pharmacist-readable prose.

    Attributes:
        client: The configured LLM SDK client. `None` when no provider
            is configured; in that case `explain()` returns `None`
            immediately rather than raising, so callers do not need to
            branch on configuration state.
    """

    def explain(self, findings: list["SafetyFinding"]) -> str | None:
        """Produce a short natural-language explanation of findings.

        Args:
            findings: Structured findings already produced by the
                deterministic rule engine, in final severity order.

        Returns:
            A concise explanation string, or `None` if no LLM provider
            is configured or the call fails for any reason (timeout,
            malformed response, provider error). A `None` return is not
            an error state for the caller — the orchestrator always has
            a complete deterministic result regardless.

        Raises:
            This method intentionally raises nothing. Every failure mode
            degrades to `None` so a flaky LLM provider can never block a
            safety-critical response.

        Notes:
            The prompt built from `app.agents.prompts` explicitly
            instructs the model to restate only what is present in
            `findings` and never to add a new interaction, drug, or
            severity level.
        """
```

## `app/services/patient_service.py`

```python
"""Retrieves patient context from the patient database.

This is the only module allowed to assemble a full `PatientContext` from
raw rows across `patients`, `conditions`, `allergies`,
`medication_history`, and current `prescriptions`. Other modules must
depend on `PatientContext`, not on `db.repositories` directly.

Imports/dependencies: app.db.session, app.db.repositories,
app.schemas.patient.

Public outputs: `get_patient_context()`, `list_patients()`.
"""


def get_patient_context(patient_id: int) -> "PatientContext":
    """Retrieve a patient's full clinical context.

    Args:
        patient_id: Internal patient identifier.

    Returns:
        A `PatientContext` combining demographics, derived age,
        pregnancy status, renal status, hepatic status, g6pd status,
        allergies, active conditions, current prescriptions and
        medication history.

    Raises:
        PatientNotFoundError: If no patient with `patient_id` exists.

    Notes:
        Fields recorded as `UNKNOWN` (renal_status, hepatic_status,
        g6pd_status) are returned as `UNKNOWN`, never coerced to
        `NORMAL`. Downstream rule modules must treat `UNKNOWN` as a
        data-gap warning, not a negative result.
    """


def list_patients(query: str | None = None) -> list["PatientSummary"]:
    """List or search synthetic patients for the patient-selection UI.

    Args:
        query: Optional case-insensitive substring match against
            `patient_code` or `name`. `None` returns all patients.

    Returns:
        Lightweight `PatientSummary` records (id, patient_code, name,
        sex, pregnancy_status) — not the full context, to keep the
        list endpoint cheap.
    """
```

## `app/services/interaction_service.py`

```python
"""Runs every deterministic drug-drug and patient-constraint check.

Delegates to the pure functions in `app.rules.*`; this module's job is
sequencing and result assembly, not clinical logic itself. Rule modules
never call each other directly — this service is the only caller of all
of them, which is what lets `AgentOrchestrator` guarantee a fixed
evaluation order.

Imports/dependencies: app.rules.interaction_rules,
app.rules.allergy_rules, app.rules.pregnancy_rules,
app.rules.contraindication_rules, app.rules.age_based_rules,
app.db.repositories, app.schemas.screening.

Public outputs: `screen_medications()`.
"""


def screen_medications(
    medications: list["MedicationContext"],
    patient: "PatientContext",
) -> list["SafetyFinding"]:
    """Evaluate medicine combinations and patient-specific safety constraints.

    Args:
        medications: Canonicalized medicines being considered, already
            resolved via `drug_catalog_service.resolve_drug()`.
        patient: Demographics, conditions, allergies, pregnancy,
            renal/hepatic/G6PD status.

    Returns:
        Machine-readable safety findings in the fixed order: drug-drug,
        allergy (direct then cross-reactive), pregnancy (only if
        `patient.pregnancy_status == "PREGNANT"`), condition-drug
        contraindication (renal, hepatic, hyperkalemia, G6PD,
        respiratory — evaluated in that sub-order), age-based caution,
        duplicate therapy. Findings within the same category are
        ordered by descending severity.

    Raises:
        RuleConfigurationError: If a required rule table (e.g.
            `interaction_rules`, `pregnancy_drug_warnings`,
            `condition_drug_contraindications`,
            `allergy_cross_reactivity`) cannot be loaded.

    Notes:
        This function never mutates `medications` or `patient`, and
        never returns fewer findings than the rules produce — filtering
        or ranking findings for display is a frontend concern.
    """
```

## `app/services/recommendation_service.py`

```python
"""Produces and safety-filters candidate alternative medicines.

Imports/dependencies: app.services.drug_catalog_service,
app.services.interaction_service, app.db.repositories.

Public outputs: `recommend_alternatives()`.
"""


def recommend_alternatives(
    patient: "PatientContext",
    target_medication: "MedicationContext",
    indication: str | None = None,
) -> list["Recommendation"]:
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
```

## `app/services/drug_catalog_service.py`

```python
"""Searches normalized PPB registered products and maps trade/INN names
to canonical medication records.

Imports/dependencies: SQLAlchemy, app.db.repositories.

Public outputs: `search_drugs()`, `resolve_drug()`.
"""


def resolve_drug(name: str) -> "MedicationContext":
    """Resolve a free-text drug name to a canonical medication record.

    Args:
        name: Trade name, INN, or common name as entered by a user or
            supplied in a screening request.

    Returns:
        The canonical `MedicationContext` (canonical_name, inn,
        trade_name, dosage_form, source).

    Raises:
        DrugResolutionError: If `name` does not match any catalogue
            entry after normalization (case-folding, whitespace
            collapse, common trade/INN alias lookup). The caller must
            surface this as an `UNRESOLVED_DRUG` finding rather than
            skipping the medicine.

    Notes:
        Never returns a best-guess partial match silently; a fuzzy
        match below the configured confidence threshold is treated as
        unresolved, not resolved.
    """


def search_drugs(query: str) -> list["DrugSummary"]:
    """Search the local catalogue for autocomplete/lookup use.

    Args:
        query: Free-text search term.

    Returns:
        Up to a configured max number of `DrugSummary` matches ranked by
        relevance (exact trade-name match first, then INN match, then
        substring match).
    """
```

## `app/services/evidence_service.py`

```python
"""Retrieves supporting drug information from configured external
sources and records provenance for every item returned.

Imports/dependencies: httpx.AsyncClient, external API adapters (e.g.
openFDA), app.core.config.

Public outputs: `get_evidence()`.
"""


async def get_evidence(drug_name: str) -> list["EvidenceItem"]:
    """Retrieve supporting (non-authoritative) evidence for a drug.

    Args:
        drug_name: Canonical drug name to look up.

    Returns:
        A list of `EvidenceItem`, each with `source_name`, `source_url`,
        `retrieved_at`, and a short excerpt. Returns an empty list
        (never raises) if every configured source times out or is
        unavailable; the caller marks `evidence_unavailable=True` in
        that case.

    Notes:
        openFDA responses are treated as supporting evidence only, per
        `03_Agent_Architecture.md` Section 9 — this function must never
        be the sole basis for a finding's severity.
    """
```

## `app/rules/interaction_rules.py`

```python
"""Deterministic drug-drug interaction rules for the hackathon's known
scenarios.

Pure functions only: no I/O, no database session, no randomness. Reads
already-loaded `interaction_rules` table rows passed in by the caller.

Imports/dependencies: app.schemas only.

Public outputs: `evaluate_drug_pairs()`.
"""


def evaluate_drug_pairs(
    medications: list["MedicationContext"],
    rules: list["InteractionRuleRow"],
) -> list["SafetyFinding"]:
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
```

## `app/rules/contraindication_rules.py`

```python
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


def evaluate_contraindications(
    medications: list["MedicationContext"],
    patient: "PatientContext",
    rules: list["ConditionContraindicationRow"],
) -> list["SafetyFinding"]:
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
```

## `app/rules/allergy_rules.py`

```python
"""Checks medicine ingredients/classes against recorded allergies,
including cross-reactive drug classes.

Imports/dependencies: app.schemas only.

Public outputs: `evaluate_allergies()`.
"""


def evaluate_allergies(
    medications: list["MedicationContext"],
    patient: "PatientContext",
    cross_reactivity_rules: list["AllergyCrossReactivityRow"],
) -> list["SafetyFinding"]:
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
```

## `app/rules/pregnancy_rules.py`

```python
"""Checks pregnancy status against configured medicine warnings.

Sibling module to `contraindication_rules.py`; kept separate because
pregnancy status is a patient-row field (`patients.pregnancy_status`),
not a `conditions` table row, and because pregnancy warnings can carry
trimester scope, which condition-drug contraindications do not.

Imports/dependencies: app.schemas only.

Public outputs: `evaluate_pregnancy()`.
"""


def evaluate_pregnancy(
    medications: list["MedicationContext"],
    patient: "PatientContext",
    rules: list["PregnancyWarningRow"],
) -> list["SafetyFinding"]:
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
```

## `app/rules/age_based_rules.py` (new module)

```python
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


def evaluate_age_based_caution(
    medications: list["MedicationContext"],
    patient: "PatientContext",
) -> list["SafetyFinding"]:
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
```

## `app/db/models.py`

```python
"""SQLAlchemy ORM models for patients, conditions, allergies,
medications, prescriptions, medication history, inventory, and every
rule table (drug-drug interactions, pregnancy warnings,
condition-drug contraindications, allergy cross-reactivity).

Imports/dependencies: sqlalchemy.

Public outputs: `Patient`, `Condition`, `Allergy`, `Medication`,
`Prescription`, `MedicationHistory`, `Inventory`, `InteractionRule`,
`PregnancyDrugWarning`, `ConditionDrugContraindication`,
`AllergyCrossReactivity`, `ScreeningAudit`.
"""
```

## `app/db/repositories.py`

```python
"""Persistence abstraction so business logic does not depend directly
on SQL statements or the SQLAlchemy session API.

Every rule-table read (interaction rules, pregnancy warnings,
condition-drug contraindications, allergy cross-reactivity) goes
through a repository function here so `app.services.*` and `app.rules.*`
never import `sqlalchemy` directly.

Imports/dependencies: sqlalchemy, app.db.models.

Public outputs: one repository class or function set per model, e.g.
`PatientRepository`, `get_active_interaction_rules()`,
`get_active_pregnancy_warnings()`,
`get_active_condition_contraindications()`,
`get_active_allergy_cross_reactivity()`.
"""
```

## `app/schemas/screening.py`

```python
"""Pydantic request/response contracts for screening results.

Imports/dependencies: pydantic.

Public outputs: `ScreeningRequest`, `ScreeningResponse`, `SafetyFinding`,
`Recommendation`.
"""

from pydantic import BaseModel, Field


class ScreeningRequest(BaseModel):
    """Request body for POST /api/v1/screenings/interaction.

    Attributes:
        patient_id: Internal patient identifier.
        medications: Drug names or catalogue IDs to screen.
        include_evidence: Whether to attach external evidence per
            finding. Defaults to False to keep the common case fast.
    """

    patient_id: int
    medications: list[str]
    include_evidence: bool = False


class SafetyFinding(BaseModel):
    """One machine-readable safety finding.

    Attributes:
        type: One of DRUG_DRUG_INTERACTION, ALLERGY,
            ALLERGY_CROSS_REACTIVITY, PREGNANCY, RENAL_CONTRAINDICATION,
            HEPATIC_CONTRAINDICATION, HYPERKALEMIA_RISK,
            G6PD_CONTRAINDICATION, RESPIRATORY_CONTRAINDICATION,
            AGE_BASED_CAUTION, DUPLICATE_THERAPY, UNRESOLVED_DRUG.
        severity: INFO, LOW, MODERATE, HIGH, or CONTRAINDICATED.
        medications: Canonical names of every medicine involved.
        rule_id: Stable identifier of the rule/row that produced this
            finding, for traceability back to `interaction_rules`,
            `pregnancy_drug_warnings`, `condition_drug_contraindications`,
            or `allergy_cross_reactivity`.
        summary: One-sentence, pharmacist-facing summary.
        rationale: Fuller mechanism/reasoning text.
        evidence: Optional supporting evidence items; empty unless
            `include_evidence=True` was set on the request.
        evidence_unavailable: True if evidence was requested but every
            configured source failed or timed out.
    """

    type: str
    severity: str
    medications: list[str]
    rule_id: str
    summary: str
    rationale: str
    evidence: list[dict] = Field(default_factory=list)
    evidence_unavailable: bool = False


class ScreeningResponse(BaseModel):
    """Response body for POST /api/v1/screenings/interaction.

    Attributes:
        patient_id: Echoes the request.
        status: CLEAR, REVIEW_REQUIRED, CONTRAINDICATED, or
            INCOMPLETE_CONTEXT — derived from the highest severity
            present in `findings` (see
            `AgentOrchestrator.run_medication_review`).
        findings: All findings in fixed rule-category order.
        recommendations: Populated only when the request or a
            follow-up call asked for alternatives.
        ruleset_version: Version tag of the interaction/contraindication
            rule tables used.
        catalogue_version: Timestamp/version of the PPB catalogue
            snapshot used to resolve drug names.
        explanation: Optional narrative from `PharmacistAgent.explain()`;
            `None` if the LLM was unavailable or not configured.
    """

    patient_id: int
    status: str
    findings: list[SafetyFinding]
    recommendations: list[dict] = Field(default_factory=list)
    ruleset_version: str
    catalogue_version: str
    explanation: str | None = None


class Recommendation(BaseModel):
    """One alternative-medicine candidate, included or excluded.

    Attributes:
        drug_name: Canonical name of the candidate.
        excluded: False if this candidate is being offered for
            pharmacist review; True if it was filtered out.
        included_reason: Present when excluded=False.
        excluded_reason: Present when excluded=True — the specific
            rule/finding that removed this candidate. Never omitted for
            an excluded candidate; pharmacists must be able to see why
            an option isn't offered.
        availability: Inventory status if inventory-aware mode is
            enabled; otherwise omitted.
    """

    drug_name: str
    excluded: bool = False
    included_reason: str | None = None
    excluded_reason: str | None = None
    availability: str | None = None
```

## `app/core/exceptions.py` (new module)

```python
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
```

## `scraper/ppb_scraper.py`

```python
"""Downloads the public PPB registered-products table, iterates
pagination, normalizes records and writes the local SQLite catalogue.

This is an offline ingestion job, run on a schedule or manually — it
must never be imported into a request-time API handler (see Section 5).

Imports/dependencies: playwright (primary) or httpx/requests (fallback),
BeautifulSoup4/lxml, sqlite3.

Public outputs: `scrape_ppb_catalog()` and a CLI entry point
(`python ppb_scraper.py --output ppb_drugs.db`).
"""
```

## `scraper/parser.py`

```python
"""Parses a PPB HTML page into normalized product rows.

Imports/dependencies: BeautifulSoup4/lxml.

Public outputs: `parse_products_page()`.
"""


def parse_products_page(html: str) -> list[dict]:
    """Parse one rendered PPB results page into product rows.

    Args:
        html: Full page HTML after client-side rendering.

    Returns:
        A list of dicts with keys matching the `products` table columns
        (registration_no, trade_name, inn_of_api, dosage_form_name,
        country_of_origin, local_foreign, mah_company_name,
        local_technical_representative, date_of_registration,
        date_of_expiry).

    Raises:
        ValueError: If the expected product table or its column headers
            cannot be found — signals the site structure changed and the
            scraper needs review, rather than silently returning an
            empty or partial page.
    """
```

## `scraper/database.py`

```python
"""Creates schema and performs idempotent upserts into the PPB SQLite
database.

Imports/dependencies: sqlite3.

Public outputs: `init_db()`, `upsert_products()`.
"""


def upsert_products(conn, rows: list[dict], page: int) -> int:
    """Insert or update product rows, keyed on (registration_no, trade_name).

    Args:
        conn: Open sqlite3 connection.
        rows: Normalized rows from `parse_products_page()`.
        page: Source page number, stored for audit/debugging.

    Returns:
        Number of rows written (inserted or updated).
    """
```

# 4. Import/Export Rules

- API modules may import schemas and services, but services must not import FastAPI route handlers.
- Rule modules (`app/rules/*`) are pure functions: no I/O, no database session, no imports of each other. `app/services/interaction_service.py` is the only caller of all of them, so evaluation order is guaranteed in exactly one place.
- The LLM layer (`pharmacist_agent.py`) consumes structured findings; it must not become the source of truth for interaction severity, and every failure mode there degrades to `explanation=None` rather than raising.
- External API adapters must be isolated behind `evidence_service` interfaces.
- Database repositories (`app/db/repositories.py`) are the only layer allowed to contain persistence-specific queries, including reads of the three new rule tables.
- Scraper code is a separate ingestion service and must not be imported into request-time API handlers.
- Domain exceptions live in `app.core.exceptions`; only `app/api/*` may catch them and translate to an `HTTPException`.

# 5. What Changed From Revision 1

- Added `app/rules/age_based_rules.py` and `app/core/exceptions.py` as new modules with their own full contracts above.
- `contraindication_rules.py`, `pregnancy_rules.py`, and `allergy_rules.py` now each take an explicit rule-row argument (`condition_drug_contraindications`, `pregnancy_drug_warnings`, `allergy_cross_reactivity` respectively) instead of an unspecified "configured medicine warnings" — there is now a concrete table and repository function behind each.
- `SafetyFinding.type` enum expanded from 6 values to 12 to give renal, hepatic, hyperkalemia, G6PD, respiratory and age-based findings their own labels instead of collapsing them all into a generic `CONTRAINDICATION`.
