import { useCallback, useState } from "react";
import { screenMedications } from "../api/screening";
import type { ScreeningRequest, ScreeningResponse } from "../types/screening";

/**
 * Wraps `POST /api/v1/screenings/interaction` as a mutation.
 *
 * @returns `{ runReview, result, isLoading, error, clearResult }`. `result` and
 *   `error` are both reset to null whenever `runReview` is called
 *   again, so a stale result never lingers next to a new loading spinner.
 *
 * @remarks The caller is responsible for invalidating/clearing `result`
 *   when `patientId` or the medication list changes, per the "State"
 *   requirement in `06_Antigravity_Frontend_Prompt.md` — a screening
 *   result must always show the exact medication set it was run
 *   against, never a stale set left over from a previous selection.
 */
export function useScreening() {
  const [result, setResult] = useState<ScreeningResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const clearResult = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  const runReview = useCallback(async (req: ScreeningRequest): Promise<ScreeningResponse | null> => {
    setIsLoading(true);
    setResult(null);
    setError(null);

    try {
      const response = await screenMedications(req);
      setResult(response);
      setIsLoading(false);
      return response;
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error(String(err));
      setError(errorObj);
      setIsLoading(false);
      return null;
    }
  }, []);

  return {
    runReview,
    result,
    isLoading,
    error,
    clearResult,
  };
}
