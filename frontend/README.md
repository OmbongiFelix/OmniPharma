# OmniPharma Frontend

> **Pharmacist Clinical Decision Support Dashboard**  
> Built with React 19, TypeScript, and Vite. Designed to provide transparent, multi-dimensional medication safety surveillance and Kenya-specific formulary recommendations.

---

## 1. Overview & Primary Clinical Workflow

OmniPharma is an agentic clinical decision-support interface built specifically for clinical pharmacists. Rather than hiding safety findings behind a conversational chatbot, it surfaces deterministic clinical safety findings in a structured, actionable dashboard:

```
Patient Selection -> Comorbidity Review -> Safety Screening -> Multi-Severity Findings -> Supporting Evidence -> Formulary Alternatives -> Pharmacist Review
```

### Twelve Distinct Finding Categories

OmniPharma evaluates twelve distinct finding categories, giving each an explicit icon, label, and clinical rationale (avoiding generic "warning" buckets):

| Finding Type | Category Label | Clinical Mechanism & Scope |
|---|---|---|
| `DRUG_DRUG_INTERACTION` | Drug-Drug Interaction | Pharmacokinetic / pharmacodynamic pair interactions (e.g. Warfarin + NSAID) |
| `PREGNANCY` | Pregnancy Safety Warning | Teratogenic and trimester-specific hazards (e.g. Isotretinoin, ACE inhibitors) |
| `RENAL_CONTRAINDICATION` | Renal Impairment Contraindication | Glomerular clearance reduction and nephrotoxicity (e.g. Metformin accumulation) |
| `HYPERKALEMIA_RISK` | Hyperkalemia Risk | Potassium excretion impairment compound risk (e.g. Lisinopril / Spironolactone) |
| `HEPATIC_CONTRAINDICATION` | Hepatic Impairment Contraindication | Hepatic reserve limits and clearance saturation (e.g. Statins, Paracetamol) |
| `RESPIRATORY_CONTRAINDICATION` | Respiratory / Asthma Contraindication | NSAID/aspirin-exacerbated bronchospasm in diagnosed asthma |
| `G6PD_CONTRAINDICATION` | G6PD Deficiency Contraindication | Oxidative hemolytic triggers in G6PD enzyme deficiency (e.g. Co-trimoxazole) |
| `AGE_BASED_CAUTION` | Age-Based / Beers Criteria Caution | Fall risk, sedation, and cognitive risks in elderly patients (e.g. Diazepam) |
| `ALLERGY` | Known Allergy Contraindication | Direct hypersensitivity to recorded patient allergens |
| `ALLERGY_CROSS_REACTIVITY` | Allergy Cross-Reactivity Risk | Shared chemical epitope risk (e.g. Penicillin allergy cross-reacting with Amoxicillin) |
| `DUPLICATE_THERAPY` | Duplicate Therapy Alert | Overlapping therapeutic classes or active ingredient redundancies |
| `UNRESOLVED_DRUG` | Unresolved / Unrecognized Drug | Unregistered medications not found in verified pharmacy catalogues |

---

## 2. Quick Start & Setup

### Prerequisites
- Node.js 18+ (tested on Node 20 / 22)
- FastAPI Backend running at `http://localhost:8000` (see `../backend/README.md`)

### Installation & Launch

```bash
# 1. Navigate to the frontend directory
cd OmniPharma/frontend

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.example .env
# Edit VITE_API_BASE_URL if your backend runs on a custom port/host (defaults to http://localhost:8000)

# 4. Start local development server
npm run dev

# 5. Build for production
npm run build

# 6. Preview production bundle
npm run preview
```

---

## 3. Architecture & File Layout

Following the contract specified in `../docs/FRONTEND_DEVELOPER_REFERENCE.md`:

```
OmniPharma/frontend/
├── src/
│   ├── main.tsx                         # Entry point mounting App and CSS design system
│   ├── App.tsx                          # App coordinator managing routing & active patient state
│   ├── api/
│   │   ├── client.ts                    # apiFetch wrapper, error handling, casing conversion, Request-ID
│   │   ├── patients.ts                  # GET /patients, GET /patients/{id}, GET /patients/{id}/medications
│   │   ├── screening.ts                 # POST /screenings/interaction, POST /recommendations
│   │   └── medications.ts               # GET /medications/search, GET /medications/{id}
│   ├── types/
│   │   ├── patient.ts                   # PatientContext, PatientSummary, ConditionRecord, AllergyRecord
│   │   ├── medication.ts                # DrugSummary, DrugDetail, EvidenceItem
│   │   └── screening.ts                 # FindingType (12 union), Severity, SafetyFinding, ScreeningResponse
│   ├── hooks/
│   │   ├── usePatients.ts               # Fetches & caches patient list for selector
│   │   ├── usePatientContext.ts         # Full patient context with auto-refetch & clean null handling
│   │   ├── useScreening.ts              # Mutation hook for POST /screenings/interaction
│   │   └── useRecommendations.ts        # Mutation hook for POST /recommendations
│   ├── components/
│   │   ├── AppShell.tsx                 # Header, navigation tabs, error boundary, subheader context
│   │   ├── PatientSelector.tsx          # Demo patient selector with quick comorbidity presets
│   │   ├── PatientSummary.tsx           # Explicit clinical statuses (not recorded chip for UNKNOWN)
│   │   ├── ConditionsList.tsx           # Scannable active/chronic diagnosis cards with ICD codes
│   │   ├── AllergyList.tsx              # Allergy records; handles 'none' as 'No known allergies'
│   │   ├── MedicationTable.tsx          # Unified sortable table for active & historical therapies
│   │   ├── SafetyReviewPanel.tsx        # Owns 'Run Review', groups by severity, handles INCOMPLETE_CONTEXT
│   │   ├── FindingCard.tsx              # Exhaustive switch over 12 FindingTypes with no default case
│   │   ├── EvidencePanel.tsx            # Three distinct states: citations, unavailable, or unrequested
│   │   ├── AlternativeTable.tsx         # Candidates labeled for pharmacist review; shows exclusion reasons
│   │   ├── DrugSearch.tsx               # Debounced catalogue autocomplete
│   │   ├── LoadingState.tsx             # Shared loading indicator
│   │   ├── ErrorState.tsx               # Shared accessible error placeholder with retry
│   │   └── AuditMeta.tsx                # Footer with ruleset, catalogue snapshot, and trace ID
│   ├── pages/
│   │   ├── DashboardPage.tsx            # High-level 12-category surveillance overview & quick demo launcher
│   │   ├── PatientReviewPage.tsx        # Comprehensive patient dossier
│   │   ├── SafetyReviewPage.tsx         # Regimen builder & safety findings evaluation
│   │   ├── AlternativesPage.tsx         # Target drug alternatives with inclusion/exclusion justifications
│   │   └── DrugDetailsPage.tsx          # Full catalogue lookup, provenance, and inventory
│   └── config/
│       └── env.ts                       # VITE_API_BASE_URL configuration
├── .env.example
├── package.json
└── README.md
```

---

## 4. Demo Mode & Synthetic Patient Presets

The application includes synthetic patient profiles specifically curated to demonstrate every safety finding category without using real patient data:

1. **Cynthia Wanjiku (ID 3) — `PREGNANCY` Warning**
   - Active condition: Acne / Dermatological
   - Regimen includes: `isotretinoin`
   - Trigger: Pregnancy status + known human teratogen rule.

2. **Felix Ochieng (ID 6) — `RENAL_CONTRAINDICATION` & `HYPERKALEMIA_RISK`**
   - Active condition: Chronic Kidney Disease (`N18`) with `MODERATE_IMPAIRMENT`
   - Regimen includes: `metformin` + `lisinopril`
   - Trigger: Renal clearance impairment + metformin accumulation hazard, combined with potassium-retention compound risk.

3. **David Mwangi (ID 4) — `HEPATIC_CONTRAINDICATION`**
   - Clinical status: `MODERATE_IMPAIRMENT` hepatic function
   - Regimen includes: `atorvastatin`
   - Trigger: Hepatic clearance saturation and hepatotoxicity threshold limits.

4. **Esther Njeri (ID 5) — `RESPIRATORY_CONTRAINDICATION`**
   - Active condition: Asthma (`J45`)
   - Regimen includes: `ibuprofen`
   - Trigger: NSAID-exacerbated bronchospasm in diagnosed asthma.

5. **Peter Mutiso (ID 11) — `G6PD_CONTRAINDICATION`**
   - Clinical status: `DEFICIENT` G6PD enzyme
   - Regimen includes: `sulfamethoxazole-trimethoprim`
   - Trigger: Acute oxidative hemolytic anemia trigger in G6PD deficiency.

6. **Mary Wambui (ID 12) — `AGE_BASED_CAUTION`**
   - Demographics: Age 73 years
   - Regimen includes: `diazepam`
   - Trigger: Beers Criteria long-acting benzodiazepine fall and sedation hazard in the elderly.

7. **Hassan Ali (ID 8) / John Kiptoo (ID 10) — `ALLERGY_CROSS_REACTIVITY`**
   - Recorded allergy: `penicillin` (severe anaphylaxis risk)
   - Evaluated drug: `amoxicillin`
   - Trigger: Shared beta-lactam core structure cross-reactivity.

8. **Brian Otieno (ID 2) — `DRUG_DRUG_INTERACTION`**
   - Regimen includes: `warfarin` + `ibuprofen`
   - Trigger: Concurrent anticoagulant + NSAID antiplatelet and gastrointestinal bleeding risk.

---

## 5. Clinical Safety & UX Guarantees

- **No Color-Alone Severity**: Every severity level (`CONTRAINDICATED`, `HIGH`, `MODERATE`, `LOW`, `INFO`) renders both an explicit text label and an icon alongside background styling.
- **Explicit "Not Recorded" Status**: Missing or unknown organ parameters (Renal, Hepatic, G6PD, Pregnancy) render as an explicit "not recorded" chip rather than being silently omitted or assumed normal.
- **Incomplete Context Handling**: Distinct `INCOMPLETE_CONTEXT` banner warns the pharmacist when an unrecorded status creates ambiguity.
- **Exclusion Transparency**: Disqualified formulary alternatives are always displayed in a dedicated section with the exact clinical rule that disqualified them.
- **Non-Prescriptive Role**: All alternatives are labeled "candidate for pharmacist review" to preserve pharmacist clinical autonomy.
- **Auditability**: Ruleset version, catalogue snapshot timestamp, and request trace IDs are attached to every screening result via `AuditMeta`.
