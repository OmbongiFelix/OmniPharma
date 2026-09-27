**OmniPharma — Mock Data Expansion Spec**

_Fixes two data bugs found in `07_mock_patients.db`, adds the three tables required by `BACKEND_DEVELOPER_REFERENCE.md`, and adds enough new data that at least six distinct non-pregnancy comorbidity categories each produce a real, demonstrable finding — not just pregnancy._

# 1. Bugs found in the supplied `07_mock_patients.db`

Both are in the `patients` table and are worth fixing regardless of the rest of this spec, since they'd misrepresent two patients in a live demo.

1. **Patient 6 (Felix Ochieng, male, diagnosed with chronic kidney disease, condition `N18`)** has `pregnancy_status = 'MODERATE_IMPAIRMENT'` and `renal_status = 'NORMAL'`. `MODERATE_IMPAIRMENT` is not a valid pregnancy status value anywhere else in the dataset — this looks like the intended renal-status value landed one column to the left. A male CKD patient showing `renal_status: NORMAL` also directly contradicts his own diagnosis.
2. **Patient 8 (Hassan Ali, male)** has `pregnancy_status = 'NORMAL'`, which isn't one of the three valid values used elsewhere (`PREGNANT`, `NOT_PREGNANT`, `NOT_APPLICABLE`).

Fix:
```sql
UPDATE patients SET pregnancy_status = 'NOT_APPLICABLE', renal_status = 'MODERATE_IMPAIRMENT' WHERE id = 6;
UPDATE patients SET pregnancy_status = 'NOT_APPLICABLE' WHERE id = 8;
```

# 2. New column: G6PD status

```sql
ALTER TABLE patients ADD COLUMN g6pd_status TEXT NOT NULL DEFAULT 'UNKNOWN';
```

Set it explicitly for the existing 10 patients (all `UNKNOWN` is a legitimate real-world default — we only know G6PD status where it's actually been tested):
```sql
UPDATE patients SET g6pd_status = 'NORMAL' WHERE id IN (1,2,3,4,5,7,8,9,10);
UPDATE patients SET g6pd_status = 'UNKNOWN' WHERE id = 6;
```

# 3. New tables

```sql
CREATE TABLE pregnancy_drug_warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_name TEXT NOT NULL,
    trimester_scope TEXT NOT NULL DEFAULT 'ALL',
    severity TEXT NOT NULL,
    mechanism TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    source TEXT,
    version TEXT NOT NULL
);

CREATE TABLE condition_drug_contraindications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition_code TEXT NOT NULL,
    drug_name TEXT NOT NULL,
    finding_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    mechanism TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    source TEXT,
    version TEXT NOT NULL
);

CREATE TABLE allergy_cross_reactivity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    allergen TEXT NOT NULL,
    cross_reactive_drug TEXT NOT NULL,
    mechanism TEXT NOT NULL,
    severity TEXT NOT NULL,
    source TEXT,
    version TEXT NOT NULL
);
```

`condition_drug_contraindications.condition_code` matches either a real diagnosis code from the `conditions` table (e.g. `J45` for asthma) or one of three reserved pseudo-codes derived from the patient row itself: `RENAL-IMPAIRED`, `HEPATIC-IMPAIRED`, `G6PD-DEFICIENT` (see `BACKEND_DEVELOPER_REFERENCE.md`, `contraindication_rules.py` Notes).

# 4. New medications

```sql
INSERT INTO medications (canonical_name, inn, trade_name, dosage_form, strength, source) VALUES
('sulfamethoxazole-trimethoprim', 'sulfamethoxazole-trimethoprim', 'Co-trimoxazole', 'Tablet', '800/160 mg', 'synthetic demo'),
('nitrofurantoin', 'nitrofurantoin', 'Nitrofurantoin', 'Capsule', '100 mg', 'synthetic demo'),
('diazepam', 'diazepam', 'Diazepam', 'Tablet', '5 mg', 'synthetic demo'),
('spironolactone', 'spironolactone', 'Spironolactone', 'Tablet', '25 mg', 'synthetic demo');
```
(IDs will follow on from the existing 20 rows — 21, 22, 23, 24. Adjust prescription inserts below if your copy of the seed already has different IDs.)

# 5. New contraindication/warning rule rows

```sql
-- Pregnancy (kept, but no longer the only category with data behind it)
INSERT INTO pregnancy_drug_warnings (drug_name, trimester_scope, severity, mechanism, recommendation, source, version) VALUES
('isotretinoin', 'ALL', 'CONTRAINDICATED', 'Isotretinoin is a known human teratogen.', 'Absolutely contraindicated in pregnancy; confirm pregnancy status and contraception before any use.', 'Demo rule', 'demo-1.0'),
('warfarin', 'ALL', 'HIGH', 'Warfarin crosses the placenta and is associated with fetal warfarin syndrome.', 'Avoid; consider alternative anticoagulation and obstetric review.', 'Demo rule', 'demo-1.0'),
('lisinopril', 'SECOND', 'HIGH', 'ACE inhibitors are associated with fetopathy in the second and third trimester.', 'Avoid; switch to a pregnancy-appropriate antihypertensive.', 'Demo rule', 'demo-1.0');

-- Renal (reserved pseudo-code)
INSERT INTO condition_drug_contraindications (condition_code, drug_name, finding_type, severity, mechanism, recommendation, source, version) VALUES
('RENAL-IMPAIRED', 'metformin', 'RENAL_CONTRAINDICATION', 'HIGH', 'Reduced renal clearance increases metformin accumulation and lactic acidosis risk.', 'Avoid or dose-adjust per renal function; consider alternative glucose-lowering agent.', 'Demo rule', 'demo-1.0'),
('RENAL-IMPAIRED', 'ibuprofen', 'RENAL_CONTRAINDICATION', 'HIGH', 'NSAIDs reduce renal perfusion and can worsen existing renal impairment.', 'Avoid NSAIDs; use paracetamol for analgesia where appropriate.', 'Demo rule', 'demo-1.0');

-- Hepatic (reserved pseudo-code)
INSERT INTO condition_drug_contraindications (condition_code, drug_name, finding_type, severity, mechanism, recommendation, source, version) VALUES
('HEPATIC-IMPAIRED', 'atorvastatin', 'HEPATIC_CONTRAINDICATION', 'MODERATE', 'Statins are hepatically metabolized; impairment raises exposure and hepatotoxicity risk.', 'Use the lowest effective dose and monitor liver function.', 'Demo rule', 'demo-1.0'),
('HEPATIC-IMPAIRED', 'paracetamol', 'HEPATIC_CONTRAINDICATION', 'MODERATE', 'Reduced hepatic reserve lowers the safety margin for paracetamol-related hepatotoxicity.', 'Reduce maximum daily dose and monitor; avoid other hepatotoxic agents concurrently.', 'Demo rule', 'demo-1.0');

-- Hyperkalemia risk (real condition code: N18 chronic kidney disease)
INSERT INTO condition_drug_contraindications (condition_code, drug_name, finding_type, severity, mechanism, recommendation, source, version) VALUES
('N18', 'lisinopril', 'HYPERKALEMIA_RISK', 'MODERATE', 'ACE inhibition reduces potassium excretion; risk is compounded by existing renal impairment.', 'Check serum potassium before and after initiation; monitor renal function.', 'Demo rule', 'demo-1.0'),
('N18', 'spironolactone', 'HYPERKALEMIA_RISK', 'HIGH', 'Potassium-sparing diuretics combined with reduced renal clearance markedly raise hyperkalemia risk.', 'Avoid unless potassium is closely monitored; consider alternative diuretic.', 'Demo rule', 'demo-1.0');

-- G6PD (reserved pseudo-code)
INSERT INTO condition_drug_contraindications (condition_code, drug_name, finding_type, severity, mechanism, recommendation, source, version) VALUES
('G6PD-DEFICIENT', 'sulfamethoxazole-trimethoprim', 'G6PD_CONTRAINDICATION', 'HIGH', 'Sulfonamides are oxidative agents that can trigger acute hemolysis in G6PD deficiency.', 'Avoid; select a non-oxidative antibiotic alternative.', 'Demo rule', 'demo-1.0'),
('G6PD-DEFICIENT', 'nitrofurantoin', 'G6PD_CONTRAINDICATION', 'HIGH', 'Nitrofurantoin is a recognized trigger of hemolysis in G6PD-deficient patients.', 'Avoid; select a non-oxidative alternative for urinary tract infection.', 'Demo rule', 'demo-1.0');

-- Respiratory (real condition code: J45 asthma)
INSERT INTO condition_drug_contraindications (condition_code, drug_name, finding_type, severity, mechanism, recommendation, source, version) VALUES
('J45', 'ibuprofen', 'RESPIRATORY_CONTRAINDICATION', 'MODERATE', 'NSAIDs can precipitate bronchospasm in aspirin/NSAID-exacerbated respiratory disease.', 'Avoid NSAIDs where a history of NSAID-exacerbated respiratory symptoms exists; use paracetamol.', 'Demo rule', 'demo-1.0');

-- Allergy cross-reactivity
INSERT INTO allergy_cross_reactivity (allergen, cross_reactive_drug, mechanism, severity, source, version) VALUES
('penicillin', 'amoxicillin', 'Amoxicillin shares the beta-lactam ring structure responsible for penicillin allergy.', 'HIGH', 'Demo rule', 'demo-1.0'),
('penicillin', 'penicillin', 'Direct allergen match.', 'HIGH', 'Demo rule', 'demo-1.0'),
('amoxicillin', 'penicillin', 'Amoxicillin and penicillin share the beta-lactam ring structure.', 'MODERATE', 'Demo rule', 'demo-1.0');
```

# 6. New patients (to reach six non-pregnancy comorbidity categories without overloading existing patients)

```sql
INSERT INTO patients (patient_code, name, date_of_birth, sex, pregnancy_status, renal_status, hepatic_status, g6pd_status) VALUES
('OMNI-011', 'Peter Mutiso', '1994-05-02', 'M', 'NOT_APPLICABLE', 'NORMAL', 'NORMAL', 'DEFICIENT'),
('OMNI-012', 'Mary Wambui', '1953-03-19', 'F', 'NOT_PREGNANT', 'NORMAL', 'NORMAL', 'NORMAL');

-- Conditions
INSERT INTO conditions (patient_id, condition_code, condition_name, status, onset_date) VALUES
(11, 'N39', 'Urinary tract infection', 'ACTIVE', '2026-09-20'),
(12, 'I10', 'Hypertension', 'ACTIVE', '2015-06-01');

-- Allergies (none recorded for either)
INSERT INTO allergies (patient_id, allergen, reaction, severity) VALUES
(11, 'none', 'none', 'NONE'),
(12, 'none', 'none', 'NONE');

-- Prescriptions: G6PD-deficient patient given co-trimoxazole for a UTI -> G6PD_CONTRAINDICATION
INSERT INTO prescriptions (patient_id, medication_id, dose, frequency, route, start_date, end_date, status, prescriber) VALUES
(11, (SELECT id FROM medications WHERE canonical_name = 'sulfamethoxazole-trimethoprim'), '800/160 mg', 'twice daily', 'oral', '2026-09-20', '2026-09-25', 'ACTIVE', 'Demo Clinic');

-- Prescriptions: elderly patient (age 73) given a long-acting benzodiazepine -> AGE_BASED_CAUTION
INSERT INTO prescriptions (patient_id, medication_id, dose, frequency, route, start_date, end_date, status, prescriber) VALUES
(12, (SELECT id FROM medications WHERE canonical_name = 'diazepam'), '5 mg', 'at night', 'oral', '2026-09-01', NULL, 'ACTIVE', 'Demo Clinic');

-- Add lisinopril to the existing CKD patient (id 6, Felix Ochieng) so one patient demonstrates
-- both RENAL_CONTRAINDICATION (already prescribed metformin) and HYPERKALEMIA_RISK
INSERT INTO prescriptions (patient_id, medication_id, dose, frequency, route, start_date, end_date, status, prescriber) VALUES
(6, (SELECT id FROM medications WHERE canonical_name = 'lisinopril'), '10 mg', 'once daily', 'oral', '2026-08-15', NULL, 'ACTIVE', 'Demo Renal');

-- Give the existing asthma patient (id 5, Esther Njeri) an NSAID -> RESPIRATORY_CONTRAINDICATION
INSERT INTO prescriptions (patient_id, medication_id, dose, frequency, route, start_date, end_date, status, prescriber) VALUES
(5, (SELECT id FROM medications WHERE canonical_name = 'ibuprofen'), '400 mg', 'as needed', 'oral', '2026-09-01', NULL, 'ACTIVE', 'Demo Respiratory');

-- Inventory rows for the new medications
INSERT INTO inventory (medication_id, quantity, facility, updated_at)
SELECT id, 40, 'Demo Hospital Pharmacy', '2026-09-27T09:00:00' FROM medications
WHERE canonical_name IN ('sulfamethoxazole-trimethoprim', 'nitrofurantoin', 'diazepam', 'spironolactone');
```

# 7. Resulting demo coverage

| Patient | Category demonstrated | Trigger |
|---|---|---|
| Cynthia Wanjiku (3) | `PREGNANCY` | Pregnancy status + isotretinoin/warfarin/lisinopril warning table |
| Felix Ochieng (6) | `RENAL_CONTRAINDICATION` **and** `HYPERKALEMIA_RISK` | Corrected renal status + metformin, and CKD condition + newly added lisinopril |
| David Mwangi (4) | `HEPATIC_CONTRAINDICATION` | Existing hepatic impairment + existing atorvastatin prescription |
| Esther Njeri (5) | `RESPIRATORY_CONTRAINDICATION` | Existing asthma condition + newly added ibuprofen prescription |
| Peter Mutiso (11, new) | `G6PD_CONTRAINDICATION` | New G6PD-deficient status + co-trimoxazole prescription |
| Mary Wambui (12, new) | `AGE_BASED_CAUTION` | Age 73 + diazepam prescription |
| Hassan Ali (8) or John Kiptoo (10) | `ALLERGY_CROSS_REACTIVITY` | Penicillin allergy + an amoxicillin prescription (already present for patient 10's medication history; add an active amoxicillin prescription if you want it live rather than historical) |

This gives seven distinct finding categories with real, traceable data behind them — pregnancy is one of seven, not the whole story.

# 8. Regenerating the database

Run the SQL in Sections 1–6, in order, against a copy of the supplied `07_mock_patients.db`:
```bash
cp 07_mock_patients.db OmniPharma/backend/data/omnipharm.db
sqlite3 OmniPharma/backend/data/omnipharm.db < expansion.sql
```
where `expansion.sql` is the concatenation of the SQL blocks above. Alternatively, hand this file directly to Antigravity as the seed source described in `05_Antigravity_Backend_Prompt.md`'s MOCK DATA section — either approach produces the same database.
