/**
 * Feature hooks.
 *
 * Each wraps one API service call in the shared loading/error/refresh shape,
 * so pages stay declarative and no component talks to Axios.
 */

import { useCallback, useEffect, useState } from "react";
import { experimentApi } from "@/api/experimentApi";
import { gameTheoryApi } from "@/api/gameTheoryApi";
import { payoffMatrixApi } from "@/api/payoffMatrixApi";
import { statisticsApi } from "@/api/statisticsApi";
import { strategyApi } from "@/api/strategyApi";
import { surveyApi } from "@/api/surveyApi";
import { tournamentApi } from "@/api/tournamentApi";
import type {
  ApiError,
  ExperimentStatistics,
  GameAnalysis,
  PayoffMatrixInput,
  TournamentStatistics,
} from "@/types";
import { isApiError } from "@/api/client";
import { useApiResource, type ApiResource } from "./useApiResource";

export { useApiAction, useApiResource } from "./useApiResource";

/** The strategy catalogue, loaded from the backend registry. */
export function useStrategies() {
  return useApiResource(() => strategyApi.list(), []);
}

export function usePayoffMatrices() {
  return useApiResource(() => payoffMatrixApi.list(), []);
}

export function useTournaments() {
  return useApiResource(() => tournamentApi.list(), []);
}

export function useTournament(id: string | undefined) {
  return useApiResource(() => tournamentApi.getById(id as string), [id], {
    enabled: Boolean(id),
  });
}

export function useTournamentResults(id: string | undefined, enabled = true) {
  return useApiResource(() => tournamentApi.results(id as string), [id], {
    enabled: Boolean(id) && enabled,
  });
}

export function useTournamentMatches(id: string | undefined) {
  return useApiResource(() => tournamentApi.matches(id as string), [id], {
    enabled: Boolean(id),
  });
}

export function useExperiments() {
  return useApiResource(() => experimentApi.list(), []);
}

export function useExperiment(id: string | undefined) {
  return useApiResource(() => experimentApi.getById(id as string), [id], {
    enabled: Boolean(id),
  });
}

export function useExperimentResults(id: string | undefined) {
  return useApiResource(() => experimentApi.results(id as string), [id], {
    enabled: Boolean(id),
  });
}

export function useParticipants(id: string | undefined) {
  return useApiResource(() => experimentApi.listParticipants(id as string), [id], {
    enabled: Boolean(id),
  });
}

/**
 * Statistics for either kind of study.
 *
 * Overloaded so the `kind` argument narrows the result type: callers get
 * `TournamentStatistics` or `ExperimentStatistics`, never a union to unpick.
 */
export function useStatistics(
  kind: "tournament",
  id: string | undefined,
  enabled?: boolean,
): ApiResource<TournamentStatistics>;
export function useStatistics(
  kind: "experiment",
  id: string | undefined,
  enabled?: boolean,
): ApiResource<ExperimentStatistics>;
export function useStatistics(
  kind: "tournament" | "experiment",
  id: string | undefined,
  enabled = true,
): ApiResource<TournamentStatistics> | ApiResource<ExperimentStatistics> {
  return useApiResource<TournamentStatistics | ExperimentStatistics>(
    () =>
      kind === "tournament"
        ? statisticsApi.tournament(id as string)
        : statisticsApi.experiment(id as string),
    [kind, id],
    { enabled: Boolean(id) && enabled },
  ) as ApiResource<TournamentStatistics> & ApiResource<ExperimentStatistics>;
}

export function useTrustSurveyStatistics(id: string | undefined) {
  return useApiResource(() => surveyApi.statistics(id as string), [id], {
    enabled: Boolean(id),
  });
}

/**
 * Analyse a matrix, re-running whenever the values change.
 *
 * Debounced so that dragging a number input does not fire a request per
 * keystroke. The analysis itself is always the backend's, never local.
 */
export function useGameAnalysis(matrix: PayoffMatrixInput, debounceMs = 400) {
  const [analysis, setAnalysis] = useState<GameAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const serialised = JSON.stringify(matrix);

  const analyse = useCallback(async (payload: PayoffMatrixInput) => {
    setLoading(true);
    setError(null);
    try {
      setAnalysis(await gameTheoryApi.analyzeMatrix(payload));
    } catch (caught) {
      setAnalysis(null);
      setError(
        isApiError(caught)
          ? caught
          : { status: 0, message: "Unexpected error", details: [], isNetworkError: false },
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const parsed = JSON.parse(serialised) as PayoffMatrixInput;
    const timer = window.setTimeout(() => void analyse(parsed), debounceMs);
    return () => window.clearTimeout(timer);
  }, [serialised, debounceMs, analyse]);

  return {
    analysis,
    loading,
    error,
    refresh: () => analyse(JSON.parse(serialised) as PayoffMatrixInput),
  };
}
