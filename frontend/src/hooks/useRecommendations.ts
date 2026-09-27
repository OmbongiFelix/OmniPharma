import { useCallback, useState } from "react";
import { fetchRecommendations as apiFetchRecommendations } from "../api/screening";
import type { Recommendation, RecommendationRequest } from "../types/screening";

/**
 * Wraps `POST /api/v1/recommendations` as a mutation.
 *
 * @returns `{ fetchRecommendations, recommendations, isLoading, error, clearRecommendations }`.
 *   `recommendations` includes both included and excluded candidates
 *   (see {@link Recommendation}) — this hook must not filter either out.
 */
export function useRecommendations() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const clearRecommendations = useCallback(() => {
    setRecommendations([]);
    setError(null);
  }, []);

  const fetchRecommendations = useCallback(
    async (req: RecommendationRequest): Promise<Recommendation[]> => {
      setIsLoading(true);
      setError(null);

      try {
        const results = await apiFetchRecommendations(req);
        // Retain both included and excluded candidates without filtering
        setRecommendations(results || []);
        setIsLoading(false);
        return results || [];
      } catch (err) {
        const errorObj = err instanceof Error ? err : new Error(String(err));
        setError(errorObj);
        setIsLoading(false);
        return [];
      }
    },
    []
  );

  return {
    fetchRecommendations,
    recommendations,
    isLoading,
    error,
    clearRecommendations,
  };
}
