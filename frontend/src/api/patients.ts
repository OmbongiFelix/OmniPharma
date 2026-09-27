import { apiFetch } from "./client";
import type { PatientContext, PatientMedications, PatientSummary } from "../types/patient";

/**
 * Fetches the synthetic patient directory from the backend.
 *
 * @param query - Optional search term filtering by patient name or patient code.
 * @returns Array of lightweight patient summaries.
 */
export async function getPatients(query?: string): Promise<PatientSummary[]> {
  const path = query && query.trim().length > 0 
    ? `/api/v1/patients?q=${encodeURIComponent(query.trim())}` 
    : "/api/v1/patients";
  return apiFetch<PatientSummary[]>(path);
}

/**
 * Retrieves the full clinical context for a specific patient.
 *
 * @param patientId - Database primary key of the patient.
 * @returns Full patient context including conditions, allergies, and history.
 */
export async function getPatientContext(patientId: number): Promise<PatientContext> {
  return apiFetch<PatientContext>(`/api/v1/patients/${patientId}`);
}

/**
 * Retrieves current prescriptions and past medication history for a patient.
 *
 * @param patientId - Database primary key of the patient.
 * @returns Container with active prescriptions and past medication records.
 */
export async function getPatientMedications(patientId: number): Promise<PatientMedications> {
  return apiFetch<PatientMedications>(`/api/v1/patients/${patientId}/medications`);
}
