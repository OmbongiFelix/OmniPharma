import type { EvidenceItem } from "./medication";

/**
 * Every distinct finding category the backend can emit. Kept as a
 * union rather than a plain string so a missing case in a switch/map is
 * a compile error, not a silent fallback render.
 */
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

/**
 * Finding severity rating.
 */
export type Severity = "INFO" | "LOW" | "MODERATE" | "HIGH" | "CONTRAINDICATED";

/**
 * One machine-readable safety finding, as returned inside
 * `ScreeningResponse.findings`.
 */
export interface SafetyFinding {
  /** Machine-readable finding category. */
  type: FindingType;
  /** Clinical severity classification. */
  severity: Severity;
  /** Canonical names of every medicine involved. */
  medications: string[];
  /** Stable identifier of the rule or row that triggered this finding. */
  ruleId: string;
  /** One-sentence pharmacist-facing summary. */
  summary: string;
  /** Clinical mechanism and reasoning explanation. */
  rationale: string;
  /** Supporting external evidence items. */
  evidence: EvidenceItem[];
  /** True if external evidence was requested but failed or timed out. */
  evidenceUnavailable: boolean;
}

/**
 * Request payload for `POST /api/v1/screenings/interaction`.
 */
export interface ScreeningRequest {
  /** Internal patient identifier. */
  patientId: number;
  /** Drug names or catalogue IDs to screen. */
  medications: string[];
  /** Whether to attach external evidence per finding. */
  includeEvidence?: boolean;
}

/**
 * Request payload for `POST /api/v1/recommendations`.
 */
export interface RecommendationRequest {
  /** Internal patient identifier. */
  patientId: number;
  /** The medicine being replaced or reconsidered. */
  targetMedication: string;
  /** Optional clinical indication filter. */
  indication?: string;
}

/**
 * One alternative-medicine candidate. Excluded candidates are always
 * included in the array with `excluded: true` — never filtered out
 * client-side, since the exclusion reason is the point.
 */
export interface Recommendation {
  /** Canonical name of candidate medicine. */
  drugName: string;
  /** True if candidate was excluded due to a contraindication or policy. */
  excluded: boolean;
  /** Clinical rationale for inclusion when excluded is false. */
  includedReason?: string;
  /** Specific rule or finding that disqualified this candidate when excluded is true. */
  excludedReason?: string;
  /** Inventory status string when available. */
  availability?: string;
}

/**
 * Full response from `POST /api/v1/screenings/interaction`.
 */
export interface ScreeningResponse {
  /** Echoed patient ID. */
  patientId: number;
  /** Overall screening status: CLEAR | REVIEW_REQUIRED | CONTRAINDICATED | INCOMPLETE_CONTEXT. */
  status: "CLEAR" | "REVIEW_REQUIRED" | "CONTRAINDICATED" | "INCOMPLETE_CONTEXT";
  /** Structured findings in rule-category priority order. */
  findings: SafetyFinding[];
  /** Safety-filtered alternative medicine options. */
  recommendations: Recommendation[];
  /** Version tag of clinical ruleset evaluated. */
  rulesetVersion: string;
  /** Version / snapshot timestamp of drug catalogue used. */
  catalogueVersion: string;
  /** Optional narrative explanation from AI pharmacist agent. */
  explanation: string | null;
  /** Injected or extracted request ID for audit traceability. */
  requestId?: string;
}
