"""Seed script for OmniPharma demo database.

Creates all tables and populates the full synthetic patient set described
in `docs/10_Mock_Data_Expansion_Spec.md`: 12 fictional patients with
demographics, conditions, allergies, pregnancy status, renal/hepatic/G6PD
status, medication history, current prescriptions, inventory rows, and
deliberate scenarios covering at least six distinct comorbidity categories:

- PREGNANCY (Cynthia Wanjiku, patient 3)
- RENAL_CONTRAINDICATION + HYPERKALEMIA_RISK (Felix Ochieng, patient 6)
- HEPATIC_CONTRAINDICATION (David Mwangi, patient 4)
- RESPIRATORY_CONTRAINDICATION (Esther Njeri, patient 5)
- G6PD_CONTRAINDICATION (Peter Mutiso, patient 11)
- AGE_BASED_CAUTION (Mary Wambui, patient 12)
- ALLERGY_CROSS_REACTIVITY (John Kiptoo, patient 10, via penicillin allergy + amoxicillin)
- DRUG_DRUG_INTERACTION (existing warfarin + ibuprofen rule)

Run with:
    uv run python -m data.seed

Or as part of the startup CLI:
    uv run python data/seed.py
"""

import sys
import os

# Allow running as a script from the backend root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import create_all_tables, SessionLocal
from app.db.models import (
    Allergy,
    AllergyCrossReactivity,
    Condition,
    ConditionDrugContraindication,
    InteractionRule,
    Inventory,
    Medication,
    MedicationHistory,
    Patient,
    PregnancyDrugWarning,
    Prescription,
)


def seed() -> None:
    """Create all tables and populate the full synthetic demo dataset.

    Returns:
        None
    """
    create_all_tables()
    db = SessionLocal()

    try:
        # Only seed if the database is empty.
        if db.query(Patient).count() > 0:
            print("Database already seeded — skipping.")
            return

        # ------------------------------------------------------------------
        # Medications (20 base + 4 new)
        # ------------------------------------------------------------------
        meds_data = [
            # id  canonical_name                inn                           trade_name         form        strength
            ("metformin", "metformin", "Glucophage", "Tablet", "500 mg"),
            ("lisinopril", "lisinopril", "Zestril", "Tablet", "10 mg"),
            ("atorvastatin", "atorvastatin", "Lipitor", "Tablet", "20 mg"),
            ("warfarin", "warfarin", "Coumadin", "Tablet", "5 mg"),
            ("aspirin", "aspirin", "Aspirin", "Tablet", "75 mg"),
            ("amoxicillin", "amoxicillin", "Amoxil", "Capsule", "500 mg"),
            ("ibuprofen", "ibuprofen", "Brufen", "Tablet", "400 mg"),
            ("omeprazole", "omeprazole", "Prilosec", "Capsule", "20 mg"),
            ("salbutamol", "salbutamol", "Ventolin", "Inhaler", "100 mcg/dose"),
            ("prednisolone", "prednisolone", "Prednisolone", "Tablet", "5 mg"),
            ("amlodipine", "amlodipine", "Norvasc", "Tablet", "5 mg"),
            ("furosemide", "furosemide", "Lasix", "Tablet", "40 mg"),
            ("paracetamol", "paracetamol", "Panadol", "Tablet", "500 mg"),
            ("ciprofloxacin", "ciprofloxacin", "Ciprofloxacin", "Tablet", "500 mg"),
            ("doxycycline", "doxycycline", "Vibramycin", "Capsule", "100 mg"),
            ("glibenclamide", "glibenclamide", "Daonil", "Tablet", "5 mg"),
            ("metoprolol", "metoprolol", "Lopressor", "Tablet", "50 mg"),
            ("simvastatin", "simvastatin", "Zocor", "Tablet", "20 mg"),
            ("isotretinoin", "isotretinoin", "Roaccutane", "Capsule", "10 mg"),
            ("phenytoin", "phenytoin", "Dilantin", "Tablet", "100 mg"),
            # New medications (spec Section 4)
            ("sulfamethoxazole-trimethoprim", "sulfamethoxazole-trimethoprim", "Co-trimoxazole", "Tablet", "800/160 mg"),
            ("nitrofurantoin", "nitrofurantoin", "Nitrofurantoin", "Capsule", "100 mg"),
            ("diazepam", "diazepam", "Diazepam", "Tablet", "5 mg"),
            ("spironolactone", "spironolactone", "Spironolactone", "Tablet", "25 mg"),
        ]

        med_objects: dict[str, Medication] = {}
        for row in meds_data:
            canonical, inn, trade, form, strength = row
            med = Medication(
                canonical_name=canonical,
                inn=inn,
                trade_name=trade,
                dosage_form=form,
                strength=strength,
                source="synthetic demo",
            )
            db.add(med)
            med_objects[canonical] = med

        db.flush()  # Assign IDs.

        # ------------------------------------------------------------------
        # Patients (12 total)
        # ------------------------------------------------------------------
        patients_data = [
            # code, name, dob, sex, pregnancy, renal, hepatic, g6pd
            ("OMNI-001", "Alice Kamau", "1985-03-15", "F", "PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-002", "Brian Omondi", "1978-07-22", "M", "NOT_APPLICABLE", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-003", "Cynthia Wanjiku", "1996-11-05", "F", "PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-004", "David Mwangi", "1965-04-18", "M", "NOT_APPLICABLE", "NORMAL", "MODERATE_IMPAIRMENT", "NORMAL"),
            ("OMNI-005", "Esther Njeri", "1990-09-30", "F", "NOT_PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-006", "Felix Ochieng", "1958-02-14", "M", "NOT_APPLICABLE", "MODERATE_IMPAIRMENT", "NORMAL", "UNKNOWN"),
            ("OMNI-007", "Grace Akinyi", "2002-06-25", "F", "NOT_PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-008", "Hassan Ali", "1945-12-01", "M", "NOT_APPLICABLE", "MILD_IMPAIRMENT", "NORMAL", "NORMAL"),
            ("OMNI-009", "Irene Mukhwana", "1972-08-19", "F", "NOT_PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-010", "John Kiptoo", "1980-01-10", "M", "NOT_APPLICABLE", "NORMAL", "NORMAL", "NORMAL"),
            # New patients (spec Section 6)
            ("OMNI-011", "Peter Mutiso", "1994-05-02", "M", "NOT_APPLICABLE", "NORMAL", "NORMAL", "DEFICIENT"),
            ("OMNI-012", "Mary Wambui", "1953-03-19", "F", "NOT_PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
        ]

        patient_objects: list[Patient] = []
        for row in patients_data:
            code, name, dob, sex, preg, renal, hepatic, g6pd = row
            p = Patient(
                patient_code=code,
                name=name,
                date_of_birth=dob,
                sex=sex,
                pregnancy_status=preg,
                renal_status=renal,
                hepatic_status=hepatic,
                g6pd_status=g6pd,
            )
            db.add(p)
            patient_objects.append(p)

        db.flush()

        def pid(code: str) -> int:
            for p in patient_objects:
                if p.patient_code == code:
                    return p.id
            raise ValueError(f"Patient {code} not found")

        def mid(name: str) -> int:
            return med_objects[name].id

        # ------------------------------------------------------------------
        # Conditions
        # ------------------------------------------------------------------
        conditions_data = [
            # patient_code, icd_code, name, status, onset
            ("OMNI-001", "Z34", "Normal pregnancy", "ACTIVE", "2026-01-15"),
            ("OMNI-003", "Z34", "Normal pregnancy", "ACTIVE", "2026-05-01"),
            ("OMNI-004", "K72", "Hepatic failure (chronic)", "ACTIVE", "2020-03-10"),
            ("OMNI-004", "E11", "Type 2 diabetes mellitus", "ACTIVE", "2015-06-20"),
            ("OMNI-005", "J45", "Asthma", "ACTIVE", "2008-04-12"),
            ("OMNI-006", "N18", "Chronic kidney disease stage 3", "ACTIVE", "2018-09-05"),
            ("OMNI-006", "E11", "Type 2 diabetes mellitus", "ACTIVE", "2016-11-20"),
            ("OMNI-007", "J06", "Upper respiratory tract infection", "ACTIVE", "2026-09-20"),
            ("OMNI-008", "I10", "Essential hypertension", "ACTIVE", "2000-01-01"),
            ("OMNI-009", "E11", "Type 2 diabetes mellitus", "ACTIVE", "2012-05-15"),
            ("OMNI-010", "I48", "Atrial fibrillation", "ACTIVE", "2019-03-22"),
            ("OMNI-011", "N39", "Urinary tract infection", "ACTIVE", "2026-09-20"),
            ("OMNI-012", "I10", "Hypertension", "ACTIVE", "2015-06-01"),
        ]
        for code, icd, name, status, onset in conditions_data:
            db.add(Condition(
                patient_id=pid(code),
                condition_code=icd,
                condition_name=name,
                status=status,
                onset_date=onset,
            ))

        # ------------------------------------------------------------------
        # Allergies
        # ------------------------------------------------------------------
        allergies_data = [
            # patient_code, allergen, reaction, severity
            ("OMNI-001", "none", "none", "NONE"),
            ("OMNI-002", "none", "none", "NONE"),
            ("OMNI-003", "none", "none", "NONE"),
            ("OMNI-004", "none", "none", "NONE"),
            ("OMNI-005", "none", "none", "NONE"),
            ("OMNI-006", "none", "none", "NONE"),
            ("OMNI-007", "none", "none", "NONE"),
            ("OMNI-008", "sulfonamide", "Rash and urticaria", "MODERATE"),
            ("OMNI-009", "none", "none", "NONE"),
            ("OMNI-010", "penicillin", "Anaphylaxis", "SEVERE"),
            ("OMNI-011", "none", "none", "NONE"),
            ("OMNI-012", "none", "none", "NONE"),
        ]
        for code, allergen, reaction, severity in allergies_data:
            db.add(Allergy(
                patient_id=pid(code),
                allergen=allergen,
                reaction=reaction,
                severity=severity,
            ))

        # ------------------------------------------------------------------
        # Active Prescriptions
        # ------------------------------------------------------------------
        prescriptions_data = [
            # patient_code, medication_canonical, dose, freq, route, start, end, status
            # Alice — pregnant, check warfarin
            ("OMNI-001", "warfarin", "5 mg", "once daily", "oral", "2026-08-01", None, "ACTIVE"),
            ("OMNI-001", "aspirin", "75 mg", "once daily", "oral", "2026-08-01", None, "ACTIVE"),
            # Brian — no risk
            ("OMNI-002", "amlodipine", "5 mg", "once daily", "oral", "2026-07-01", None, "ACTIVE"),
            # Cynthia — pregnant + isotretinoin (CONTRAINDICATED)
            ("OMNI-003", "isotretinoin", "10 mg", "once daily", "oral", "2026-06-01", None, "ACTIVE"),
            ("OMNI-003", "lisinopril", "10 mg", "once daily", "oral", "2026-06-01", None, "ACTIVE"),
            # David — hepatic impairment + atorvastatin
            ("OMNI-004", "atorvastatin", "20 mg", "once daily", "oral", "2021-01-01", None, "ACTIVE"),
            ("OMNI-004", "metformin", "500 mg", "twice daily", "oral", "2015-06-20", None, "ACTIVE"),
            # Esther — asthma + ibuprofen (RESPIRATORY_CONTRAINDICATION)
            ("OMNI-005", "salbutamol", "100 mcg", "as needed", "inhaled", "2008-04-12", None, "ACTIVE"),
            ("OMNI-005", "ibuprofen", "400 mg", "as needed", "oral", "2026-09-01", None, "ACTIVE"),
            # Felix — CKD + metformin (RENAL) + lisinopril (HYPERKALEMIA)
            ("OMNI-006", "metformin", "500 mg", "twice daily", "oral", "2016-11-20", None, "ACTIVE"),
            ("OMNI-006", "lisinopril", "10 mg", "once daily", "oral", "2026-08-15", None, "ACTIVE"),
            # Grace — no risk
            ("OMNI-007", "paracetamol", "500 mg", "four times daily", "oral", "2026-09-20", "2026-09-27", "ACTIVE"),
            # Hassan — hypertension, mild renal
            ("OMNI-008", "amlodipine", "5 mg", "once daily", "oral", "2010-01-01", None, "ACTIVE"),
            ("OMNI-008", "metoprolol", "50 mg", "twice daily", "oral", "2010-01-01", None, "ACTIVE"),
            # Irene — diabetes
            ("OMNI-009", "metformin", "500 mg", "twice daily", "oral", "2012-05-15", None, "ACTIVE"),
            ("OMNI-009", "glibenclamide", "5 mg", "once daily", "oral", "2015-06-01", None, "ACTIVE"),
            # John — AF + warfarin + penicillin allergy (cross-reactivity with amoxicillin)
            ("OMNI-010", "warfarin", "5 mg", "once daily", "oral", "2019-03-22", None, "ACTIVE"),
            ("OMNI-010", "amoxicillin", "500 mg", "three times daily", "oral", "2026-09-20", "2026-09-27", "ACTIVE"),
            # Peter — G6PD deficient + co-trimoxazole (G6PD_CONTRAINDICATION)
            ("OMNI-011", "sulfamethoxazole-trimethoprim", "800/160 mg", "twice daily", "oral", "2026-09-20", "2026-09-25", "ACTIVE"),
            # Mary — age 73 + diazepam (AGE_BASED_CAUTION)
            ("OMNI-012", "diazepam", "5 mg", "at night", "oral", "2026-09-01", None, "ACTIVE"),
        ]
        for code, med_name, dose, freq, route, start, end, status in prescriptions_data:
            db.add(Prescription(
                patient_id=pid(code),
                medication_id=mid(med_name),
                dose=dose,
                frequency=freq,
                route=route,
                start_date=start,
                end_date=end,
                status=status,
            ))

        # ------------------------------------------------------------------
        # Medication History
        # ------------------------------------------------------------------
        history_data = [
            # patient_code, med, dose, freq, start, end, outcome
            ("OMNI-001", "paracetamol", "500 mg", "as needed", "2025-01-01", "2025-03-01", "Resolved"),
            ("OMNI-003", "omeprazole", "20 mg", "once daily", "2025-06-01", "2025-09-01", "Completed"),
            ("OMNI-004", "simvastatin", "20 mg", "once daily", "2018-01-01", "2021-01-01", "Switched to atorvastatin"),
            ("OMNI-006", "furosemide", "40 mg", "once daily", "2019-01-01", "2022-01-01", "Discontinued — electrolyte imbalance"),
            ("OMNI-010", "aspirin", "75 mg", "once daily", "2015-01-01", "2019-03-22", "Switched to warfarin on AF diagnosis"),
        ]
        for code, med_name, dose, freq, start, end, outcome in history_data:
            db.add(MedicationHistory(
                patient_id=pid(code),
                medication_id=mid(med_name),
                dose=dose,
                frequency=freq,
                start_date=start,
                end_date=end,
                outcome=outcome,
            ))

        # ------------------------------------------------------------------
        # Inventory
        # ------------------------------------------------------------------
        facility = "Demo Hospital Pharmacy"
        inventory_quantities = {
            "metformin": 200,
            "lisinopril": 150,
            "atorvastatin": 120,
            "warfarin": 80,
            "aspirin": 300,
            "amoxicillin": 180,
            "ibuprofen": 250,
            "omeprazole": 200,
            "salbutamol": 60,
            "prednisolone": 100,
            "amlodipine": 140,
            "furosemide": 90,
            "paracetamol": 500,
            "ciprofloxacin": 120,
            "doxycycline": 100,
            "glibenclamide": 80,
            "metoprolol": 110,
            "simvastatin": 100,
            "isotretinoin": 40,
            "phenytoin": 60,
            "sulfamethoxazole-trimethoprim": 40,
            "nitrofurantoin": 35,
            "diazepam": 50,
            "spironolactone": 45,
        }
        for med_name, qty in inventory_quantities.items():
            db.add(Inventory(
                medication_id=mid(med_name),
                quantity=qty,
                facility=facility,
                updated_at="2026-09-27T09:00:00",
            ))

        # ------------------------------------------------------------------
        # Interaction Rules
        # ------------------------------------------------------------------
        interaction_rules = [
            ("warfarin", "ibuprofen", "HIGH",
             "NSAIDs inhibit platelet aggregation and can displace warfarin from plasma proteins, "
             "raising INR and increasing the risk of bleeding.",
             "Monitor INR closely; consider paracetamol for analgesia. Avoid NSAIDs where possible.",
             "Demo rule", "demo-1.0"),
            ("warfarin", "aspirin", "MODERATE",
             "Aspirin has antiplatelet activity; combined with warfarin the risk of bleeding is increased.",
             "Monitor INR; use lowest effective aspirin dose; assess bleeding risk.",
             "Demo rule", "demo-1.0"),
            ("metformin", "furosemide", "LOW",
             "Loop diuretics may impair renal function and increase metformin accumulation risk.",
             "Monitor renal function regularly when combining.",
             "Demo rule", "demo-1.0"),
            ("lisinopril", "spironolactone", "HIGH",
             "Dual renin-angiotensin-aldosterone blockade markedly increases hyperkalemia risk, "
             "particularly in patients with impaired renal function.",
             "Monitor serum potassium and creatinine frequently; avoid unless under specialist supervision.",
             "Demo rule", "demo-1.0"),
            ("metoprolol", "amlodipine", "LOW",
             "Combined negative chronotropic and inotropic effects may excessively slow the heart rate.",
             "Monitor heart rate and blood pressure; dose adjustments may be required.",
             "Demo rule", "demo-1.0"),
            ("phenytoin", "warfarin", "MODERATE",
             "Phenytoin induces CYP2C9, increasing warfarin metabolism and potentially reducing anticoagulant effect; "
             "displacement interactions can also transiently raise free warfarin levels.",
             "Monitor INR closely when initiating, adjusting, or stopping phenytoin.",
             "Demo rule", "demo-1.0"),
            ("ciprofloxacin", "warfarin", "MODERATE",
             "Fluoroquinolones inhibit CYP1A2 and may reduce gut flora that produce vitamin K, "
             "potentiating warfarin anticoagulation.",
             "Monitor INR during and shortly after a fluoroquinolone course.",
             "Demo rule", "demo-1.0"),
            ("glibenclamide", "ciprofloxacin", "MODERATE",
             "Fluoroquinolones can cause dysglycaemia, both hypoglycaemia and hyperglycaemia, "
             "particularly with sulfonylureas.",
             "Monitor blood glucose carefully during concurrent use.",
             "Demo rule", "demo-1.0"),
        ]
        for drug_a, drug_b, sev, mech, rec, src, ver in interaction_rules:
            db.add(InteractionRule(
                drug_a=drug_a,
                drug_b=drug_b,
                severity=sev,
                mechanism=mech,
                recommendation=rec,
                source=src,
                version=ver,
            ))

        # ------------------------------------------------------------------
        # Pregnancy Drug Warnings
        # ------------------------------------------------------------------
        pregnancy_warnings = [
            ("isotretinoin", "ALL", "CONTRAINDICATED",
             "Isotretinoin is a known human teratogen causing embryopathy, craniofacial, "
             "cardiac, and CNS malformations.",
             "Absolutely contraindicated in pregnancy; confirm pregnancy status and contraception before any use.",
             "Demo rule", "demo-1.0"),
            ("warfarin", "ALL", "HIGH",
             "Warfarin crosses the placenta and is associated with fetal warfarin syndrome "
             "(nasal hypoplasia, stippled epiphyses, optic atrophy, mental retardation).",
             "Avoid; consider alternative anticoagulation and obstetric review.",
             "Demo rule", "demo-1.0"),
            ("lisinopril", "SECOND", "HIGH",
             "ACE inhibitors are associated with fetal renal tubular dysplasia and hypocalvaria "
             "in the second and third trimester.",
             "Avoid; switch to a pregnancy-appropriate antihypertensive.",
             "Demo rule", "demo-1.0"),
            ("ibuprofen", "THIRD", "HIGH",
             "NSAIDs in the third trimester are associated with premature closure of the ductus arteriosus "
             "and oligohydramnios.",
             "Avoid NSAIDs in the third trimester; use paracetamol where appropriate.",
             "Demo rule", "demo-1.0"),
            ("doxycycline", "ALL", "HIGH",
             "Tetracyclines bind calcium and are deposited in fetal bone and teeth, causing staining "
             "and skeletal abnormalities.",
             "Avoid throughout pregnancy; use an alternative antibiotic.",
             "Demo rule", "demo-1.0"),
            ("phenytoin", "ALL", "HIGH",
             "Phenytoin is associated with fetal hydantoin syndrome (digit/nail hypoplasia, "
             "craniofacial features, cognitive impairment).",
             "Continue only if seizure risk outweighs teratogenic risk; use lowest effective dose "
             "with specialist review.",
             "Demo rule", "demo-1.0"),
        ]
        for drug, scope, sev, mech, rec, src, ver in pregnancy_warnings:
            db.add(PregnancyDrugWarning(
                drug_name=drug,
                trimester_scope=scope,
                severity=sev,
                mechanism=mech,
                recommendation=rec,
                source=src,
                version=ver,
            ))

        # ------------------------------------------------------------------
        # Condition-Drug Contraindications
        # ------------------------------------------------------------------
        contraindications = [
            # Renal (pseudo-code)
            ("RENAL-IMPAIRED", "metformin", "RENAL_CONTRAINDICATION", "HIGH",
             "Reduced renal clearance increases metformin accumulation and lactic acidosis risk.",
             "Avoid or dose-adjust per renal function; consider alternative glucose-lowering agent.",
             "Demo rule", "demo-1.0"),
            ("RENAL-IMPAIRED", "ibuprofen", "RENAL_CONTRAINDICATION", "HIGH",
             "NSAIDs reduce renal perfusion and can worsen existing renal impairment.",
             "Avoid NSAIDs; use paracetamol for analgesia where appropriate.",
             "Demo rule", "demo-1.0"),
            ("RENAL-IMPAIRED", "nitrofurantoin", "RENAL_CONTRAINDICATION", "HIGH",
             "Nitrofurantoin requires adequate renal function for urinary concentration; "
             "reduced clearance also causes systemic accumulation and peripheral neuropathy.",
             "Avoid in moderate-to-severe renal impairment (eGFR <30); select an alternative.",
             "Demo rule", "demo-1.0"),

            # Hepatic (pseudo-code)
            ("HEPATIC-IMPAIRED", "atorvastatin", "HEPATIC_CONTRAINDICATION", "MODERATE",
             "Statins are hepatically metabolized; impairment raises exposure and hepatotoxicity risk.",
             "Use the lowest effective dose and monitor liver function.",
             "Demo rule", "demo-1.0"),
            ("HEPATIC-IMPAIRED", "paracetamol", "HEPATIC_CONTRAINDICATION", "MODERATE",
             "Reduced hepatic reserve lowers the safety margin for paracetamol-related hepatotoxicity.",
             "Reduce maximum daily dose and monitor; avoid other hepatotoxic agents concurrently.",
             "Demo rule", "demo-1.0"),
            ("HEPATIC-IMPAIRED", "metformin", "HEPATIC_CONTRAINDICATION", "MODERATE",
             "Hepatic impairment increases lactic acidosis risk with metformin due to impaired lactate metabolism.",
             "Avoid in significant hepatic impairment; monitor liver function if used.",
             "Demo rule", "demo-1.0"),

            # Hyperkalemia risk (real ICD code N18: CKD)
            ("N18", "lisinopril", "HYPERKALEMIA_RISK", "MODERATE",
             "ACE inhibition reduces potassium excretion; risk is compounded by existing renal impairment.",
             "Check serum potassium before and after initiation; monitor renal function.",
             "Demo rule", "demo-1.0"),
            ("N18", "spironolactone", "HYPERKALEMIA_RISK", "HIGH",
             "Potassium-sparing diuretics combined with reduced renal clearance markedly raise hyperkalemia risk.",
             "Avoid unless potassium is closely monitored; consider alternative diuretic.",
             "Demo rule", "demo-1.0"),

            # G6PD (pseudo-code)
            ("G6PD-DEFICIENT", "sulfamethoxazole-trimethoprim", "G6PD_CONTRAINDICATION", "HIGH",
             "Sulfonamides are oxidative agents that can trigger acute hemolysis in G6PD deficiency.",
             "Avoid; select a non-oxidative antibiotic alternative.",
             "Demo rule", "demo-1.0"),
            ("G6PD-DEFICIENT", "nitrofurantoin", "G6PD_CONTRAINDICATION", "HIGH",
             "Nitrofurantoin is a recognized trigger of hemolysis in G6PD-deficient patients.",
             "Avoid; select a non-oxidative alternative for urinary tract infection.",
             "Demo rule", "demo-1.0"),
            ("G6PD-DEFICIENT", "doxycycline", "G6PD_CONTRAINDICATION", "MODERATE",
             "Doxycycline can cause oxidative stress and has been associated with hemolysis in "
             "G6PD-deficient patients, though risk is lower than sulfonamides.",
             "Use with caution; consider an alternative antibiotic if clinically feasible.",
             "Demo rule", "demo-1.0"),

            # Respiratory (ICD J45: asthma)
            ("J45", "ibuprofen", "RESPIRATORY_CONTRAINDICATION", "MODERATE",
             "NSAIDs can precipitate bronchospasm in aspirin/NSAID-exacerbated respiratory disease.",
             "Avoid NSAIDs where a history of NSAID-exacerbated respiratory symptoms exists; "
             "use paracetamol.",
             "Demo rule", "demo-1.0"),
            ("J45", "aspirin", "RESPIRATORY_CONTRAINDICATION", "MODERATE",
             "Aspirin sensitivity is common in asthma; aspirin-exacerbated respiratory disease "
             "(AERD/Samter's triad) can cause severe bronchospasm.",
             "Screen for NSAID/aspirin sensitivity; avoid if any history of bronchospasm with these agents.",
             "Demo rule", "demo-1.0"),
            ("J45", "metoprolol", "RESPIRATORY_CONTRAINDICATION", "LOW",
             "Non-cardioselective beta-blockers are contraindicated in asthma; cardioselective agents "
             "like metoprolol carry lower risk but should still be used with caution.",
             "Prefer non-beta-blocker antihypertensives if possible; if essential, use a cardioselective "
             "beta-blocker at the lowest effective dose with spirometry monitoring.",
             "Demo rule", "demo-1.0"),
        ]
        for cond, drug, ftype, sev, mech, rec, src, ver in contraindications:
            db.add(ConditionDrugContraindication(
                condition_code=cond,
                drug_name=drug,
                finding_type=ftype,
                severity=sev,
                mechanism=mech,
                recommendation=rec,
                source=src,
                version=ver,
            ))

        # ------------------------------------------------------------------
        # Allergy Cross-Reactivity Rules
        # ------------------------------------------------------------------
        cross_reactivity = [
            ("penicillin", "amoxicillin",
             "Amoxicillin shares the beta-lactam ring structure responsible for penicillin allergy; "
             "cross-reactivity rate estimated at 1–10%.",
             "HIGH", "Demo rule", "demo-1.0"),
            ("penicillin", "ampicillin",
             "Ampicillin is an aminopenicillin and shares the beta-lactam and side-chain structure "
             "with penicillin.",
             "HIGH", "Demo rule", "demo-1.0"),
            ("penicillin", "cloxacillin",
             "Cloxacillin is a penicillinase-resistant penicillin; shares the beta-lactam core.",
             "MODERATE", "Demo rule", "demo-1.0"),
            ("amoxicillin", "penicillin",
             "Amoxicillin and penicillin share the beta-lactam ring structure.",
             "MODERATE", "Demo rule", "demo-1.0"),
            ("sulfonamide", "sulfamethoxazole-trimethoprim",
             "Co-trimoxazole contains a sulfonamide moiety (sulfamethoxazole); patients with a "
             "sulfonamide allergy are at risk of cross-reactive reactions.",
             "HIGH", "Demo rule", "demo-1.0"),
            ("sulfonamide", "doxycycline",
             "Doxycycline is not a sulfonamide and does not share the implicated N4 amine group; "
             "this is a low-risk pairing.",
             "LOW", "Demo rule", "demo-1.0"),
        ]
        for allergen, cross_drug, mech, sev, src, ver in cross_reactivity:
            db.add(AllergyCrossReactivity(
                allergen=allergen,
                cross_reactive_drug=cross_drug,
                mechanism=mech,
                severity=sev,
                source=src,
                version=ver,
            ))

        db.commit()
        print("[OK] OmniPharma demo database seeded successfully.")
        print(f"   Patients: {db.query(Patient).count()}")
        print(f"   Medications: {db.query(Medication).count()}")
        print(f"   Interaction rules: {db.query(InteractionRule).count()}")
        print(f"   Pregnancy warnings: {db.query(PregnancyDrugWarning).count()}")
        print(f"   Condition contraindications: {db.query(ConditionDrugContraindication).count()}")
        print(f"   Cross-reactivity rules: {db.query(AllergyCrossReactivity).count()}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
