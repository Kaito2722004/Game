/** Classroom trust survey. */

import { get, post } from "./client";
import type { TrustSurvey, TrustSurveyRequest, TrustSurveyStatistics } from "@/types";

export const surveyApi = {
  submit: (payload: TrustSurveyRequest) => post<TrustSurvey>("/surveys/trust", payload),

  listForExperiment: (experimentId: string) =>
    get<TrustSurvey[]>(`/experiments/${experimentId}/surveys/trust`),

  statistics: (experimentId: string) =>
    get<TrustSurveyStatistics>(`/experiments/${experimentId}/surveys/trust/statistics`),
};
