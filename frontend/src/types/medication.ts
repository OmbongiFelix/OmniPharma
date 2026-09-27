/**
 * Medication catalogue data types.
 */

/**
 * Lightweight catalogue entry for autocomplete and search responses.
 */
export interface DrugSummary {
  /** Database primary key. */
  id: number;
  /** Normalised canonical drug name. */
  canonicalName: string;
  /** International Non-proprietary Name. */
  inn: string | null;
  /** Registered trade name. */
  tradeName: string | null;
  /** Dosage form (e.g. Tablet, Capsule, Injection). */
  dosageForm: string | null;
  /** Dose strength string (e.g. 500 mg). */
  strength: string | null;
  /** Provenance tag (e.g. ppb-scraped, synthetic demo). */
  source: string | null;
}

/**
 * Full catalogue entry for `GET /api/v1/medications/{drug_id}`.
 */
export interface DrugDetail {
  /** Database primary key. */
  id: number;
  /** Normalised canonical drug name. */
  canonicalName: string;
  /** International Non-proprietary Name. */
  inn: string | null;
  /** Registered trade name. */
  tradeName: string | null;
  /** Dosage form. */
  dosageForm: string | null;
  /** Strength. */
  strength: string | null;
  /** Provenance source. */
  source: string | null;
  /** True when at least one positive inventory row exists. */
  inStock: boolean;
  /** Sum of all inventory quantities across facilities. */
  totalQuantity: number;
}

/**
 * Single evidence reference item attached to a safety finding.
 */
export interface EvidenceItem {
  /** Source title or guideline name. */
  title?: string;
  /** Organization or database (e.g. OpenFDA, DailyMed, WHO, BNF). */
  source?: string;
  /** Link to clinical literature or prescribing label. */
  url?: string;
  /** Concise evidence statement or summary. */
  summary?: string;
  /** Snippet or quote from literature. */
  snippet?: string;
  /** Publication or revision date string. */
  publicationDate?: string;
  [key: string]: unknown;
}
