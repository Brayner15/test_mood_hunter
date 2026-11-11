import { useCallback, useState } from "react";

import { fetchSummary, toMessage } from "../api/client";
import type { SummaryResponse } from "../api/types";

export function useSummary() {
  const [result, setResult] = useState<SummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const next = await fetchSummary();
      setResult(next);
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { result, isLoading, error, generate };
}
