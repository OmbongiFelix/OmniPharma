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

from sqlalchemy.orm import Session

from app.core.exceptions import RuleConfigurationError
from app.db.repositories import (
    get_active_allergy_cross_reactivity,
    get_active_condition_contraindications,
    get_active_interaction_rules,
    get_active_pregnancy_warnings,
)
from app.rules import (
    age_based_rules,
    allergy_rules,
    contraindication_rules,
    duplicate_therapy_rules,
    interaction_rules,
    pregnancy_rules,
)
from app.schemas.medication import (
    AllergyCrossReactivityRow,
    ConditionContraindicationRow,
    InteractionRuleRow,
    MedicationContext,
    PregnancyWarningRow,
)
from app.schemas.patient import PatientContext
from app.schemas.screening import SafetyFinding


def _orm_to_interaction_rows(rows) -> list[InteractionRuleRow]:
    return [
        InteractionRuleRow(
            id=r.id,
            drug_a=r.drug_a,
            drug_b=r.drug_b,
            severity=r.severity,
            mechanism=r.mechanism,
            recommendation=r.recommendation,
            source=r.source,
            version=r.version,
        )
        for r in rows
    ]


def _orm_to_pregnancy_rows(rows) -> list[PregnancyWarningRow]:
    return [
        PregnancyWarningRow(
            id=r.id,
            drug_name=r.drug_name,
            trimester_scope=r.trimester_scope,
            severity=r.severity,
            mechanism=r.mechanism,
            recommendation=r.recommendation,
            source=r.source,
            version=r.version,
        )
        for r in rows
    ]


def _orm_to_contraindication_rows(rows) -> list[ConditionContraindicationRow]:
    return [
        ConditionContraindicationRow(
            id=r.id,
            condition_code=r.condition_code,
            drug_name=r.drug_name,
            finding_type=r.finding_type,
            severity=r.severity,
            mechanism=r.mechanism,
            recommendation=r.recommendation,
            source=r.source,
            version=r.version,
        )
        for r in rows
    ]


def _orm_to_cross_reactivity_rows(rows) -> list[AllergyCrossReactivityRow]:
    return [
        AllergyCrossReactivityRow(
            id=r.id,
            allergen=r.allergen,
            cross_reactive_drug=r.cross_reactive_drug,
            mechanism=r.mechanism,
            severity=r.severity,
            source=r.source,
            version=r.version,
        )
        for r in rows
    ]


def screen_medications(
    medications: list[MedicationContext],
    patient: PatientContext,
    db: Session,
) -> list[SafetyFinding]:
    """Evaluate medicine combinations and patient-specific safety constraints.

    Args:
        medications: Canonicalized medicines being considered, already
            resolved via `drug_catalog_service.resolve_drug()`.
        patient: Demographics, conditions, allergies, pregnancy,
            renal/hepatic/G6PD status.
        db: Active SQLAlchemy session used to load rule tables.

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
    # Load rule tables from the DB (via repositories — no direct SQL here).
    interaction_rule_rows = _orm_to_interaction_rows(get_active_interaction_rules(db))
    pregnancy_warning_rows = _orm_to_pregnancy_rows(get_active_pregnancy_warnings(db))
    contraindication_rule_rows = _orm_to_contraindication_rows(
        get_active_condition_contraindications(db)
    )
    cross_reactivity_rows = _orm_to_cross_reactivity_rows(
        get_active_allergy_cross_reactivity(db)
    )

    all_findings: list[SafetyFinding] = []

    # 1. Drug–drug interactions.
    all_findings.extend(
        interaction_rules.evaluate_drug_pairs(medications, interaction_rule_rows)
    )

    # 2a. Direct allergy conflicts + 2b. Cross-reactive allergy conflicts.
    all_findings.extend(
        allergy_rules.evaluate_allergies(medications, patient, cross_reactivity_rows)
    )

    # 3. Pregnancy warnings (no-op if not PREGNANT).
    all_findings.extend(
        pregnancy_rules.evaluate_pregnancy(medications, patient, pregnancy_warning_rows)
    )

    # 4. Condition-drug contraindications (renal, hepatic, hyperkalemia, G6PD, respiratory).
    if contraindication_rule_rows:
        all_findings.extend(
            contraindication_rules.evaluate_contraindications(
                medications, patient, contraindication_rule_rows
            )
        )

    # 5. Age-based caution.
    all_findings.extend(age_based_rules.evaluate_age_based_caution(medications, patient))

    # 6. Duplicate therapy.
    all_findings.extend(duplicate_therapy_rules.evaluate_duplicate_therapy(medications))

    return all_findings
