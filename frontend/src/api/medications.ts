import { apiFetch } from "./client";
import type { DrugDetail, DrugSummary } from "../types/medication";

/**
 * Searches the drug catalogue across canonical names, INNs, and trade names.
 *
 * @param query - Free-text search string; queries with only whitespace return an empty list without calling API.
 * @returns Array of matching drug summaries ranked by relevance.
 */
export async function searchMedications(query: string): Promise<DrugSummary[]> {
  const trimmed = query.trim();
  if (!trimmed) {
    return [];
  }
  return apiFetch<DrugSummary[]>(`/api/v1/medications/search?q=${encodeURIComponent(trimmed)}`);
}

/**
 * Fetches full drug details including inventory counts and facility status.
 *
 * @param drugId - Database primary key of the medication.
 * @returns Detailed medication model with inventory counts and registration provenance.
 */
export async function getMedicationDetail(drugId: number): Promise<DrugDetail> {
  return apiFetch<DrugDetail>(`/api/v1/medications/${drugId}`);
}
