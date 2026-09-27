import { useEffect, useState } from "react";
import { getPatients } from "../api/patients";
import type { PatientSummary } from "../types/patient";

/**
 * Fetches and caches the patient list for {@link PatientSelector}.
 *
 * @param query - Optional search string, forwarded to
 *   `GET /api/v1/patients?query=`.
 * @returns `{ patients, isLoading, error }`. `patients` is `[]` while
 *   loading, never `undefined`.
 */
export function usePatients(query?: string) {
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getPatients(query)
      .then((data) => {
        if (!cancelled) {
          setPatients(data || []);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)));
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [query]);

  return { patients, isLoading, error };
}
