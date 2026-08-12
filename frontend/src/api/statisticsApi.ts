/** Statistics endpoints, shared by the tournament and experiment features. */

import { get } from "./client";
import type { ExperimentStatistics, TournamentStatistics } from "@/types";

export const statisticsApi = {
  tournament: (tournamentId: string) =>
    get<TournamentStatistics>(`/tournaments/${tournamentId}/statistics`),

  experiment: (experimentId: string) =>
    get<ExperimentStatistics>(`/experiments/${experimentId}/statistics`),
};
