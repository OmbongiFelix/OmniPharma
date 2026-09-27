"""Pydantic schemas for drug catalogue lookup and search responses.

Imports/dependencies: pydantic.

Public outputs: `DrugSummary`, `DrugDetail`, `MedicationContext`.
"""

from pydantic import BaseModel, Field


class MedicationContext(BaseModel):
    """Canonical medication record used throughout the rule engine.

    This schema is the internal representation passed between the
    orchestrator, service layer, and rule modules.  It must never be
    built from an unresolved name — always go through
    ``drug_catalog_service.resolve_drug()`` first.

    Attributes:
        id: Database primary key of the :class:`~app.db.models.Medication`.
        canonical_name: Normalised INN-based name (lowercase, whitespace-
            collapsed) used as the primary key for rule lookups.
        inn: International Non-proprietary Name.
        trade_name: Registered trade name, if available.
        dosage_form: e.g. ``Tablet``, ``Capsule``, ``Injection``.
        strength: e.g. ``500 mg``, ``10 mg/mL``.
        source: Provenance tag, e.g. ``ppb-scraped`` or ``synthetic demo``.
    """

    id: int | None = None
    canonical_name: str
    inn: str | None = None
    trade_name: str | None = None
    dosage_form: str | None = None
    strength: str | None = None
    source: str | None = None


class DrugSummary(BaseModel):
    """Lightweight catalogue entry for autocomplete/search responses.

    Attributes:
        id: Database primary key.
        canonical_name: Normalised drug name.
        inn: International Non-proprietary Name.
        trade_name: Registered trade name.
        dosage_form: Dosage form.
        strength: Dose strength string.
        source: Provenance tag.
    """

    id: int
    canonical_name: str
    inn: str | None = None
    trade_name: str | None = None
    dosage_form: str | None = None
    strength: str | None = None
    source: str | None = None


class DrugDetail(BaseModel):
    """Full catalogue entry for ``GET /api/v1/medications/{drug_id}``.

    Attributes:
        id: Database primary key.
        canonical_name: Normalised drug name.
        inn: International Non-proprietary Name.
        trade_name: Registered trade name.
        dosage_form: Dosage form.
        strength: Dose strength string.
        source: Provenance tag.
        in_stock: ``True`` when at least one positive inventory row exists
            in any facility.
        total_quantity: Sum of all inventory quantities across facilities.
    """

    id: int
    canonical_name: str
    inn: str | None = None
    trade_name: str | None = None
    dosage_form: str | None = None
    strength: str | None = None
    source: str | None = None
    in_stock: bool = False
    total_quantity: int = 0


# Internal row types used by rule modules as typed data-transfer objects.


class InteractionRuleRow(BaseModel):
    """Typed row from the ``interaction_rules`` table.

    Attributes:
        id: Rule row primary key.
        drug_a: First drug in the interacting pair.
        drug_b: Second drug in the interacting pair.
        severity: ``INFO | LOW | MODERATE | HIGH | CONTRAINDICATED``.
        mechanism: Clinical mechanism description.
        recommendation: Prescriber action guidance.
        source: Data provenance tag.
        version: Ruleset version string.
    """

    id: int
    drug_a: str
    drug_b: str
    severity: str
    mechanism: str
    recommendation: str
    source: str | None = None
    version: str = "demo-1.0"


class PregnancyWarningRow(BaseModel):
    """Typed row from the ``pregnancy_drug_warnings`` table.

    Attributes:
        id: Rule row primary key.
        drug_name: Canonical drug name.
        trimester_scope: ``ALL | FIRST | SECOND | THIRD``.
        severity: ``INFO | LOW | MODERATE | HIGH | CONTRAINDICATED``.
        mechanism: Clinical mechanism of harm.
        recommendation: Prescriber action guidance.
        source: Data provenance tag.
        version: Ruleset version string.
    """

    id: int
    drug_name: str
    trimester_scope: str
    severity: str
    mechanism: str
    recommendation: str
    source: str | None = None
    version: str = "demo-1.0"


class ConditionContraindicationRow(BaseModel):
    """Typed row from the ``condition_drug_contraindications`` table.

    Attributes:
        id: Rule row primary key.
        condition_code: ICD-10 code or reserved pseudo-code.
        drug_name: Canonical drug name.
        finding_type: One of the five contraindication finding-type values.
        severity: ``INFO | LOW | MODERATE | HIGH | CONTRAINDICATED``.
        mechanism: Clinical mechanism text.
        recommendation: Prescriber action guidance.
        source: Data provenance tag.
        version: Ruleset version string.
    """

    id: int
    condition_code: str
    drug_name: str
    finding_type: str
    severity: str
    mechanism: str
    recommendation: str
    source: str | None = None
    version: str = "demo-1.0"


class AllergyCrossReactivityRow(BaseModel):
    """Typed row from the ``allergy_cross_reactivity`` table.

    Attributes:
        id: Rule row primary key.
        allergen: Recorded allergen name.
        cross_reactive_drug: Drug that may trigger a cross-reactive response.
        mechanism: Clinical mechanism of cross-reactivity.
        severity: Expected reaction severity.
        source: Data provenance tag.
        version: Ruleset version string.
    """

    id: int
    allergen: str
    cross_reactive_drug: str
    mechanism: str
    severity: str
    source: str | None = None
    version: str = "demo-1.0"
