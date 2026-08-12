/** Strategy catalogue. */

import { get } from "./client";
import type { Strategy } from "@/types";

export const strategyApi = {
  list: () => get<Strategy[]>("/strategies"),

  getById: (id: string) => get<Strategy>(`/strategies/${id}`),
};
