"""Unit tests for all clinical rule modules.

Covers:
- interaction_rules.evaluate_drug_pairs
- allergy_rules.evaluate_allergies (ALLERGY and ALLERGY_CROSS_REACTIVITY)
- pregnancy_rules.evaluate_pregnancy
- contraindication_rules.evaluate_contraindications
  (RENAL_CONTRAINDICATION, HEPATIC_CONTRAINDICATION, HYPERKALEMIA_RISK,
   G6PD_CONTRAINDICATION, RESPIRATORY_CONTRAINDICATION)
- age_based_rules.evaluate_age_based_caution (AGE_BASED_CAUTION)
- duplicate_therapy_rules.evaluate_duplicate_therapy (DUPLICATE_THERAPY)
"""

from datetime import date, timedelta

import pytest

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
from app.schemas.patient import AllergyRecord, ConditionRecord, PatientContext
from tests.conftest import make_med, make_patient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ddi_rule(drug_a: str, drug_b: str, severity: str = "HIGH") -> InteractionRuleRow:
    return InteractionRuleRow(
        id=1, drug_a=drug_a, drug_b=drug_b,
        severity=severity, mechanism="Test mechanism.",
        recommendation="Test rec.", version="demo-1.0",
    )


def _make_preg_rule(drug_name: str, severity: str = "CONTRAINDICATED",
                    scope: str = "ALL") -> PregnancyWarningRow:
    return PregnancyWarningRow(
        id=1, drug_name=drug_name, trimester_scope=scope,
        severity=severity, mechanism="Teratogenic.", recommendation="Avoid.",
        version="demo-1.0",
    )


def _make_cond_rule(condition_code: str, drug_name: str,
                    finding_type: str, severity: str = "HIGH") -> ConditionContraindicationRow:
    return ConditionContraindicationRow(
        id=1, condition_code=condition_code, drug_name=drug_name,
        finding_type=finding_type, severity=severity,
        mechanism="Mechanism.", recommendation="Recommendation.",
        version="demo-1.0",
    )


def _make_cross_rule(allergen: str, cross_reactive_drug: str,
                     severity: str = "HIGH") -> AllergyCrossReactivityRow:
    return AllergyCrossReactivityRow(
        id=1, allergen=allergen, cross_reactive_drug=cross_reactive_drug,
        mechanism="Beta-lactam cross-reactivity.", severity=severity,
        version="demo-1.0",
    )


# ---------------------------------------------------------------------------
# interaction_rules
# ---------------------------------------------------------------------------


class TestEvaluateDrugPairs:
    def test_matching_pair_returns_ddi_finding(self):
        meds = [make_med("warfarin"), make_med("ibuprofen")]
        rules = [_make_ddi_rule("warfarin", "ibuprofen", "HIGH")]
        findings = interaction_rules.evaluate_drug_pairs(meds, rules)
        assert len(findings) == 1
        assert findings[0].type == "DRUG_DRUG_INTERACTION"
        assert findings[0].severity == "HIGH"
        assert "warfarin" in findings[0].medications
        assert "ibuprofen" in findings[0].medications

    def test_order_of_pair_does_not_matter(self):
        """Rule (a, b) must match (b, a) in the medication list."""
        meds = [make_med("ibuprofen"), make_med("warfarin")]
        rules = [_make_ddi_rule("warfarin", "ibuprofen")]
        findings = interaction_rules.evaluate_drug_pairs(meds, rules)
        assert len(findings) == 1

    def test_no_rule_returns_empty(self):
        meds = [make_med("metformin"), make_med("lisinopril")]
        rules = [_make_ddi_rule("warfarin", "ibuprofen")]
        findings = interaction_rules.evaluate_drug_pairs(meds, rules)
        assert findings == []

    def test_single_medication_returns_empty(self):
        findings = interaction_rules.evaluate_drug_pairs(
            [make_med("warfarin")], [_make_ddi_rule("warfarin", "ibuprofen")]
        )
        assert findings == []

    def test_findings_sorted_descending_severity(self):
        meds = [make_med("warfarin"), make_med("ibuprofen"), make_med("aspirin")]
        rules = [
            _make_ddi_rule("warfarin", "ibuprofen", "LOW"),
            _make_ddi_rule("warfarin", "aspirin", "HIGH"),
        ]
        findings = interaction_rules.evaluate_drug_pairs(meds, rules)
        assert findings[0].severity == "HIGH"
        assert findings[1].severity == "LOW"


# ---------------------------------------------------------------------------
# allergy_rules
# ---------------------------------------------------------------------------


class TestEvaluateAllergies:
    def test_direct_allergy_match(self):
        meds = [make_med("penicillin")]
        patient = make_patient(allergies=[AllergyRecord(allergen="penicillin", severity="SEVERE")])
        findings = allergy_rules.evaluate_allergies(meds, patient, [])
        assert len(findings) == 1
        assert findings[0].type == "ALLERGY"
        assert findings[0].severity == "CONTRAINDICATED"

    def test_allergy_cross_reactivity(self):
        meds = [make_med("amoxicillin")]
        patient = make_patient(allergies=[AllergyRecord(allergen="penicillin", severity="SEVERE")])
        cross_rules = [_make_cross_rule("penicillin", "amoxicillin", "HIGH")]
        findings = allergy_rules.evaluate_allergies(meds, patient, cross_rules)
        assert len(findings) == 1
        assert findings[0].type == "ALLERGY_CROSS_REACTIVITY"
        assert findings[0].severity == "HIGH"

    def test_none_allergen_ignored(self):
        meds = [make_med("amoxicillin")]
        patient = make_patient(allergies=[AllergyRecord(allergen="none", severity="NONE")])
        findings = allergy_rules.evaluate_allergies(meds, patient, [])
        assert findings == []

    def test_no_allergy_returns_empty(self):
        meds = [make_med("amoxicillin")]
        patient = make_patient(allergies=[])
        findings = allergy_rules.evaluate_allergies(meds, patient, [])
        assert findings == []

    def test_drug_not_allergen_not_cross_reactive_returns_empty(self):
        meds = [make_med("metformin")]
        patient = make_patient(allergies=[AllergyRecord(allergen="penicillin", severity="SEVERE")])
        cross_rules = [_make_cross_rule("penicillin", "amoxicillin")]
        findings = allergy_rules.evaluate_allergies(meds, patient, cross_rules)
        assert findings == []


# ---------------------------------------------------------------------------
# pregnancy_rules
# ---------------------------------------------------------------------------


class TestEvaluatePregnancy:
    def test_not_pregnant_returns_empty(self):
        meds = [make_med("isotretinoin")]
        patient = make_patient(pregnancy_status="NOT_PREGNANT")
        rules = [_make_preg_rule("isotretinoin")]
        assert pregnancy_rules.evaluate_pregnancy(meds, patient, rules) == []

    def test_not_applicable_returns_empty(self):
        meds = [make_med("warfarin")]
        patient = make_patient(pregnancy_status="NOT_APPLICABLE")
        rules = [_make_preg_rule("warfarin")]
        assert pregnancy_rules.evaluate_pregnancy(meds, patient, rules) == []

    def test_pregnant_with_contraindicated_drug(self):
        meds = [make_med("isotretinoin")]
        patient = make_patient(pregnancy_status="PREGNANT")
        rules = [_make_preg_rule("isotretinoin", severity="CONTRAINDICATED")]
        findings = pregnancy_rules.evaluate_pregnancy(meds, patient, rules)
        assert len(findings) == 1
        assert findings[0].type == "PREGNANCY"
        assert findings[0].severity == "CONTRAINDICATED"

    def test_pregnant_safe_drug_no_rule_returns_empty(self):
        meds = [make_med("paracetamol")]
        patient = make_patient(pregnancy_status="PREGNANT")
        rules = [_make_preg_rule("isotretinoin")]
        findings = pregnancy_rules.evaluate_pregnancy(meds, patient, rules)
        assert findings == []

    def test_trimester_scoped_rule_matches_conservatively(self):
        """SECOND-scoped rules match conservatively when no gestational week is tracked."""
        meds = [make_med("lisinopril")]
        patient = make_patient(pregnancy_status="PREGNANT")
        rules = [_make_preg_rule("lisinopril", severity="HIGH", scope="SECOND")]
        findings = pregnancy_rules.evaluate_pregnancy(meds, patient, rules)
        assert len(findings) == 1
        assert findings[0].severity == "HIGH"


# ---------------------------------------------------------------------------
# contraindication_rules
# ---------------------------------------------------------------------------


class TestEvaluateContraindications:
    def test_renal_contraindication(self):
        meds = [make_med("metformin")]
        patient = make_patient(renal_status="MODERATE_IMPAIRMENT")
        rules = [_make_cond_rule("RENAL-IMPAIRED", "metformin", "RENAL_CONTRAINDICATION", "HIGH")]
        findings = contraindication_rules.evaluate_contraindications(meds, patient, rules)
        assert len(findings) == 1
        assert findings[0].type == "RENAL_CONTRAINDICATION"
        assert findings[0].severity == "HIGH"

    def test_hepatic_contraindication(self):
        meds = [make_med("atorvastatin")]
        patient = make_patient(hepatic_status="MODERATE_IMPAIRMENT")
        rules = [_make_cond_rule("HEPATIC-IMPAIRED", "atorvastatin", "HEPATIC_CONTRAINDICATION", "MODERATE")]
        findings = contraindication_rules.evaluate_contraindications(meds, patient, rules)
        assert len(findings) == 1
        assert findings[0].type == "HEPATIC_CONTRAINDICATION"

    def test_hyperkalemia_risk(self):
        meds = [make_med("spironolactone")]
        condition = ConditionRecord(condition_code="N18", condition_name="CKD", status="ACTIVE")
        patient = make_patient(conditions=[condition])
        rules = [_make_cond_rule("N18", "spironolactone", "HYPERKALEMIA_RISK", "HIGH")]
        findings = contraindication_rules.evaluate_contraindications(meds, patient, rules)
        assert len(findings) == 1
        assert findings[0].type == "HYPERKALEMIA_RISK"

    def test_g6pd_contraindication(self):
        meds = [make_med("sulfamethoxazole-trimethoprim")]
        patient = make_patient(g6pd_status="DEFICIENT")
        rules = [_make_cond_rule("G6PD-DEFICIENT", "sulfamethoxazole-trimethoprim",
                                  "G6PD_CONTRAINDICATION", "HIGH")]
        findings = contraindication_rules.evaluate_contraindications(meds, patient, rules)
        assert len(findings) == 1
        assert findings[0].type == "G6PD_CONTRAINDICATION"
        assert findings[0].severity == "HIGH"

    def test_respiratory_contraindication(self):
        meds = [make_med("ibuprofen")]
        condition = ConditionRecord(condition_code="J45", condition_name="Asthma", status="ACTIVE")
        patient = make_patient(conditions=[condition])
        rules = [_make_cond_rule("J45", "ibuprofen", "RESPIRATORY_CONTRAINDICATION", "MODERATE")]
        findings = contraindication_rules.evaluate_contraindications(meds, patient, rules)
        assert len(findings) == 1
        assert findings[0].type == "RESPIRATORY_CONTRAINDICATION"

    def test_renal_normal_does_not_trigger(self):
        meds = [make_med("metformin")]
        patient = make_patient(renal_status="NORMAL")
        rules = [_make_cond_rule("RENAL-IMPAIRED", "metformin", "RENAL_CONTRAINDICATION")]
        findings = contraindication_rules.evaluate_contraindications(meds, patient, rules)
        assert findings == []

    def test_renal_unknown_does_not_trigger(self):
        """UNKNOWN renal status must not trigger a renal rule."""
        meds = [make_med("metformin")]
        patient = make_patient(renal_status="UNKNOWN")
        rules = [_make_cond_rule("RENAL-IMPAIRED", "metformin", "RENAL_CONTRAINDICATION")]
        findings = contraindication_rules.evaluate_contraindications(meds, patient, rules)
        assert findings == []

    def test_g6pd_normal_does_not_trigger(self):
        meds = [make_med("sulfamethoxazole-trimethoprim")]
        patient = make_patient(g6pd_status="NORMAL")
        rules = [_make_cond_rule("G6PD-DEFICIENT", "sulfamethoxazole-trimethoprim",
                                  "G6PD_CONTRAINDICATION")]
        findings = contraindication_rules.evaluate_contraindications(meds, patient, rules)
        assert findings == []

    def test_empty_rules_raises_configuration_error(self):
        from app.core.exceptions import RuleConfigurationError
        with pytest.raises(RuleConfigurationError):
            contraindication_rules.evaluate_contraindications(
                [make_med("metformin")], make_patient(), []
            )


# ---------------------------------------------------------------------------
# age_based_rules
# ---------------------------------------------------------------------------


class TestEvaluateAgeBasedCaution:
    def _patient_aged(self, years: int, **kwargs) -> PatientContext:
        dob = (date.today() - timedelta(days=years * 365 + years // 4)).isoformat()
        return make_patient(date_of_birth=dob, **kwargs)

    def test_age_based_caution_diazepam_over_65(self):
        meds = [make_med("diazepam")]
        patient = self._patient_aged(73)
        findings = age_based_rules.evaluate_age_based_caution(meds, patient)
        assert len(findings) == 1
        assert findings[0].type == "AGE_BASED_CAUTION"
        assert findings[0].severity != "CONTRAINDICATED"

    def test_under_65_returns_empty(self):
        meds = [make_med("diazepam")]
        patient = self._patient_aged(40)
        findings = age_based_rules.evaluate_age_based_caution(meds, patient)
        assert findings == []

    def test_exactly_65_triggers(self):
        meds = [make_med("diazepam")]
        patient = self._patient_aged(65)
        findings = age_based_rules.evaluate_age_based_caution(meds, patient)
        assert len(findings) == 1

    def test_severity_never_contraindicated(self):
        meds = [make_med("diazepam")]
        patient = self._patient_aged(85)
        findings = age_based_rules.evaluate_age_based_caution(meds, patient)
        for f in findings:
            assert f.severity != "CONTRAINDICATED"

    def test_safe_drug_not_in_table_returns_empty(self):
        meds = [make_med("paracetamol")]
        patient = self._patient_aged(75)
        findings = age_based_rules.evaluate_age_based_caution(meds, patient)
        assert findings == []

    def test_amitriptyline_tca_caution(self):
        meds = [make_med("amitriptyline")]
        patient = self._patient_aged(70)
        findings = age_based_rules.evaluate_age_based_caution(meds, patient)
        assert len(findings) == 1
        assert findings[0].type == "AGE_BASED_CAUTION"


# ---------------------------------------------------------------------------
# duplicate_therapy_rules
# ---------------------------------------------------------------------------


class TestEvaluateDuplicateTherapy:
    def test_two_nsaids_triggers(self):
        meds = [make_med("ibuprofen"), make_med("naproxen")]
        findings = duplicate_therapy_rules.evaluate_duplicate_therapy(meds)
        assert len(findings) == 1
        assert findings[0].type == "DUPLICATE_THERAPY"
        assert "ibuprofen" in findings[0].medications
        assert "naproxen" in findings[0].medications

    def test_two_statins_triggers(self):
        meds = [make_med("atorvastatin"), make_med("simvastatin")]
        findings = duplicate_therapy_rules.evaluate_duplicate_therapy(meds)
        assert len(findings) == 1
        assert findings[0].type == "DUPLICATE_THERAPY"

    def test_different_classes_no_finding(self):
        meds = [make_med("metformin"), make_med("atorvastatin")]
        findings = duplicate_therapy_rules.evaluate_duplicate_therapy(meds)
        assert findings == []

    def test_single_drug_no_finding(self):
        findings = duplicate_therapy_rules.evaluate_duplicate_therapy([make_med("ibuprofen")])
        assert findings == []
