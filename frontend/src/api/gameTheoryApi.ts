/** Game-theory analysis endpoints.
 *
 * The backend computes dominance, Nash equilibria and Pareto status. The
 * frontend only displays what comes back.
 */

import { get, post } from "./client";
import type { AnalyzeGameRequest, GameAnalysis, PayoffMatrixInput } from "@/types";

export const gameTheoryApi = {
  analyze: (payload: AnalyzeGameRequest) =>
    post<GameAnalysis>("/game-theory/analyze", payload),

  analyzeMatrix: (matrix: PayoffMatrixInput) =>
    post<GameAnalysis>("/game-theory/analyze", { matrix }),

  analyzeStored: (payoffMatrixId: string) =>
    get<GameAnalysis>(`/game-theory/analyze/${payoffMatrixId}`),
};
