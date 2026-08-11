/**
 * Development-only mock adapter.
 *
 * Installed as an Axios adapter when `VITE_USE_MOCK_API=true`, so the whole
 * service layer above it is untouched and production always talks to FastAPI.
 * A Demo Mode banner is shown for as long as this is active.
 *
 * It replays fixtures. It does not simulate anything: the frontend holds no
 * game-theory logic, so any request the fixtures cannot answer returns an
 * explicit error telling the user to connect the real backend rather than
 * silently inventing a result.
 */

import type { AxiosAdapter, AxiosResponse, InternalAxiosRequestConfig } from "axios";
import type { ApiResponse } from "@/types";
import {
  DEMO_EXPERIMENT_ID,
  DEMO_TOURNAMENT_ID,
  MOCK_ANALYSIS,
  MOCK_EXPERIMENT,
  MOCK_EXPERIMENT_RESULTS,
  MOCK_EXPERIMENT_STATISTICS,
  MOCK_MATRIX,
  MOCK_PARTICIPANTS,
  MOCK_STRATEGIES,
  MOCK_SURVEY_STATISTICS,
  MOCK_TOURNAMENT,
  MOCK_TOURNAMENT_MATCHES,
  MOCK_TOURNAMENT_RESULTS,
  MOCK_TOURNAMENT_STATISTICS,
  mockMatchResult,
} from "./fixtures";

const LATENCY_MS = 220;

function envelope<T>(data: T): ApiResponse<T> {
  return { success: true, data, message: "Demo Mode: sample data, not from the backend." };
}

function ok<T>(config: InternalAxiosRequestConfig, data: T): AxiosResponse<ApiResponse<T>> {
  return {
    data: envelope(data),
    status: 200,
    statusText: "OK",
    headers: {},
    config,
  };
}

function notSupported(path: string): never {
  throw Object.assign(new Error("Not available in Demo Mode"), {
    isAxiosError: true,
    response: {
      status: 501,
      data: {
        success: false,
        data: null,
        message:
          "Demo Mode cannot answer this request. Start the FastAPI backend and set " +
          "VITE_USE_MOCK_API=false to use the real simulation engine.",
        errors: [`No fixture for ${path}`],
      },
    },
  });
}

/** True when the body matches the classic matrix the fixture analysis describes. */
function isClassicMatrix(body: unknown): boolean {
  if (!body || typeof body !== "object") return false;
  const matrix = (body as { matrix?: unknown }).matrix;
  if (!matrix || typeof matrix !== "object") return false;
  return JSON.stringify(matrix) === JSON.stringify(MOCK_ANALYSIS.matrix);
}

export const mockAdapter: AxiosAdapter = async (config) => {
  const url = (config.url ?? "").split("?")[0];
  const method = (config.method ?? "get").toLowerCase();
  const body = config.data ? JSON.parse(config.data as string) : undefined;

  await new Promise((resolve) => setTimeout(resolve, LATENCY_MS));

  if (url === "/strategies") return ok(config, MOCK_STRATEGIES);
  if (url.startsWith("/strategies/")) {
    const id = url.split("/")[2];
    const found = MOCK_STRATEGIES.find((strategy) => strategy.id === id);
    return found ? ok(config, found) : notSupported(url);
  }

  if (url === "/payoff-matrices" && method === "get") return ok(config, [MOCK_MATRIX]);
  if (url.startsWith("/payoff-matrices/") && method === "get") return ok(config, MOCK_MATRIX);

  if (url === "/game-theory/analyze") {
    // Analysing an arbitrary matrix requires the backend engine.
    return isClassicMatrix(body) ? ok(config, MOCK_ANALYSIS) : notSupported(url);
  }

  if (url === "/matches/simulate") return ok(config, mockMatchResult());

  if (url === "/tournaments" && method === "get") return ok(config, [MOCK_TOURNAMENT]);
  if (url === `/tournaments/${DEMO_TOURNAMENT_ID}`) return ok(config, MOCK_TOURNAMENT);
  if (url === `/tournaments/${DEMO_TOURNAMENT_ID}/results`)
    return ok(config, MOCK_TOURNAMENT_RESULTS);
  if (url === `/tournaments/${DEMO_TOURNAMENT_ID}/matches`)
    return ok(config, MOCK_TOURNAMENT_MATCHES);
  if (url === `/tournaments/${DEMO_TOURNAMENT_ID}/statistics`)
    return ok(config, MOCK_TOURNAMENT_STATISTICS);

  if (url === "/experiments" && method === "get") return ok(config, [MOCK_EXPERIMENT]);
  if (url === `/experiments/${DEMO_EXPERIMENT_ID}`) return ok(config, MOCK_EXPERIMENT);
  if (url === `/experiments/${DEMO_EXPERIMENT_ID}/participants` && method === "get")
    return ok(config, MOCK_PARTICIPANTS);
  if (url === `/experiments/${DEMO_EXPERIMENT_ID}/results`)
    return ok(config, MOCK_EXPERIMENT_RESULTS);
  if (url === `/experiments/${DEMO_EXPERIMENT_ID}/statistics`)
    return ok(config, MOCK_EXPERIMENT_STATISTICS);
  if (url === `/experiments/${DEMO_EXPERIMENT_ID}/surveys/trust/statistics`)
    return ok(config, MOCK_SURVEY_STATISTICS);

  return notSupported(url);
};
