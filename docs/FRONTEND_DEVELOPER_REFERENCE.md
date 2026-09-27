**OmniPharma — Frontend Developer Reference & Docstring Contract**

_React/TypeScript module contracts, responsibilities, props, and full TSDoc comments. This is the frontend's equivalent of `BACKEND_DEVELOPER_REFERENCE.md`. `06_Antigravity_Frontend_Prompt.md` references this file directly — every component, hook and API client function Antigravity generates must carry a TSDoc comment that matches the contract given here._

# 1. Package Layout

```
OmniPharma/frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts
│   │   ├── patients.ts
│   │   ├── screening.ts
│   │   └── medications.ts
│   ├── types/
│   │   ├── patient.ts
│   │   ├── medication.ts
│   │   └── screening.ts
│   ├── hooks/
│   │   ├── usePatients.ts
│   │   ├── usePatientContext.ts
│   │   ├── useScreening.ts
│   │   └── useRecommendations.ts
│   ├── components/
│   │   ├── AppShell.tsx
│   │   ├── PatientSelector.tsx
│   │   ├── PatientSummary.tsx
│   │   ├── ConditionsList.tsx
│   │   ├── AllergyList.tsx
│   │   ├── MedicationTable.tsx
│   │   ├── SafetyReviewPanel.tsx
│   │   ├── FindingCard.tsx
│   │   ├── EvidencePanel.tsx
│   │   ├── AlternativeTable.tsx
│   │   ├── DrugSearch.tsx
│   │   ├── LoadingState.tsx
│   │   ├── ErrorState.tsx
│   │   └── AuditMeta.tsx
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   ├── PatientReviewPage.tsx
│   │   ├── SafetyReviewPage.tsx
│   │   ├── AlternativesPage.tsx
│   │   └── DrugDetailsPage.tsx
│   └── config/
│       └── env.ts
├── package.json
├── vite.config.ts
├── .env.example
└── README.md
```

# 2. Docstring Standard

Every exported component, hook and API client function gets a TSDoc block (`/** ... */`) directly above its declaration. A component's doc block always lists `@param props` (or destructured prop docs), what the component renders, and any side effects (data fetching, none, etc.). A hook's doc block always lists its inputs, its returned shape, and its loading/error contract. Every exported TypeScript `type`/`interface` field gets an inline comment where the name alone doesn't make the meaning obvious (e.g. `severity`, `excludedReason`). A component or hook with no doc block, or a doc block that only restates its name, does not satisfy this contract.

# 3. Backend Contract This Frontend Consumes

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

`SafetyFinding.type` values the UI must render distinctly (see `BACKEND_DEVELOPER_REFERENCE.md` Section 3, `app/schemas/screening.py`):
`DRUG_DRUG_INTERACTION | ALLERGY | ALLERGY_CROSS_REACTIVITY | PREGNANCY | RENAL_CONTRAINDICATION | HEPATIC_CONTRAINDICATION | HYPERKALEMIA_RISK | G6PD_CONTRAINDICATION | RESPIRATORY_CONTRAINDICATION | AGE_BASED_CAUTION | DUPLICATE_THERAPY | UNRESOLVED_DRUG`

The UI must not group the five contraindication types plus `PREGNANCY` into one generic "warning" bucket — each needs its own label and icon (see Section 5, `FindingCard`), because collapsing them back into "pregnancy vs. everything else" is exactly the gap this revision is fixing on the backend side.

# 4. Module Reference — API Client and Types

## `src/api/client.ts`

```typescript
/**
 * Configured fetch wrapper for all OmniPharma backend calls.
 *
 * Reads the backend base URL from `import.meta.env.VITE_API_BASE_URL`
 * (see `src/config/env.ts`), attaches a request-ID header, and
 * normalizes non-2xx responses into a thrown `ApiError` so every caller
 * handles failures the same way.
 *
 * @param path - Path relative to the API base URL, e.g. "/api/v1/patients".
 * @param init - Standard fetch RequestInit, merged with default headers.
 * @returns Parsed JSON response body, typed by the caller via a generic.
 * @throws {ApiError} When the response status is not in the 200-299 range.
 *   Carries `status` and the backend's error `detail` string so a
 *   component can distinguish, e.g., a 404 (unknown patient) from a 503
 *   (evidence service unavailable).
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> { /* ... */ }

/**
 * Error type thrown by {@link apiFetch} for any non-2xx response.
 */
export class ApiError extends Error {
  /** HTTP status code returned by the backend. */
  status: number;
  /** Backend-provided error detail, when present. */
  detail?: string;
}
```

## `src/types/patient.ts`

```typescript
/**
 * Full clinical context for one patient, as returned by
 * `GET /api/v1/patients/{patient_id}`.
 */
export interface PatientContext {
  id: number;
  patientCode: string;
  name: string;
  dateOfBirth: string;
  sex: "M" | "F";
  /** PREGNANT | NOT_PREGNANT | NOT_APPLICABLE — NOT_APPLICABLE covers
   * patients for whom pregnancy status is not clinically relevant. */
  pregnancyStatus: "PREGNANT" | "NOT_PREGNANT" | "NOT_APPLICABLE";
  /** NORMAL | MILD_IMPAIRMENT | MODERATE_IMPAIRMENT | SEVERE_IMPAIRMENT | UNKNOWN */
  renalStatus: string;
  /** Same value set as renalStatus. */
  hepaticStatus: string;
  /** NORMAL | DEFICIENT | UNKNOWN. Missing/UNKNOWN must render as an
   * explicit "not recorded" state, never silently as NORMAL. */
  g6pdStatus: string;
  conditions: ConditionRecord[];
  allergies: AllergyRecord[];
}

/** One active or historical condition on a patient's record. */
export interface ConditionRecord {
  conditionCode: string;
  conditionName: string;
  status: "ACTIVE" | "RESOLVED";
  onsetDate: string | null;
}

/** One recorded allergy. `allergen: "none"` means no known allergies —
 * render as "No known allergies," not as a red allergy chip. */
export interface AllergyRecord {
  allergen: string;
  reaction: string;
  severity: "NONE" | "MODERATE" | "HIGH";
}
```

## `src/types/screening.ts`

```typescript
/** Every distinct finding category the backend can emit. Kept as a
 * union rather than a plain string so a missing case in a switch/map is
 * a compile error, not a silent fallback render. */
export type FindingType =
  | "DRUG_DRUG_INTERACTION"
  | "ALLERGY"
  | "ALLERGY_CROSS_REACTIVITY"
  | "PREGNANCY"
  | "RENAL_CONTRAINDICATION"
  | "HEPATIC_CONTRAINDICATION"
  | "HYPERKALEMIA_RISK"
  | "G6PD_CONTRAINDICATION"
  | "RESPIRATORY_CONTRAINDICATION"
  | "AGE_BASED_CAUTION"
  | "DUPLICATE_THERAPY"
  | "UNRESOLVED_DRUG";

export type Severity = "INFO" | "LOW" | "MODERATE" | "HIGH" | "CONTRAINDICATED";

/** One machine-readable safety finding, as returned inside
 * `ScreeningResponse.findings`. */
export interface SafetyFinding {
  type: FindingType;
  severity: Severity;
  medications: string[];
  ruleId: string;
  summary: string;
  rationale: string;
  evidence: EvidenceItem[];
  evidenceUnavailable: boolean;
}

/** Full response from `POST /api/v1/screenings/interaction`. */
export interface ScreeningResponse {
  patientId: number;
  status: "CLEAR" | "REVIEW_REQUIRED" | "CONTRAINDICATED" | "INCOMPLETE_CONTEXT";
  findings: SafetyFinding[];
  recommendations: Recommendation[];
  rulesetVersion: string;
  catalogueVersion: string;
  explanation: string | null;
}

/** One alternative-medicine candidate. Excluded candidates are always
 * included in the array with `excluded: true` — never filtered out
 * client-side, since the exclusion reason is the point. */
export interface Recommendation {
  drugName: string;
  excluded: boolean;
  includedReason?: string;
  excludedReason?: string;
  availability?: string;
}
```

# 5. Component Reference

## `AppShell`

```typescript
/**
 * Top-level layout: header, patient context bar, and routed page body.
 * Renders {@link ErrorState} at the shell level for any uncaught render
 * error in a page, so one broken page never blanks the whole app.
 *
 * @param props.children - The currently routed page.
 */
```

## `PatientSelector`

```typescript
/**
 * Dropdown/search control for choosing the active demo patient.
 * Fetches the patient list via {@link usePatients} and calls
 * `onSelect` with the chosen patient's id. Renders a "Demo Patient"
 * badge next to every entry, since this dataset is synthetic only.
 *
 * @param props.onSelect - Called with the selected patient's id.
 * @param props.selectedPatientId - Currently selected id, for
 *   highlighting; null when no patient is selected yet.
 */
```

## `PatientSummary`

```typescript
/**
 * Renders demographics, pregnancy status, renal/hepatic/G6PD status for
 * one patient. Any of the four status fields that is `"UNKNOWN"` or
 * missing renders as a visible "not recorded" chip rather than being
 * omitted, per the "make missing context explicit" UX requirement.
 *
 * @param props.patient - Full {@link PatientContext} to summarize.
 */
```

## `ConditionsList` / `AllergyList`

```typescript
/**
 * Renders a patient's active conditions (ConditionsList) or recorded
 * allergies (AllergyList) as a scannable list. AllergyList renders
 * `allergen: "none"` rows as a single "No known allergies" line, not as
 * an empty-looking allergy chip.
 *
 * @param props.items - ConditionRecord[] or AllergyRecord[].
 */
```

## `MedicationTable`

```typescript
/**
 * Renders current prescriptions and/or medication history in a single
 * sortable table, with a status column distinguishing ACTIVE, COMPLETED
 * and STOPPED entries.
 *
 * @param props.prescriptions - Current prescriptions.
 * @param props.history - Past medication history entries.
 * @param props.mode - "current" | "history" | "both" — controls which
 *   rows render; defaults to "both".
 */
```

## `SafetyReviewPanel`

```typescript
/**
 * Owns the "Run Safety Review" action and renders the resulting
 * findings grouped by severity (CONTRAINDICATED and HIGH first). Uses
 * {@link useScreening} for the mutation and shows {@link LoadingState}
 * while a review is in flight and {@link ErrorState} on failure,
 * including a distinct message for `status: "INCOMPLETE_CONTEXT"`
 * versus a network/API error.
 *
 * @param props.patientId - Patient being reviewed.
 * @param props.medicationNames - Exact medicine list being evaluated;
 *   changing this list invalidates any previous result (see Section 6).
 */
```

## `FindingCard`

```typescript
/**
 * Renders one {@link SafetyFinding}. Severity is always communicated
 * with a text label and icon, never color alone. Each of the twelve
 * `FindingType` values maps to its own label and icon in a single
 * exhaustive switch — the switch has no `default` case, so adding a
 * new backend finding type without updating this component is a
 * TypeScript compile error, not a silent generic render.
 *
 * @param props.finding - The finding to render.
 * @param props.expanded - Whether the technical detail (rule id,
 *   rationale, evidence) starts expanded; the concise summary always
 *   renders regardless of this flag.
 */
```

## `EvidencePanel`

```typescript
/**
 * Renders supporting evidence items for a finding, or an explicit
 * "evidence unavailable" state when `finding.evidenceUnavailable` is
 * true, or a "no evidence requested" state when
 * `finding.evidence.length === 0 && !evidenceUnavailable`. These three
 * states must never look the same to the user.
 *
 * @param props.finding - The finding whose evidence is being shown.
 */
```

## `AlternativeTable`

```typescript
/**
 * Renders {@link Recommendation} candidates. Every row is labeled
 * "candidate for pharmacist review," never "prescription" or
 * "recommended dose." Excluded candidates render in a visually distinct
 * (not hidden) section with their `excludedReason`.
 *
 * @param props.recommendations - Full list, included and excluded.
 */
```

## `DrugSearch`

```typescript
/**
 * Autocomplete search box over `GET /api/v1/medications/search`.
 * Debounces input and shows {@link LoadingState} inline while a search
 * is in flight.
 *
 * @param props.onSelect - Called with the chosen drug's catalogue id.
 */
```

## `LoadingState` / `ErrorState`

```typescript
/**
 * Shared loading/error placeholders used by every data-fetching
 * component, so loading and error UI is visually consistent app-wide.
 *
 * @param props.message - Optional context-specific text
 *   (LoadingState) or the error description to show (ErrorState).
 * @param props.retry - Optional retry callback (ErrorState only).
 */
```

## `AuditMeta`

```typescript
/**
 * Renders ruleset version, catalogue version/timestamp, and screening
 * request id in a small, consistently-placed footer on any screen that
 * shows a screening result, so a pharmacist can always see how current
 * the data behind a finding is.
 *
 * @param props.rulesetVersion - From ScreeningResponse.rulesetVersion.
 * @param props.catalogueVersion - From ScreeningResponse.catalogueVersion.
 */
```

# 6. Hook Reference

## `usePatients`

```typescript
/**
 * Fetches and caches the patient list for {@link PatientSelector}.
 *
 * @param query - Optional search string, forwarded to
 *   `GET /api/v1/patients?query=`.
 * @returns `{ patients, isLoading, error }`. `patients` is `[]` while
 *   loading, never `undefined`.
 */
```

## `usePatientContext`

```typescript
/**
 * Fetches full patient context for the currently selected patient.
 *
 * @param patientId - Selected patient id, or null when none selected.
 * @returns `{ patient, isLoading, error }`. Automatically refetches
 *   when `patientId` changes; returns `{ patient: null, isLoading:
 *   false, error: null }` when `patientId` is null, rather than firing
 *   a request with an invalid id.
 */
```

## `useScreening`

```typescript
/**
 * Wraps `POST /api/v1/screenings/interaction` as a mutation.
 *
 * @returns `{ runReview, result, isLoading, error }`. `result` and
 *   `error` are both reset to null whenever `runReview` is called
 *   again, so a stale result never lingers next to a new loading spinner.
 *
 * @remarks The caller is responsible for invalidating/clearing `result`
 *   when `patientId` or the medication list changes, per the "State"
 *   requirement in `06_Antigravity_Frontend_Prompt.md` — a screening
 *   result must always show the exact medication set it was run
 *   against, never a stale set left over from a previous selection.
 */
```

## `useRecommendations`

```typescript
/**
 * Wraps `POST /api/v1/recommendations` as a mutation.
 *
 * @returns `{ fetchRecommendations, recommendations, isLoading, error }`.
 *   `recommendations` includes both included and excluded candidates
 *   (see {@link Recommendation}) — this hook must not filter either out.
 */
```

# 7. Import/Export Rules

- `src/api/*` is the only layer allowed to call `apiFetch`/`fetch` directly. Components and pages must go through a hook in `src/hooks/*`.
- `src/hooks/*` own loading/error/caching state; components must not duplicate that state locally.
- `src/types/*` mirror the backend Pydantic schemas field-for-field (camelCase, per the JSON the backend serializes); if a backend schema field is added or renamed, the matching type here must change in the same commit as the backend change, since there is no separate contract test between them in this hackathon build.
- Components must not construct mock/placeholder clinical data when a request fails — render {@link ErrorState} instead, per the "do not invent missing clinical information" requirement.
