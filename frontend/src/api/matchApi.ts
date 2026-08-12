/** Single-match simulation. */

import { get, post } from "./client";
import type { MatchRequest, MatchResult } from "@/types";

export const matchApi = {
  simulate: (payload: MatchRequest) => post<MatchResult>("/matches/simulate", payload),

  getById: (id: string) => get<MatchResult>(`/matches/${id}`),
};
