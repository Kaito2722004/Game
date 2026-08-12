import { useCallback, useEffect, useRef, useState } from "react";
import { isApiError } from "@/api/client";
import type { ApiError } from "@/types";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

export interface ApiResource<T> extends AsyncState<T> {
  /** Re-run the fetch. Safe to pass straight to a retry button. */
  refresh: () => Promise<void>;
  /** Replace the value locally, e.g. after a mutation returns fresh data. */
  setData: (value: T | null) => void;
}

function normalise(error: unknown): ApiError {
  if (isApiError(error)) return error;
  return {
    status: 0,
    message: error instanceof Error ? error.message : "Unexpected error",
    details: [],
    isNetworkError: false,
  };
}

/**
 * Fetch-on-mount with loading, error and refresh.
 *
 * Small on purpose: this project has no need for a caching data layer, and a
 * predictable hook is easier to reason about than a query library here.
 *
 * `enabled` defers the request (for a route param that is not ready yet).
 */
export function useApiResource<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  options: { enabled?: boolean } = {},
): ApiResource<T> {
  const enabled = options.enabled ?? true;
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: enabled,
    error: null,
  });

  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  // Guards against a slow response from a previous dependency value
  // overwriting a newer one.
  const requestId = useRef(0);

  const run = useCallback(async () => {
    const currentRequest = ++requestId.current;
    setState((previous) => ({ ...previous, loading: true, error: null }));
    try {
      const result = await fetcherRef.current();
      if (currentRequest === requestId.current) {
        setState({ data: result, loading: false, error: null });
      }
    } catch (error) {
      if (currentRequest === requestId.current) {
        setState({ data: null, loading: false, error: normalise(error) });
      }
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      setState({ data: null, loading: false, error: null });
      return;
    }
    void run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, run, ...deps]);

  const setData = useCallback((value: T | null) => {
    setState((previous) => ({ ...previous, data: value }));
  }, []);

  return { ...state, refresh: run, setData };
}

/**
 * Manual action with pending and error state, for buttons and form submits.
 */
export function useApiAction<TArgs extends unknown[], TResult>(
  action: (...args: TArgs) => Promise<TResult>,
) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const actionRef = useRef(action);
  actionRef.current = action;

  const execute = useCallback(async (...args: TArgs): Promise<TResult | null> => {
    setPending(true);
    setError(null);
    try {
      return await actionRef.current(...args);
    } catch (caught) {
      setError(normalise(caught));
      return null;
    } finally {
      setPending(false);
    }
  }, []);

  return { execute, pending, error, clearError: () => setError(null) };
}
