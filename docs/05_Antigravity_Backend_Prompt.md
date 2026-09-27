You are building the OmniPharma hackathon backend in Python.

READ FIRST
Before writing any code, read `../docs/BACKEND_DEVELOPER_REFERENCE.md` in full. That file is the
authoritative module/docstring contract for this backend: every module, class and public function
you generate must carry a docstring matching the contract given there (Google-style, full
Args/Returns/Raises/Notes) — not a shortened paraphrase of it. If anything below conflicts with
that file, the reference file wins. Also read `../docs/04_FastAPI_Backend_Design.md` for the API
and schema design and `../docs/03_Agent_Architecture.md` for the decision flow and rule ordering.

REPO LOCATION
This backend is a subdirectory of a single combined repo: build it at `OmniPharma/backend/`, as a
sibling of `OmniPharma/frontend/` (built separately from `06_Antigravity_Frontend_Prompt.md`) and
`OmniPharma/docs/` (shared specs, read-only inputs to this build). Do not create a separate
top-level project for the backend.

SOURCE CONTEXT
OmniPharma is an agentic pharmacist/clinical decision-support prototype. The broader problem includes
medication reconciliation, drug information/advisory, ward-round support and medication safety. The
hackathon MVP must demonstrate:
1) patient-context-aware drug interaction/safety screening — covering pregnancy, allergies (including
   cross-reactive drug classes), renal impairment, hepatic impairment, hyperkalemia risk, G6PD
   deficiency, respiratory conditions and age-based prescribing caution. Pregnancy is one category
   among several, not the primary focus — the mock dataset and rule tables must give at least five
   distinct non-pregnancy comorbidity scenarios a real, rule-backed finding; and
2) context-aware medication alternative support using a Kenya-specific drug catalogue.
Use synthetic patient data only.

ARCHITECTURE
Implement a hybrid architecture:
- FastAPI API layer
- SQLAlchemy repositories
- SQLite for demo
- deterministic clinical safety rules as the source of truth (see rule ordering in
  `../docs/03_Agent_Architecture.md` Section 5 — do not reorder it)
- agent orchestrator for tool selection/flow
- LLM adapter only for explanation/synthesis, never for inventing or overriding safety findings
- separate PPB scraper/ingestion service (relocate the supplied `08_ppb_drug_scraper_service/` to
  `OmniPharma/scripts/ppb_scraper/` unchanged)
- Pydantic v2 schemas
- httpx for external evidence APIs
- pytest tests
- uv for dependency management (own `pyproject.toml`/`uv.lock`, not `requirements.txt` — see PACKAGE
  MANAGEMENT below)

PROJECT STRUCTURE
```
OmniPharma/backend/
  app/main.py
  app/api/{patients,screening,medications,health}.py
  app/agents/{orchestrator,pharmacist_agent,prompts}.py
  app/services/{patient_service,interaction_service,recommendation_service,drug_catalog_service,evidence_service}.py
  app/rules/{interaction_rules,contraindication_rules,allergy_rules,pregnancy_rules,age_based_rules}.py
  app/db/{session,models,repositories}.py
  app/schemas/{patient,medication,screening}.py
  app/core/{config,logging,exceptions}.py
  tests/
  data/
  pyproject.toml
  uv.lock
  .python-version
  .env.example
  README.md
```

PACKAGE MANAGEMENT
Use uv, not pip/requirements.txt. This backend is its own uv project — do not fold it into a
repo-root uv project or a uv workspace with the PPB scraper. Initialize with
`uv init --app --name omnipharma-backend` inside `OmniPharma/backend/`, add runtime dependencies with
`uv add fastapi uvicorn[standard] sqlalchemy pydantic httpx beautifulsoup4` and dev dependencies with
`uv add --dev pytest pytest-asyncio httpx`. Document `uv sync` and `uv run uvicorn app.main:app --reload`
as the setup/run commands in `OmniPharma/backend/README.md` instead of `pip install -r requirements.txt`.

API
```
GET  /api/v1/health
GET  /api/v1/patients
GET  /api/v1/patients/{patient_id}
GET  /api/v1/patients/{patient_id}/medications
GET  /api/v1/medications/search?q=...
GET  /api/v1/medications/{drug_id}
POST /api/v1/screenings/interaction
POST /api/v1/recommendations
```

SCREENING
Request:
```json
{
  "patient_id": 1,
  "medications": ["drug name 1", "drug name 2"],
  "include_evidence": true
}
```
Return:
```json
{
  "patient_id": 1,
  "status": "CLEAR|REVIEW_REQUIRED|CONTRAINDICATED|INCOMPLETE_CONTEXT",
  "findings": [
    {
      "type": "DRUG_DRUG_INTERACTION|ALLERGY|ALLERGY_CROSS_REACTIVITY|PREGNANCY|RENAL_CONTRAINDICATION|HEPATIC_CONTRAINDICATION|HYPERKALEMIA_RISK|G6PD_CONTRAINDICATION|RESPIRATORY_CONTRAINDICATION|AGE_BASED_CAUTION|DUPLICATE_THERAPY|UNRESOLVED_DRUG",
      "severity": "INFO|LOW|MODERATE|HIGH|CONTRAINDICATED",
      "medications": [],
      "rule_id": "...",
      "summary": "...",
      "rationale": "...",
      "evidence": [],
      "evidence_unavailable": false
    }
  ],
  "recommendations": [],
  "ruleset_version": "demo-1.0",
  "catalogue_version": "...",
  "explanation": null
}
```

DATA
Create ORM models for:
patients (add `g6pd_status`: NORMAL|DEFICIENT|UNKNOWN alongside the existing `renal_status` /
`hepatic_status`), conditions, allergies, medications, prescriptions, medication_history, inventory,
interaction_rules, screening_audit, **plus three new tables**:
- `pregnancy_drug_warnings` (id, drug_name, trimester_scope, severity, mechanism, recommendation, source, version)
- `condition_drug_contraindications` (id, condition_code, drug_name, finding_type, severity, mechanism, recommendation, source, version)
- `allergy_cross_reactivity` (id, allergen, cross_reactive_drug, mechanism, severity, source, version)

These three tables exist because `contraindication_rules.py`, `pregnancy_rules.py` and
`allergy_rules.py` need real, versioned, queryable data to read from — do not hard-code any warning
inside a rule module. See `../docs/BACKEND_DEVELOPER_REFERENCE.md` Section 3 for the exact function
contracts these tables feed.

Use integer PKs and foreign keys. Add indexes for medication names/INN and patient medication lookups.

RULE ENGINE
Implement deterministic functions, each documented exactly per
`../docs/BACKEND_DEVELOPER_REFERENCE.md`:
- `evaluate_drug_pairs()`
- `evaluate_allergies()` (direct allergen match and cross-reactivity match, distinct finding types)
- `evaluate_pregnancy()` (returns immediately with no findings if not PREGNANT)
- `evaluate_contraindications()` (renal, hepatic, hyperkalemia, G6PD, respiratory — one evaluator,
  five finding types, driven by `finding_type` on the matched rule row)
- `evaluate_age_based_caution()` (new — Beers-criteria-style, age derived from date_of_birth, no
  backing table, threshold age 65, severity never CONTRAINDICATED)
- `evaluate_duplicate_therapy()`

Rules must be easy to extend and version, and must be pure functions (no I/O, no DB session). Do not
put safety logic in prompts. `interaction_service.screen_medications()` is the only caller of all six
functions and is the only place evaluation order is defined — follow the fixed order in
`../docs/03_Agent_Architecture.md` Section 5.

MOCK DATA
Load the supplied `07_mock_patients.db` if present, extended per `../docs/10_Mock_Data_Expansion_Spec.md`.
Otherwise provide a seed script that creates the full patient set described in that spec: at least 10
fictional patients with demographics, conditions, allergies, pregnancy status where applicable, renal/
hepatic/G6PD status, medication history, current prescriptions, inventory rows, and deliberate
scenarios covering **at least five distinct non-pregnancy comorbidity categories** (renal, hepatic,
G6PD, respiratory, hyperkalemia, or age-based) in addition to the pregnancy scenario — do not build a
seed set where pregnancy is the only condition with a matching rule.

RECOMMENDATION ENGINE
Do NOT directly generate a prescription.
Generate candidates from the local drug catalogue/inventory, then:
1. resolve canonical medicine
2. filter allergies (direct and cross-reactive)
3. filter pregnancy conflicts
4. filter condition contraindications (renal, hepatic, hyperkalemia, G6PD, respiratory)
5. filter age-based caution
6. filter known DDIs against current medication list
7. filter unavailable inventory if inventory mode is enabled
8. return remaining candidates AND excluded candidates together, each excluded one carrying a
   machine-readable exclusion reason — never drop an excluded candidate from the response silently.

EVIDENCE
Create an EvidenceService adapter. openFDA may be used as supporting drug-label evidence, but never
as the sole authority for the deterministic interaction engine. Store source URL/name and retrieval
timestamp. Handle timeouts and unavailable sources gracefully — return `evidence_unavailable: true` on
the affected finding rather than failing the whole request.

AGENT
Implement `AgentOrchestrator.run_medication_review()` exactly per
`../docs/BACKEND_DEVELOPER_REFERENCE.md` Section 3. The orchestrator retrieves patient context,
resolves medicines, executes deterministic rules in fixed order, optionally retrieves evidence, then
asks the PharmacistAgent to summarize structured findings.
If the LLM is unavailable, return deterministic findings without narrative (`explanation: null`).
Never allow an LLM response to change severity, add an unsupported interaction, or prescribe.

FASTAPI QUALITY
- dependency injection for DB sessions
- typed Pydantic models
- consistent HTTP errors, mapped from the domain exceptions in `app/core/exceptions.py`
- request IDs
- structured logging
- CORS configurable by environment (see `.env.example`: `CORS_ALLOWED_ORIGINS`)
- OpenAPI descriptions
- health endpoint that reports per-dependency status, not just a flat OK/not-OK
- no blocking network calls inside async endpoints; use httpx AsyncClient or move sync work to a
  safe service boundary

TESTS
Include unit tests for every rule (including at least one test per new finding type: RENAL_,
HEPATIC_, HYPERKALEMIA_RISK, G6PD_, RESPIRATORY_CONTRAINDICATION, AGE_BASED_CAUTION,
ALLERGY_CROSS_REACTIVITY), API integration tests, repository tests and recommendation filtering tests.
Add a deterministic demo test that proves: one patient produces a DDI finding, one produces a
pregnancy finding, and at least one other patient produces a non-pregnancy comorbidity finding (e.g.
the CKD patient on metformin from `../docs/10_Mock_Data_Expansion_Spec.md`).

DELIVERABLE
Produce runnable code, README (at `OmniPharma/backend/README.md`), `pyproject.toml`/`uv.lock`,
`.env.example`, a `uv run` seed command, a `uv run pytest` test command, and curl examples. Do not
leave TODO placeholders for the core hackathon interaction feature.
