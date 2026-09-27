Build the OmniPharma frontend for the FastAPI backend described below.

READ FIRST
Before writing any code, read `../docs/FRONTEND_DEVELOPER_REFERENCE.md` in full. That file is the
authoritative component/hook/TSDoc contract for this frontend — the same role
`../docs/BACKEND_DEVELOPER_REFERENCE.md` plays for the backend. Every exported component, hook and API
client function you generate must carry a TSDoc comment matching the contract given there. If anything
below conflicts with that file, the reference file wins.

REPO LOCATION
This frontend is a subdirectory of a single combined repo: build it at `OmniPharma/frontend/`, as a
sibling of `OmniPharma/backend/` (built separately from `05_Antigravity_Backend_Prompt.md`) and
`OmniPharma/docs/` (shared specs). Do not create a separate top-level project for the frontend.

GOAL
Create a pharmacist-facing clinical decision-support dashboard. The UI should make medication safety
findings easy to inspect, not hide them behind a chatbot. The primary workflow is:
Patient -> current/history medicines -> run safety review -> findings -> evidence -> alternatives ->
pharmacist review.

Findings are not pregnancy-only. The backend returns twelve distinct finding types (drug-drug,
allergy, allergy cross-reactivity, pregnancy, renal, hepatic, hyperkalemia, G6PD, respiratory,
age-based, duplicate therapy, unresolved drug — see `../docs/FRONTEND_DEVELOPER_REFERENCE.md` Section
3) and the UI must give each its own label/icon, not collapse everything into "pregnancy vs.
everything else."

BACKEND CONTRACT
```
GET /api/v1/health
GET /api/v1/patients
GET /api/v1/patients/{patient_id}
GET /api/v1/patients/{patient_id}/medications
GET /api/v1/medications/search?q=...
POST /api/v1/screenings/interaction
POST /api/v1/recommendations
```
Full response shapes, including the `FindingType` and `Severity` unions, are defined in
`../docs/FRONTEND_DEVELOPER_REFERENCE.md` Section 4 — implement `src/types/*` to match those exactly.

PREFERRED STACK
Use React + TypeScript + Vite. Use a clean component architecture and a query/data-fetching library if
appropriate. Keep the backend base URL configurable via `VITE_API_BASE_URL` (see
`OmniPharma/frontend/.env.example`).

SCREENS
1. Dashboard
   - patient search/select
   - recent reviews
   - high-level counts of active alerts, broken down by finding category (not just a single total)
2. Patient Review
   - patient demographics
   - pregnancy status
   - renal / hepatic / G6PD status (each shown even when "not recorded" — see Section 5,
     `PatientSummary`, in the frontend reference)
   - allergies
   - conditions
   - current medications
   - medication history
3. Medication Safety Review
   - selected medicines
   - "Run Safety Review" action
   - findings grouped by severity
   - affected medicines
   - rule ID
   - rationale
   - evidence/source
   - review-required status
4. Alternative Medicines
   - indication/target medicine
   - candidate medicines
   - availability
   - why candidate is included
   - why other candidates were excluded (always shown, never hidden)
5. Drug Details
   - trade name
   - INN/API
   - dosage form
   - registration/source information
   - evidence links

UX REQUIREMENTS
- Clear visual distinction between information, warning, high-risk and contraindicated findings.
- Never use color alone to communicate severity; include labels/icons/text.
- Show patient context prominently before displaying recommendations.
- Make missing context explicit — a status of "not recorded" is a visible state, never an omitted field.
- Provide loading, empty, error and stale-data states.
- Show catalogue/evidence timestamps.
- Do not present an alternative as a prescription; label it "candidate for pharmacist review."
- Provide a concise explanation plus expandable technical detail.
- Make the interface desktop-first but responsive.
- Use accessible semantic HTML and keyboard navigation.

DEMO MODE
Include a "Demo Patient" selector and make the expanded synthetic database (see
`../docs/10_Mock_Data_Expansion_Spec.md`) easy to demonstrate — the selector should make it obvious
which patient illustrates which finding category (pregnancy, renal, hepatic, G6PD, respiratory,
hyperkalemia, age-based) so the demo can move through categories quickly. Do not add real patient
information.

COMPONENTS
Build exactly the components specified in `../docs/FRONTEND_DEVELOPER_REFERENCE.md` Section 5:
AppShell, PatientSelector, PatientSummary, ConditionsList, AllergyList, MedicationTable,
SafetyReviewPanel, FindingCard, EvidencePanel, AlternativeTable, DrugSearch, LoadingState, ErrorState,
AuditMeta. `FindingCard` in particular must use an exhaustive switch over `FindingType` with no
default case, per the reference doc — this is what guarantees a new backend finding type can't render
as a generic, unlabeled block.

STATE
Keep patient context and screening results separate (see `usePatients`, `usePatientContext`,
`useScreening`, `useRecommendations` in `../docs/FRONTEND_DEVELOPER_REFERENCE.md` Section 6). A
screening result should show the exact medication set that was evaluated. Invalidate/refetch results
when patient or medication selection changes.

ERROR HANDLING
Handle 4xx/5xx API errors, unresolved drugs, `status: "INCOMPLETE_CONTEXT"`, and
`evidence_unavailable: true` as distinct, clearly labeled states. Do not invent missing clinical
information.

OUTPUT
Generate the complete frontend code, package configuration, README (at
`OmniPharma/frontend/README.md`), `.env.example`, and API client types. Use mocked API responses only
as a development fallback; the production/demo configuration must point to the FastAPI backend at
`OmniPharma/backend/`.
