import { useEffect, useState, useCallback } from "react";
import { getPatientContext } from "../api/patients";
import type { PatientContext } from "../types/patient";

/**
 * Fetches full patient context for the currently selected patient.
 *
 * @param patientId - Selected patient id, or null when none selected.
 * @returns `{ patient, isLoading, error, refetch }`. Automatically refetches
 *   when `patientId` changes; returns `{ patient: null, isLoading:
 *   false, error: null }` when `patientId` is null, rather than firing
 *   a request with an invalid id.
 */
export function usePatientContext(patientId: number | null) {
  const [patient, setPatient] = useState<PatientContext | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchContext = useCallback(() => {
    if (patientId === null || isNaN(patientId)) {
      setPatient(null);
      setIsLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getPatientContext(patientId)
      .then((data) => {
        if (!cancelled) {
          setPatient(data);
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
  }, [patientId]);

  useEffect(() => {
    const cleanup = fetchContext();
    return cleanup;
  }, [fetchContext]);

  return { patient, isLoading, error, refetch: fetchContext };
}
