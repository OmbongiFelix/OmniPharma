# OmniPharma Backend

Agentic pharmacist / clinical decision-support API built with FastAPI, SQLAlchemy 2.x, Pydantic v2, and SQLite.

## Architecture

```
FastAPI → AgentOrchestrator → InteractionService → RuleModules (pure functions)
                            → PatientService
                            → DrugCatalogService
                            → EvidenceService (openFDA, best-effort)
                            → PharmacistAgent (LLM explanation, optional)
```

Deterministic rules are the sole authority for safety findings. The LLM layer summarises findings only; if unavailable, `explanation: null` is returned and everything else works normally.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
# 1. Install dependencies
uv sync

# 2. Add pydantic-settings if not yet added
uv add pydantic-settings

# 3. Copy and fill environment variables
cp .env.example .env

# 4. Seed the demo database
uv run python data/seed.py
```

## Running

```bash
uv run uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000`.  
OpenAPI docs: `http://localhost:8000/docs`

## Testing

```bash
uv run pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Service health + per-dependency status |
| `GET` | `/api/v1/patients` | List / search patients |
| `GET` | `/api/v1/patients/{id}` | Full patient context |
| `GET` | `/api/v1/patients/{id}/medications` | Current prescriptions + history |
| `GET` | `/api/v1/medications/search?q=` | Drug catalogue autocomplete |
| `GET` | `/api/v1/medications/{id}` | Drug detail + inventory status |
| `POST` | `/api/v1/screenings/interaction` | Full safety screening |
| `POST` | `/api/v1/recommendations` | Safety-filtered alternative candidates |

## Screening Request Example

```bash
curl -X POST http://localhost:8000/api/v1/screenings/interaction \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 3,
    "medications": ["isotretinoin", "lisinopril"],
    "include_evidence": false
  }'
```

Expected findings: `PREGNANCY` (CONTRAINDICATED) for isotretinoin, `PREGNANCY` (HIGH) for lisinopril.

## Demo Scenarios

| Patient | Scenario | Finding type |
|---------|----------|-------------|
| Cynthia Wanjiku (3) | Pregnant + isotretinoin | `PREGNANCY` |
| Felix Ochieng (6) | CKD + metformin | `RENAL_CONTRAINDICATION` |
| Felix Ochieng (6) | CKD + lisinopril | `HYPERKALEMIA_RISK` |
| David Mwangi (4) | Hepatic impairment + atorvastatin | `HEPATIC_CONTRAINDICATION` |
| Esther Njeri (5) | Asthma + ibuprofen | `RESPIRATORY_CONTRAINDICATION` |
| Peter Mutiso (11) | G6PD deficient + co-trimoxazole | `G6PD_CONTRAINDICATION` |
| Mary Wambui (12) | Age 73 + diazepam | `AGE_BASED_CAUTION` |
| John Kiptoo (10) | Penicillin allergy + amoxicillin | `ALLERGY_CROSS_REACTIVITY` |
| Any patient | Warfarin + ibuprofen | `DRUG_DRUG_INTERACTION` |

## Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── api/                       # Thin HTTP handlers
│   │   ├── patients.py
│   │   ├── screening.py
│   │   ├── medications.py
│   │   └── health.py
│   ├── agents/                    # Orchestrator + LLM wrapper
│   │   ├── orchestrator.py
│   │   ├── pharmacist_agent.py
│   │   └── prompts.py
│   ├── services/                  # Business logic
│   │   ├── patient_service.py
│   │   ├── interaction_service.py
│   │   ├── recommendation_service.py
│   │   ├── drug_catalog_service.py
│   │   └── evidence_service.py
│   ├── rules/                     # Pure deterministic rule functions
│   │   ├── interaction_rules.py
│   │   ├── contraindication_rules.py
│   │   ├── allergy_rules.py
│   │   ├── pregnancy_rules.py
│   │   ├── age_based_rules.py
│   │   └── duplicate_therapy_rules.py
│   ├── db/
│   │   ├── session.py
│   │   ├── models.py
│   │   └── repositories.py
│   ├── schemas/
│   │   ├── patient.py
│   │   ├── medication.py
│   │   └── screening.py
│   └── core/
│       ├── config.py
│       ├── logging.py
│       └── exceptions.py
├── data/
│   └── seed.py                    # Demo database seed script
├── tests/
│   ├── conftest.py
│   ├── test_rules.py
│   └── test_api.py
├── pyproject.toml
├── .env.example
└── README.md
```

## Configuration

All settings are loaded from environment variables (or `.env`). See `.env.example` for the full list. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./data/omnipharm.db` | Main DB |
| `LLM_PROVIDER` | *(blank)* | `openai` or `google`; blank = LLM disabled |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,...` | Frontend origins |
| `RULESET_VERSION` | `demo-1.0` | Embedded in every response |
| `INVENTORY_AWARE` | `false` | Exclude OOS from recommendations |

## Rule Engine

Rules execute in this fixed order (enforced by `interaction_service.screen_medications`):

1. Drug–drug interactions (`interaction_rules`)
2. Allergy conflicts — direct then cross-reactive (`allergy_rules`)
3. Pregnancy warnings — only if `PREGNANT` (`pregnancy_rules`)
4. Condition contraindications — renal, hepatic, hyperkalemia, G6PD, respiratory (`contraindication_rules`)
5. Age-based caution — Beers-criteria style, threshold 65 years (`age_based_rules`)
6. Duplicate therapy (`duplicate_therapy_rules`)

Rule modules are pure functions: no I/O, no DB access. All DB access goes through `app/db/repositories.py`.
