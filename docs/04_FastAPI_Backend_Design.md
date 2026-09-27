**OmniPharma — FastAPI Backend Design**

_Python + FastAPI + SQLAlchemy/SQLite + Pydantic. Revision 2: new safety tables, merged-repo paths._

# 1. Stack

- Python 3.12+
- FastAPI + Uvicorn
- Pydantic v2
- SQLAlchemy 2.x
- SQLite for hackathon/demo; PostgreSQL-ready repository layer
- httpx for external HTTP APIs
- BeautifulSoup4/lxml for PPB HTML ingestion
- pytest for tests
- Optional LLM provider behind an adapter interface

# 2. Repo Location

This backend lives at `OmniPharma/backend/` as a sibling of `OmniPharma/frontend/`, with shared specification documents at `OmniPharma/docs/`. See the root `README.md` for the full layout.

# 3. API Endpoints

`GET /api/v1/health` — Service health and database connectivity.

`GET /api/v1/patients` — List/search synthetic patients.

`GET /api/v1/patients/{patient_id}` — Return patient context (now includes `renal_status`, `hepatic_status`, and `g6pd_status`).

`GET /api/v1/patients/{patient_id}/medications` — Return medication history/current medicines.

`GET /api/v1/medications/search?q=...` — Search PPB/local drug catalogue.

`POST /api/v1/screenings/interaction` — Check a patient and medicine list for safety findings.

`POST /api/v1/recommendations` — Return filtered medication candidates for a stated indication/context.

`GET /api/v1/medications/{drug_id}` — Return canonical drug/product details.

# 4. Screening Request/Response Contract

`POST /api/v1/screenings/interaction`

Request:
```json
{
  "patient_id": 1,
  "medications": ["warfarin", "ibuprofen"],
  "include_evidence": true
}
```

Response:
```json
{
  "patient_id": 1,
  "status": "REVIEW_REQUIRED",
  "findings": [
    {
      "type": "DRUG_DRUG_INTERACTION",
      "severity": "HIGH",
      "medications": ["warfarin", "ibuprofen"],
      "rule_id": "DDI-WARFARIN-NSAID-001",
      "summary": "...",
      "rationale": "...",
      "evidence": []
    }
  ],
  "recommendations": [],
  "ruleset_version": "demo-1.0",
  "catalogue_version": "ppb-YYYY-MM-DD"
}
```

The `type` enum for a finding is now:
`DRUG_DRUG_INTERACTION | ALLERGY | ALLERGY_CROSS_REACTIVITY | PREGNANCY | RENAL_CONTRAINDICATION | HEPATIC_CONTRAINDICATION | HYPERKALEMIA_RISK | G6PD_CONTRAINDICATION | RESPIRATORY_CONTRAINDICATION | AGE_BASED_CAUTION | DUPLICATE_THERAPY | UNRESOLVED_DRUG`

`RENAL_CONTRAINDICATION`, `HEPATIC_CONTRAINDICATION`, `HYPERKALEMIA_RISK`, `G6PD_CONTRAINDICATION` and `RESPIRATORY_CONTRAINDICATION` are all backed by the same `condition_drug_contraindications` table (see below) and are only split into distinct `type` values so the frontend can group and label them clearly; they share one evaluator, `evaluate_contraindications()`.

# 5. Database Schema

- **patients**: id, patient_code, name, date_of_birth, sex, pregnancy_status, renal_status, hepatic_status, **g6pd_status**
- **conditions**: id, patient_id, condition_code, condition_name, status, onset_date
- **allergies**: id, patient_id, allergen, reaction, severity
- **medications**: id, canonical_name, inn, trade_name, dosage_form, strength, source
- **prescriptions**: id, patient_id, medication_id, dose, frequency, route, start_date, end_date, status, prescriber
- **medication_history**: id, patient_id, medication_id, dose, frequency, start_date, end_date, outcome, notes
- **inventory**: id, medication_id, quantity, facility, updated_at
- **interaction_rules**: id, drug_a, drug_b, severity, mechanism, recommendation, source, version
- **pregnancy_drug_warnings** _(new)_: id, drug_name, trimester_scope (`ALL | FIRST | SECOND | THIRD`), severity, mechanism, recommendation, source, version
- **condition_drug_contraindications** _(new)_: id, condition_code, drug_name, finding_type (one of the five contraindication `type` values above), severity, mechanism, recommendation, source, version
- **allergy_cross_reactivity** _(new)_: id, allergen, cross_reactive_drug, mechanism, severity, source, version
- **screening_audit**: id, request_id, patient_id, created_at, ruleset_version, result_json

These three new tables exist because the original spec's `pregnancy_rules.py`, `contraindication_rules.py` and `allergy_rules.py` were each documented as reading from "configured medicine warnings" or "recorded allergies," but no table backed that data — only `interaction_rules` existed, and it is drug-pair-only by design (`drug_a`, `drug_b`). Without a dedicated table, those three rule modules would have had to hard-code warnings inside Python, which violates the "rule modules must remain deterministic and side-effect free... easy to extend and version" requirement, since a hard-coded list isn't versioned data.

`g6pd_status` on `patients` takes the same three-state shape as `renal_status`/`hepatic_status`: `NORMAL | DEFICIENT | UNKNOWN`.

Age-based caution does **not** get its own table: age is derived from `date_of_birth` at evaluation time and compared against a small set of hard-coded thresholds documented in `BACKEND_DEVELOPER_REFERENCE.md` (`app/rules/age_based_rules.py`), because age-prescribing caution (Beers-criteria-style) is inherently a function of the patient row, not a lookup against a drug catalogue row.

# 6. Service Responsibilities

- **PatientService**: patient context retrieval only.
- **DrugCatalogService**: canonicalization and PPB product lookup.
- **InteractionService**: deterministic DDI evaluation.
- **ConstraintService**: allergy (incl. cross-reactivity), pregnancy, condition-contraindication and age-based rules.
- **RecommendationService**: candidate generation + safety filtering.
- **EvidenceService**: external source adapters and provenance.
- **AgentOrchestrator**: sequence tools and construct a structured result.
- **PharmacistAgent**: narrative explanation only.

# 7. Configuration

Environment variables (`OmniPharma/backend/.env.example`):
```
APP_ENV=development
DATABASE_URL=sqlite:///./data/omnipharm.db
PPB_DATABASE_URL=sqlite:///./data/ppb_drugs.db
LLM_PROVIDER=...
LLM_API_KEY=...
OPENFDA_API_KEY=...
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

# 8. Testing Strategy

- Unit-test every clinical rule with positive and negative examples, including at least one case per new contraindication `finding_type`.
- Integration-test screening against the expanded synthetic database (see `10_Mock_Data_Expansion_Spec.md`), asserting that at least five distinct non-pregnancy comorbidity scenarios each produce a finding.
- Contract-test FastAPI endpoints with TestClient.
- Scraper tests use saved HTML fixtures so tests do not depend on the live PPB site.
- LLM tests verify schema compliance and that narrative cannot override deterministic findings.

# 9. Important Implementation Boundary

Medication recommendations must be implemented as candidate generation and filtering, not autonomous prescribing. The API should return candidates plus reasons/constraints and a review-required state. Renal, hepatic, G6PD and age-based findings are risk flags for pharmacist review — the backend must never compute or suggest an adjusted dose.
