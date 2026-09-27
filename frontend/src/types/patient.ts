/**
 * Patient data models matching the backend Pydantic schemas.
 */

/** One active or historical condition on a patient's record. */
export interface ConditionRecord {
  /** ICD-10 or synthetic code. */
  conditionCode: string;
  /** Human-readable diagnosis name. */
  conditionName: string;
  /** Status of condition: ACTIVE, RESOLVED, or CHRONIC. */
  status: "ACTIVE" | "RESOLVED" | "CHRONIC" | string;
  /** ISO-8601 onset date string, or null if unrecorded. */
  onsetDate: string | null;
}

/** One recorded allergy. `allergen: "none"` means no known allergies —
 * render as "No known allergies," not as a red allergy chip. */
export interface AllergyRecord {
  /** Allergen substance or "none". */
  allergen: string;
  /** Manifested clinical reaction description. */
  reaction: string;
  /** Reaction severity level. */
  severity: "NONE" | "MILD" | "MODERATE" | "HIGH" | "SEVERE" | "LIFE_THREATENING" | string;
}

/** Current prescription details for a patient. */
export interface PrescriptionRecord {
  /** Foreign key to medication catalogue. */
  medicationId: number;
  /** Display medication name. */
  medicationName: string;
  /** Dose specification (e.g. "500 mg"). */
  dose: string | null;
  /** Frequency (e.g. "twice daily"). */
  frequency: string | null;
  /** Administration route (e.g. "oral"). */
  route: string | null;
  /** ISO-8601 prescription start date. */
  startDate: string | null;
  /** ISO-8601 end date, or null if ongoing. */
  endDate: string | null;
  /** ACTIVE, DISCONTINUED, or COMPLETED. */
  status: "ACTIVE" | "DISCONTINUED" | "COMPLETED" | string;
}

/** Historical medication entry for a patient. */
export interface MedicationHistoryRecord {
  /** Foreign key to medication catalogue. */
  medicationId: number;
  /** Historical medication name. */
  medicationName: string;
  /** Dose taken during historical therapy. */
  dose: string | null;
  /** Dosing frequency during past therapy. */
  frequency: string | null;
  /** ISO-8601 start date. */
  startDate: string | null;
  /** ISO-8601 discontinuation or completion date. */
  endDate: string | null;
  /** Clinical outcome or treatment response. */
  outcome: string | null;
  /** Pharmacist or prescriber notes. */
  notes: string | null;
}

/**
 * Lightweight patient summary returned by `GET /api/v1/patients`.
 */
export interface PatientSummary {
  /** Database patient identifier. */
  id: number;
  /** Human-readable identifier (e.g. OMNI-001). */
  patientCode: string;
  /** Full patient name. */
  name: string;
  /** Biological sex: M or F. */
  sex: "M" | "F" | string;
  /** PREGNANT | NOT_PREGNANT | NOT_APPLICABLE. */
  pregnancyStatus: "PREGNANT" | "NOT_PREGNANT" | "NOT_APPLICABLE" | string;
  /** Renal impairment status. */
  renalStatus: string;
  /** Hepatic impairment status. */
  hepaticStatus: string;
  /** G6PD enzyme status: NORMAL | DEFICIENT | UNKNOWN. */
  g6pdStatus: string;
  /** ISO-8601 birth date. */
  dateOfBirth: string;
}

/**
 * Full clinical context for one patient, as returned by
 * `GET /api/v1/patients/{patient_id}`.
 */
export interface PatientContext {
  /** Database patient identifier. */
  id: number;
  /** Human-readable identifier (e.g. OMNI-001). */
  patientCode: string;
  /** Full patient name. */
  name: string;
  /** ISO-8601 birth date. */
  dateOfBirth: string;
  /** Biological sex: M or F. */
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
  /** Active and chronic diagnoses. */
  conditions: ConditionRecord[];
  /** Documented allergies. */
  allergies: AllergyRecord[];
  /** Active prescriptions. */
  currentPrescriptions?: PrescriptionRecord[];
  /** Historical medication courses. */
  medicationHistory?: MedicationHistoryRecord[];
}

/**
 * Medications container returned by `GET /api/v1/patients/{patient_id}/medications`.
 */
export interface PatientMedications {
  /** Internal patient identifier. */
  patientId: number;
  /** Active prescriptions. */
  currentPrescriptions: PrescriptionRecord[];
  /** Historical prescriptions. */
  medicationHistory: MedicationHistoryRecord[];
}
