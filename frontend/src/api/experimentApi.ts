/** Human classroom experiment endpoints. */

import { del, get, post, put, requestBlob } from "./client";
import type {
  Experiment,
  ExperimentCreateRequest,
  ExperimentResults,
  ExperimentStart,
  ExperimentStatistics,
  HumanRound,
  Participant,
  RoundSubmission,
} from "@/types";

export const experimentApi = {
  list: () => get<Experiment[]>("/experiments"),

  getById: (id: string) => get<Experiment>(`/experiments/${id}`),

  create: (payload: ExperimentCreateRequest) => post<Experiment>("/experiments", payload),

  update: (id: string, payload: Partial<ExperimentCreateRequest>) =>
    put<Experiment>(`/experiments/${id}`, payload),

  listParticipants: (id: string) => get<Participant[]>(`/experiments/${id}/participants`),

  addParticipant: (id: string, payload: { code: string; display_name?: string | null }) =>
    post<Participant>(`/experiments/${id}/participants`, payload),

  removeParticipant: (id: string, participantId: string) =>
    del<null>(`/experiments/${id}/participants/${participantId}`),

  /** Randomly pairs participants and opens the experiment for rounds. */
  start: (id: string, seed?: number | null) =>
    post<ExperimentStart>(
      `/experiments/${id}/start${seed !== undefined && seed !== null ? `?seed=${seed}` : ""}`,
    ),

  complete: (id: string) => post<Experiment>(`/experiments/${id}/complete`),

  /** Payoffs are computed by the backend; only the two actions are sent. */
  submitRound: (id: string, payload: RoundSubmission) =>
    post<HumanRound>(`/experiments/${id}/rounds`, payload),

  results: (id: string) => get<ExperimentResults>(`/experiments/${id}/results`),

  statistics: (id: string) => get<ExperimentStatistics>(`/experiments/${id}/statistics`),

  exportRoundsCsv: (id: string) => requestBlob(`/experiments/${id}/export/rounds.csv`),

  exportSurveysCsv: (id: string) => requestBlob(`/experiments/${id}/export/surveys.csv`),
};
