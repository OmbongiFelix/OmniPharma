# OmniPharma — Hackathon Deliverables (Revised)

This is the revised deliverable package. Frontend and backend now live under
one root folder, `OmniPharma/`, so you can build, run and demo both from a
single directory today. Python dependency management uses **uv** throughout.

## Package management: uv, and where to run `uv init`

**Don't run `uv init` once at the `OmniPharma/` repo root.** Run it separately
inside `backend/` and inside `scripts/ppb_scraper/`. Two independent uv
projects, not one, and not a shared workspace, for this hackathon build:

- **The frontend isn't a Python project at all** — it's `npm`/Vite. A root-level
  `uv init` would only ever manage the backend's dependencies anyway, so it
  would just be a confusingly-placed `backend` project wearing the repo root's
  name.
- **The backend and the scraper have deliberately different dependency
  footprints.** `backend/` needs FastAPI, SQLAlchemy, httpx, pytest.
  `scripts/ppb_scraper/` needs Playwright plus a downloaded Chromium binary,
  which is a multi-hundred-MB install you don't want triggered every time you
  `uv sync` the backend before a demo. Two separate `pyproject.toml`/`uv.lock`
  pairs keep those isolated.
- **This matches the architecture rule already in the spec**: "Scraper code is
  a separate ingestion service and must not be imported into request-time API
  handlers" (`docs/BACKEND_DEVELOPER_REFERENCE.md` Section 4). Separate uv
  projects enforce that boundary at the tooling level, not just by convention.
- A uv **workspace** (one root `pyproject.toml` with
  `[tool.uv.workspace] members = ["backend", "scripts/ppb_scraper"]`) is the
  right move later if you want one `uv sync` to set up everything at once —
  but it still resolves all members into one shared lockfile/environment,
  which brings Playwright back into the backend's dependency graph. Skip it
  for today; revisit it only if you actually need both running from one
  `uv sync` for CI or onboarding later.

So, concretely:
```bash
cd OmniPharma/backend && uv init --app --name omnipharma-backend
cd OmniPharma/scripts/ppb_scraper && uv init --app --name ppb-scraper
```
Each directory gets its own `pyproject.toml`, `uv.lock`, and `.venv`. Add
dependencies with `uv add fastapi uvicorn sqlalchemy pydantic httpx` (backend)
and `uv add playwright beautifulsoup4 lxml` (scraper), and dev-only tools with
`uv add --dev pytest`.

## Target repo layout (what Antigravity should produce)

```
OmniPharma/
├── README.md                          <- this file (or your own demo notes)
├── docs/
│   ├── BACKEND_DEVELOPER_REFERENCE.md      <- Python/FastAPI docstring contract
│   ├── FRONTEND_DEVELOPER_REFERENCE.md     <- TypeScript/React docstring contract
│   ├── 01_Problem_Context_Proposed_Solution.md
│   ├── 03_Agent_Architecture.md
│   ├── 04_FastAPI_Backend_Design.md
│   └── 10_Mock_Data_Expansion_Spec.md
├── backend/
│   ├── app/...                        <- built from 05_Antigravity_Backend_Prompt.md
│   ├── tests/
│   ├── data/
│   │   ├── omnipharm.db               <- seeded from 07_mock_patients.db + expansion spec
│   │   └── ppb_drugs.db               <- output of the PPB scraper
│   ├── pyproject.toml                 <- own uv project
│   ├── uv.lock
│   ├── .python-version
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/...                        <- built from 06_Antigravity_Frontend_Prompt.md
│   ├── package.json
│   ├── .env.example
│   └── README.md
└── scripts/
    └── ppb_scraper/                   <- relocated 08_ppb_drug_scraper_service/, own uv project
        ├── ppb_scraper.py
        ├── pyproject.toml
        └── uv.lock
```

## File manifest and what changed

| File | Status | What changed |
|---|---|---|
| `docs/BACKEND_DEVELOPER_REFERENCE.md` | Rewritten (was `02_Developer_Docstrings_Reference.md`) | Every module now has a full docstring, not a one-line purpose. Every public class/function has complete Google-style Args/Returns/Raises/Notes. Adds the new safety-rule modules and tables described below. |
| `docs/FRONTEND_DEVELOPER_REFERENCE.md` | **New** | The frontend previously had no equivalent contract. This defines the TSDoc/JSDoc standard, component prop contracts, hook contracts and API client typing rules that `06_Antigravity_Frontend_Prompt.md` now points to. |
| `05_Antigravity_Backend_Prompt.md` | Rewritten (was `.txt`) | Points Antigravity at `docs/BACKEND_DEVELOPER_REFERENCE.md` before writing code, specifies uv (`pyproject.toml`/`uv.lock`, not `requirements.txt`), adds the new contraindication/pregnancy-warning tables and rule modules, and targets the merged repo layout. |
| `06_Antigravity_Frontend_Prompt.md` | Rewritten (was `.txt`) | Points at `docs/FRONTEND_DEVELOPER_REFERENCE.md` the same way the backend prompt points at its own reference. Adds UI surface for the broadened comorbidity findings (not just pregnancy). Targets the merged repo layout. |
| `docs/03_Agent_Architecture.md` | Updated | Adds the renal, hepatic, hyperkalemia, G6PD, age-based (Beers-criteria-style) and QT-prolongation risk categories to the safety engine and agent tools. |
| `docs/04_FastAPI_Backend_Design.md` | Updated | Adds `pregnancy_drug_warnings`, `condition_drug_contraindications` and `allergy_cross_reactivity` tables — these were referenced by `pregnancy_rules.py`, `contraindication_rules.py` and `allergy_rules.py` in the original spec but never actually had a backing table, so those rule modules had nowhere to read from except hard-coded values. |
| `docs/01_Problem_Context_Proposed_Solution.md` | Light edit | Scope language broadened so "medication safety" isn't read as pregnancy-only; directory references updated. |
| `docs/10_Mock_Data_Expansion_Spec.md` | **New** | The mock dataset had only one pregnant patient and, while it already had CKD/hepatic/asthma/AF/diabetes patients, none of those conditions had a rule to actually fire against them. This spec fixes two data bugs it found along the way and adds the missing rule rows so at least six distinct non-pregnancy comorbidity scenarios produce real findings. |
| `07_mock_patients.db` | Unchanged binary; superseded by the SQL in the expansion spec | Regenerate it by running the SQL in `10_Mock_Data_Expansion_Spec.md` against the original file, or hand that file to Antigravity as the seed source. |
| `08_ppb_drug_scraper_service/` | Unchanged, relocated | Move as-is to `scripts/ppb_scraper/`. Convert its `requirements.txt` to a uv project (see above) — no functional changes needed, it was already correctly kept out of the request-time API path. |

## What I found worth improving (summary)

1. **Schema/rule mismatch.** `pregnancy_rules.py` and `contraindication_rules.py` were specified as reading from "configured medicine warnings," but no table for that existed anywhere in the schema — only a generic `interaction_rules` table for drug-drug pairs. Fixed by adding two dedicated tables (see `04_FastAPI_Backend_Design.md`).
2. **Docstrings were purpose-only, not real contracts.** The original reference gave one-line "Purpose" statements for most modules and full Args/Returns/Raises for only three functions. The rewritten reference gives every public class and function a complete docstring.
3. **Mock data exercised only one non-default clinical scenario (pregnancy)** even though the patient set already had CKD, hepatic impairment, asthma and atrial fibrillation patients. None of those conditions had a matching contraindication rule, so they were narrative-only, not testable. The expansion spec gives each of them a real, demonstrable finding — and along the way found two real data bugs in `07_mock_patients.db` (a CKD patient's renal status had shifted into the pregnancy-status column; another patient had an invalid pregnancy-status value).
4. **No frontend developer contract.** Added `FRONTEND_DEVELOPER_REFERENCE.md` and wired the frontend prompt to it exactly the way the backend prompt is wired to its reference.
5. **Two separate project roots.** Restructured into one `OmniPharma/` root with `backend/` and `frontend/` as siblings and a shared `docs/` folder, for a same-day demo.
6. **Package management.** Standardized on uv for both Python components, kept as two independent uv projects rather than one root project or a shared workspace (see the section above).

## Demo checklist

- [ ] `cd OmniPharma/backend && uv sync && uv run uvicorn app.main:app --reload`
- [ ] `cd OmniPharma/frontend && npm install && npm run dev` (point `VITE_API_BASE_URL` at the backend)
- [ ] Confirm `GET /api/v1/health` returns OK before opening the frontend.
- [ ] Walk through at least four findings in the demo: one drug-drug (warfarin + ibuprofen), one pregnancy (isotretinoin/ACE inhibitor on the pregnant patient), one renal (the CKD patient on metformin), and one from another category of your choice — G6PD, hepatic, respiratory or age-based — from `10_Mock_Data_Expansion_Spec.md`.
