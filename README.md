# OmniPharma

**Agentic Medication Safety & Clinical Decision-Support Platform**

OmniPharma is an agentic clinical decision-support platform designed to augment pharmacists and clinical teams by automating medication reconciliation, medication safety screening, drug-information retrieval, evidence-aware alternatives, and related medication-review workflows.

The hackathon MVP focuses on a demonstrable medication-safety workflow while establishing an architecture that can later support ward-round assistance, admission/discharge reconciliation, drug information/advisory, stock-aware alternatives, and longitudinal medication review.

> **Important:** OmniPharma is a clinical decision-support tool, not an autonomous prescribing system. Its recommendations and alerts are advisory and require professional review.

---

## 1. Problem

Pharmacists and clinical teams must continuously review information distributed across:

- Patient demographics and clinical conditions
- Allergies and cross-reactive drug classes
- Current prescriptions
- Medication history
- Drug catalogues
- Drug availability/inventory
- Medication-safety rules
- External drug-information sources

Medication reconciliation is repetitive but safety-critical. A medication that was appropriate historically may become inappropriate after a new medication, condition, allergy, pregnancy status, or other patient-specific factor is introduced.

Drug-drug interactions are therefore only one part of medication safety.

A useful decision-support system must also identify issues involving:

- Allergies and cross-reactivity
- Pregnancy
- Renal impairment
- Hepatic impairment
- Hyperkalemia risk
- G6PD deficiency
- Respiratory conditions such as asthma/reactive airway disease
- Age-related prescribing caution
- Duplicate therapy
- Other condition-drug contraindications
- Unresolved medicines

The system must provide explanations and traceable evidence rather than opaque model-generated conclusions.

---

## 2. Proposed Solution

OmniPharma separates **deterministic clinical safety logic** from the **LLM explanation layer**.

The core workflow is:

```text
Patient + Medicines
        │
        ▼
Patient Context Retrieval
        │
        ▼
Drug Name Resolution
        │
        ▼
Deterministic Safety Rules
        │
        ├── Drug-drug interactions
        ├── Allergies / cross-reactivity
        ├── Pregnancy
        ├── Renal contraindications
        ├── Hepatic contraindications
        ├── Hyperkalemia risk
        ├── G6PD contraindications
        ├── Respiratory contraindications
        ├── Age-based caution
        └── Duplicate therapy
        │
        ▼
Structured Safety Findings
        │
        ├──────────────► Optional Evidence Retrieval
        │
        ▼
Optional LLM Explanation
        │
        ▼
Screening Response
        │
        ▼
Pharmacist Review
```

The deterministic layer remains the source of truth. The LLM summarizes structured findings and must not introduce new clinical facts, change severity, or create additional interactions.

---

## 3. MVP Scope

The MVP treats medication safety as a **multi-dimensional patient-context problem**, not merely a pregnancy checker.

Every dimension below is represented in the rule-engine design and should have at least one demonstrable rule-backed scenario in the mock dataset:

| Safety dimension | Purpose |
|---|---|
| Drug-drug interaction | Detect potentially unsafe medicine combinations |
| Allergy | Detect direct allergy conflicts |
| Allergy cross-reactivity | Detect medicines related to recorded allergen classes |
| Pregnancy | Identify configured pregnancy-specific warnings |
| Renal impairment | Detect medicines unsuitable for recorded renal status |
| Hepatic impairment | Detect hepatic contraindications |
| Hyperkalemia | Detect medication risk associated with hyperkalemia |
| G6PD deficiency | Detect medicines contraindicated for recorded deficiency |
| Respiratory | Detect condition-drug conflicts such as asthma-related risks |
| Age-based caution | Flag medicines requiring caution in older adults |
| Duplicate therapy | Detect potentially duplicative treatment |
| Unresolved drug | Prevent silent use of an unverified medicine |

---

## 4. Key Design Principles

### 4.1 Deterministic safety first

Clinical safety rules execute before any LLM explanation.

The orchestrator owns the evaluation order, while individual rule modules remain independent pure functions.

### 4.2 The LLM is not the clinical source of truth

The pharmacist agent only explains structured findings already produced by deterministic rules.

It must not:

- Invent safety facts
- Change severity
- Add interactions
- Add medicines
- Create prescriptions
- Override deterministic rules

If the LLM fails, the structured safety response is still returned.

### 4.3 Never silently guess clinical data

Unknown clinical information remains unknown.

For example:

```text
UNKNOWN renal status
        ≠
NORMAL renal status
```

Missing or unknown required context can result in:

```text
INCOMPLETE_CONTEXT
```

rather than an unjustified safe result.

### 4.4 Conservative drug resolution

User-entered drug names are resolved against a canonical medication catalogue.

Low-confidence or missing matches must not silently become a guessed medicine. An unresolved medicine is explicitly represented as `UNRESOLVED_DRUG`.

### 4.5 Recommendations are advisory

Alternative medicines are candidates for pharmacist review, not automatic substitutions or prescriptions.

Excluded candidates remain visible together with the reason they were excluded.

### 4.6 Evidence is supporting, not authoritative

External evidence can support a finding, but evidence retrieval does not determine the safety severity.

### 4.7 Missing information must be visible in the UI

The frontend must not silently replace missing clinical information with safe-looking defaults.

For example, unknown renal, hepatic, or G6PD status is rendered explicitly as **not recorded**.

---

## 5. Architecture

```text
┌──────────────────────────────────────────────┐
│                  Frontend                    │
│             React + TypeScript               │
│                                              │
│ Pages → Components → Hooks → API Clients     │
└──────────────────────┬───────────────────────┘
                       │ HTTP/JSON
                       ▼
┌──────────────────────────────────────────────┐
│                  FastAPI                     │
│                 API Layer                    │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│              Agent Orchestrator              │
│                                              │
│ Patient → Resolution → Rules → Evidence     │
│                       → Explanation          │
└───────────────┬──────────────────────────────┘
                │
       ┌────────┴─────────┐
       ▼                  ▼
┌─────────────┐    ┌───────────────┐
│  Services   │    │ Deterministic │
│             │    │    Rules      │
└──────┬──────┘    └───────┬───────┘
       │                   │
       └─────────┬─────────┘
                 ▼
        ┌──────────────────┐
        │ Repositories / DB│
        └──────────────────┘

External supporting systems:

PPB Catalogue ──► Scraper ──► Local Drug Catalogue

External Drug Information ──► Evidence Service
```

---

## 6. Repository Structure

### Backend

```text
OmniPharma/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── patients.py
│   │   │   ├── screening.py
│   │   │   ├── medications.py
│   │   │   └── health.py
│   │   ├── agents/
│   │   │   ├── pharmacist_agent.py
│   │   │   ├── orchestrator.py
│   │   │   └── prompts.py
│   │   ├── services/
│   │   │   ├── patient_service.py
│   │   │   ├── interaction_service.py
│   │   │   ├── recommendation_service.py
│   │   │   ├── drug_catalog_service.py
│   │   │   └── evidence_service.py
│   │   ├── rules/
│   │   │   ├── interaction_rules.py
│   │   │   ├── contraindication_rules.py
│   │   │   ├── allergy_rules.py
│   │   │   ├── pregnancy_rules.py
│   │   │   └── age_based_rules.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   ├── models.py
│   │   │   └── repositories.py
│   │   ├── schemas/
│   │   │   ├── patient.py
│   │   │   ├── medication.py
│   │   │   └── screening.py
│   │   └── core/
│   │       ├── config.py
│   │       ├── logging.py
│   │       └── exceptions.py
│   ├── scraper/
│   │   ├── ppb_scraper.py
│   │   ├── parser.py
│   │   └── database.py
│   └── tests/
│
└── frontend/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/
    │   ├── types/
    │   ├── hooks/
    │   ├── components/
    │   ├── pages/
    │   └── config/
    ├── package.json
    ├── vite.config.ts
    ├── .env.example
    └── README.md
```

---

## 7. Backend Responsibilities

### API layer

The API layer exposes HTTP endpoints and delegates to services/orchestrators. It must not contain clinical rule logic or direct database queries.

### Services

Services coordinate application operations such as:

- Patient-context assembly
- Medication interaction screening
- Alternative generation
- Drug catalogue lookup
- Evidence retrieval

### Rules

Rule modules contain deterministic clinical checks as pure functions.

They:

- Receive already-loaded data
- Produce structured findings
- Perform no database/network I/O
- Do not call one another

`interaction_service.py` is responsible for invoking the rule modules and maintaining their evaluation sequence.

### Repositories

Repositories isolate persistence-specific queries.

Rule-table access is routed through repositories rather than directly from business logic.

### Exceptions

Domain exceptions such as:

```text
PatientNotFoundError
DrugResolutionError
RuleConfigurationError
```

belong to the domain layer.

Only API handlers translate these exceptions into HTTP errors.

---

## 8. Medication-Safety Decision Flow

The orchestrator evaluates a review in a fixed sequence:

```text
1. Drug-drug interactions
2. Allergy
   └── Direct allergy
   └── Cross-reactivity
3. Pregnancy
4. Condition/clinical contraindications
   ├── Renal
   ├── Hepatic
   ├── Hyperkalemia
   ├── G6PD
   └── Respiratory
5. Age-based caution
6. Duplicate therapy
```

### Overall status

```text
No findings
    ↓
CLEAR

LOW / MODERATE finding
    ↓
REVIEW_REQUIRED

HIGH / CONTRAINDICATED finding
    ↓
CONTRAINDICATED

Required clinical context missing/unknown
    ↓
INCOMPLETE_CONTEXT
```

---

## 9. Safety Finding Model

Every finding is machine-readable and traceable.

```text
SafetyFinding
├── type
├── severity
├── medications
├── rule_id
├── summary
├── rationale
├── evidence
└── evidence_unavailable
```

### Finding types

```text
DRUG_DRUG_INTERACTION
ALLERGY
ALLERGY_CROSS_REACTIVITY
PREGNANCY
RENAL_CONTRAINDICATION
HEPATIC_CONTRAINDICATION
HYPERKALEMIA_RISK
G6PD_CONTRAINDICATION
RESPIRATORY_CONTRAINDICATION
AGE_BASED_CAUTION
DUPLICATE_THERAPY
UNRESOLVED_DRUG
```

### Severity levels

```text
INFO
LOW
MODERATE
HIGH
CONTRAINDICATED
```

---

## 10. API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Service/dependency health |
| GET | `/api/v1/patients` | List/search patients |
| GET | `/api/v1/patients/{patient_id}` | Full patient context |
| GET | `/api/v1/patients/{patient_id}/medications` | Patient medications |
| GET | `/api/v1/medications/search?q=...` | Drug search |
| GET | `/api/v1/medications/{drug_id}` | Drug details |
| POST | `/api/v1/screenings/interaction` | Medication safety screening |
| POST | `/api/v1/recommendations` | Alternative candidates |

---

## 11. Frontend

The frontend is a React/TypeScript application designed around the backend contracts.

### Primary components

```text
PatientSelector
PatientSummary
ConditionsList
AllergyList
MedicationTable
SafetyReviewPanel
FindingCard
EvidencePanel
AlternativeTable
DrugSearch
LoadingState
ErrorState
AuditMeta
```

### State management principles

API calls are isolated in `src/api/*`.

Hooks own loading, error, caching, and request state.

Components consume hooks rather than calling `fetch` directly.

A screening result must never remain visible after the patient or medication set changes if that result belongs to a different review context.

---

## 12. Safety UX Requirements

### Finding cards

Every finding must communicate:

- Finding category
- Severity
- Concise summary
- Detailed rationale
- Rule ID
- Supporting evidence where available

Severity cannot be communicated through color alone. Each finding type has its own label and icon.

### Evidence

The UI distinguishes between:

1. Evidence available
2. Evidence requested but unavailable
3. Evidence not requested

### Missing patient information

Missing/unknown clinical information is explicitly displayed as **not recorded** rather than omitted.

### Recommendations

Alternative medicines are labelled:

> **Candidate for pharmacist review**

They must never be presented as an automatic prescription or recommended dose.

Excluded alternatives remain visible with their exclusion reason.

---

## 13. Drug Catalogue & PPB Integration

The drug catalogue service maps trade names, INNs, and common names to canonical medication records.

The catalogue supports:

- Drug search
- Drug resolution
- Canonical medication records
- Catalogue version tracking

The PPB scraper is a separate offline ingestion process. It downloads and normalizes registered-product data into a local catalogue.

It must **never be imported into request-time API handlers**.

---

## 14. Evidence Retrieval

Evidence retrieval is deliberately separated from the deterministic safety engine.

```text
Safety Finding
      │
      ▼
Evidence Service
      │
      ├── External source
      ├── Source URL
      ├── Retrieval timestamp
      └── Supporting excerpt
```

Evidence failures do not invalidate the underlying deterministic screening result.

When evidence was requested but configured sources were unavailable:

```text
evidence_unavailable = true
```

---

## 15. LLM / Agent Architecture

The LLM layer is intentionally narrow.

### Agent responsibility

The `PharmacistAgent` converts structured findings into concise pharmacist-facing prose.

### It may

- Summarize findings
- Explain the supplied rationale
- Present findings in readable language

### It must not

- Invent safety facts
- Change severity
- Add interactions
- Add medicines
- Create prescriptions
- Override deterministic rules

If no LLM provider is configured, or the provider fails:

```text
explanation = null
```

The structured safety result remains available.

---

## 16. Recommendations & Alternatives

The recommendation service generates candidate alternatives from the configured Kenya drug catalogue/inventory.

Each candidate is safety-screened against the same patient context and medication rules.

Results contain both:

```text
Included candidate
    └── included_reason

Excluded candidate
    └── excluded_reason
```

An excluded candidate is not silently removed.

Where inventory-aware mode is enabled, an unavailable candidate can be excluded with:

```text
OUT_OF_STOCK
```

---

## 17. Health & Failure Handling

The system follows a fail-safe information-handling philosophy:

```text
Clinical rules fail
        ↓
Do not fabricate a result

Drug resolution fails
        ↓
Explicit UNRESOLVED_DRUG

Required patient context missing
        ↓
INCOMPLETE_CONTEXT

Evidence service fails
        ↓
Return result + evidence_unavailable

LLM fails
        ↓
Return structured result + explanation=null
```

---

## 18. Auditability

Screening responses expose:

```text
ruleset_version
catalogue_version
```

Individual findings expose:

```text
rule_id
```

The frontend displays this metadata through `AuditMeta`, allowing a pharmacist to identify the ruleset and catalogue snapshot behind a result.

---

## 19. Development Contracts

### Backend

Every Python module must have a module-level docstring.

Every public class/function must have appropriate Google-style documentation containing relevant:

```text
Args
Returns
Raises
Notes
```

Pydantic and SQLAlchemy fields must also be documented where their meaning is not self-evident.

### Backend dependency rules

```text
API
 └── may import schemas/services

Services
 └── must not import API handlers

Rules
 └── pure functions
 └── no I/O
 └── no database sessions
 └── no rule-to-rule imports

Repositories
 └── persistence-specific queries

Evidence
 └── external API isolation

Scraper
 └── offline ingestion only

Exceptions
 └── domain layer
 └── translated to HTTP only by API
```

### Frontend

Every exported component, hook, API client function, type, or interface requiring clarification must have appropriate TSDoc documentation.

Frontend types must mirror backend schemas field-for-field.

---

## 20. Testing Priorities

The MVP should demonstrate at least one rule-backed scenario for every in-scope safety dimension:

```text
✓ Drug-drug interaction
✓ Direct allergy
✓ Allergy cross-reactivity
✓ Pregnancy
✓ Renal impairment
✓ Hepatic impairment
✓ Hyperkalemia
✓ G6PD deficiency
✓ Respiratory condition
✓ Age-based caution
✓ Duplicate therapy
✓ Unresolved drug
```

Testing should also verify:

- Rules execute in the defined order.
- Rule functions are deterministic.
- Unknown clinical context is not converted into normal/safe context.
- Unresolved drugs are not silently accepted.
- LLM failure does not remove structured findings.
- Evidence-service failure does not block screening.
- Excluded recommendation candidates retain their reasons.
- Frontend renders every `FindingType` distinctly.
- Frontend does not display stale screening results for a different patient/medication set.
- API failures display error states rather than fabricated clinical information.

---

## 21. Current MVP Boundaries

### Included

- Synthetic patient data
- Patient context retrieval
- Medication history/current prescriptions
- Medication catalogue lookup
- Deterministic medication safety screening
- Multiple patient-specific safety dimensions
- Evidence retrieval
- Optional LLM explanation
- Safety-filtered alternative candidates
- PPB catalogue ingestion
- Ruleset/catalogue traceability
- Pharmacist-oriented frontend

### Broader product direction

The architecture is intended to support future:

- Ward-round assistance
- Admission medication reconciliation
- Discharge medication reconciliation
- Drug information/advisory
- Inventory-aware medication alternatives
- Longitudinal medication review

These are product directions rather than claims that all capabilities are already implemented in the MVP.

---

## 22. Revision 2 Changes

Revision 2 broadens the medication-safety scope beyond pregnancy and expands the architecture accordingly.

Key changes include:

- Added `age_based_rules.py`
- Added `core/exceptions.py`
- Added explicit rule tables for:
  - Condition-drug contraindications
  - Pregnancy warnings
  - Allergy cross-reactivity
- Expanded `SafetyFinding.type` from six categories to twelve
- Added explicit renal, hepatic, hyperkalemia, G6PD, respiratory, and age-based findings
- Consolidated the repository layout into the unified backend/frontend structure

---

## 23. Project Status

| Property | Value |
|---|---|
| Project | OmniPharma |
| Purpose | Agentic medication-safety and clinical decision support |
| Primary users | Pharmacists and clinical teams |
| MVP focus | Demonstrable medication-safety workflow |
| Backend | FastAPI / Python |
| Frontend | React / TypeScript |
| Drug catalogue | PPB registered-product ingestion |
| Safety engine | Deterministic rule modules |
| AI layer | Optional LLM-based explanation |
| Evidence | External supporting drug information |
| Decision authority | Pharmacist / clinical professional |

---

## Disclaimer

OmniPharma is designed as a **clinical decision-support prototype**. Its findings, evidence, and alternative candidates are intended to assist professional review and are not a substitute for clinical judgment, prescribing authority, institutional protocols, or validated clinical decision-support systems.
