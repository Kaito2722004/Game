/** Tournament endpoints, including CSV export URLs. */

import { API_BASE_URL, get, post, requestBlob } from "./client";
import type {
  Tournament,
  TournamentCreateRequest,
  TournamentMatch,
  TournamentMatchDetail,
  TournamentResults,
  TournamentStatistics,
} from "@/types";

export const tournamentApi = {
  list: () => get<Tournament[]>("/tournaments"),

  getById: (id: string) => get<Tournament>(`/tournaments/${id}`),

  create: (payload: TournamentCreateRequest) => post<Tournament>("/tournaments", payload),

  run: (id: string) => post<TournamentResults>(`/tournaments/${id}/run`),

  results: (id: string) => get<TournamentResults>(`/tournaments/${id}/results`),

  matches: (id: string) => get<TournamentMatch[]>(`/tournaments/${id}/matches`),

  matchDetail: (id: string, matchId: string) =>
    get<TournamentMatchDetail>(`/tournaments/${id}/matches/${matchId}`),

  statistics: (id: string) => get<TournamentStatistics>(`/tournaments/${id}/statistics`),

  exportResultsCsv: (id: string) => requestBlob(`/tournaments/${id}/export/results.csv`),

  exportRoundsCsv: (id: string) => requestBlob(`/tournaments/${id}/export/rounds.csv`),

  /** Direct link, for cases where a plain anchor is preferable to a fetch. */
  resultsCsvUrl: (id: string) => `${API_BASE_URL}/tournaments/${id}/export/results.csv`,
};
