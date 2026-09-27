**OmniPharma — Agent Architectural Design**

_Hybrid agent: deterministic clinical safety + retrieval + constrained LLM explanation. Revision 2: broadened safety-rule taxonomy beyond pregnancy._

# 1. Architectural Principle

Use a hybrid architecture. The agent orchestrates tools and explains results, but deterministic safety rules and structured data retrieval remain authoritative for the hackathon's medication-safety checks. This reduces the risk of hallucinated interactions or contraindications.

# 2. Logical Architecture

```
User / Pharmacist
        |
        v
    Frontend (OmniPharma/frontend)
        |
        v
FastAPI API Gateway (OmniPharma/backend)
        |
        v
  Agent Orchestrator
   |    |    |    |
   |    |    |    +--> Evidence Service --> openFDA / configured sources
   |    |    |
   |    |    +-----------> Recommendation Service --> PPB Catalogue + Inventory
   |    |
   |    +--------------------> Patient Service --> Patient DB
   |
   +----------------------------> Safety Engine
        |--> Drug-Drug rules
        |--> Allergy rules (incl. cross-reactivity)
        |--> Pregnancy rules
        |--> Condition/contraindication rules (renal, hepatic, hyperkalemia,
        |     G6PD, respiratory)
        |--> Age-based caution rules
        |--> Duplicate-therapy rules
        |
        v
  Structured Findings
        |
        v
  LLM Explanation Layer
        |
        v
  Pharmacist Review UI
```

# 3. Agent State

- Request state: user intent, patient ID, target medicines and indication.
- Patient context: demographics (including derived age), allergies, conditions, pregnancy status, renal status, hepatic status, G6PD status, medication history and current medicines.
- Medication context: canonical drug ID, trade name, INN/API, dosage form and source.
- Safety findings: finding type, severity, affected drugs, rule ID, rationale and evidence source.
- Recommendation context: candidate drugs, reasons included/excluded, catalogue/stock status.
- Audit context: timestamp, request ID, ruleset version and source versions.

# 4. Agent Tools

- `get_patient_context(patient_id)`
- `resolve_drug(name)`
- `search_drug_catalog(query)`
- `screen_drug_pairs(medications)`
- `screen_patient_constraints(patient, medication)` — dispatches to allergy, pregnancy, condition-contraindication, and age-based sub-checks
- `search_inventory(drug_id)`
- `get_drug_evidence(drug_id)`
- `filter_alternatives(patient, target, indication)`

# 5. Decision Flow

1. Classify the request: review, interaction check, drug information or alternative search.
2. Retrieve patient and medication context.
3. Resolve all medicine names to canonical records; stop or flag unresolved drugs rather than guessing.
4. Run deterministic safety rules, in this fixed order so severity is never overwritten by a later, less specific rule:
   a. Drug–drug interactions
   b. Allergy conflicts (direct and cross-reactive)
   c. Pregnancy warnings (only if `pregnancy_status == PREGNANT`)
   d. Condition–drug contraindications (renal, hepatic, hyperkalemia, G6PD, respiratory)
   e. Age-based caution
   f. Duplicate therapy
5. Retrieve supporting evidence where required.
6. For alternatives, generate a candidate set from the local catalogue and inventory, then safety-filter candidates through the same six checks.
7. Ask the LLM only to synthesize the structured findings into a pharmacist-readable explanation.
8. Return structured JSON plus an explanation and explicit review status.

# 6. Severity Model

Use severity as a clinical rule output rather than an LLM judgment: `INFO`, `LOW`, `MODERATE`, `HIGH`, `CONTRAINDICATED`. Each severity must be tied to a rule/evidence record. A condition-contraindication or pregnancy-warning finding uses the same severity scale as a drug-drug interaction finding — the frontend must not treat them as a lesser category of alert.

# 7. Failure Modes

- Unknown drug name → return unresolved medication and request confirmation.
- External evidence service unavailable → use cached/local rules and clearly mark external evidence unavailable.
- Patient context incomplete → show missing fields; do not infer pregnancy, allergies, renal/hepatic status, G6PD status, or conditions.
- LLM unavailable → return deterministic findings without narrative synthesis.
- PPB scraper unavailable → continue with last successful catalogue snapshot and expose catalogue timestamp.
- Conflicting evidence → display source disagreement and require pharmacist review.
- Renal/hepatic/G6PD status recorded as `UNKNOWN` → surface as a data-gap warning rather than silently skipping the corresponding rule category.

# 8. Security and Privacy

- Use synthetic data for the hackathon.
- Do not place patient identifiers in logs or LLM prompts when not necessary.
- Separate authentication/authorization from clinical rule execution.
- Version the rules and catalogue snapshot used for each screening.
- Treat external API responses as untrusted input.

# 9. Architecture Decision

Do not make the LLM responsible for discovering interactions from raw prose. The supplied API notes correctly identify that openFDA labeling can require parsing; therefore, openFDA should primarily provide supporting evidence unless a validated extraction pipeline is introduced. The interaction engine should start with structured rules and a dedicated interaction source.

**Revision 2 decision:** pregnancy was the only condition-based rule category with real data-model backing in revision 1 (there was no table for condition-drug contraindications at all). Treating pregnancy as architecturally special was an oversight rather than a deliberate choice — clinically, renal impairment, hepatic impairment, G6PD deficiency, hyperkalemia risk and reactive airway disease are just as likely to change what's safe to prescribe. `condition_drug_contraindications` and `pregnancy_drug_warnings` are now sibling tables with an identical shape (see `04_FastAPI_Backend_Design.md`), and `contraindication_rules.py` and `pregnancy_rules.py` are sibling modules with an identical contract (see `BACKEND_DEVELOPER_REFERENCE.md`).
