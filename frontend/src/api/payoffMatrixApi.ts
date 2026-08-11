/** Stored payoff matrices. */

import { del, get, post, put } from "./client";
import type { PayoffMatrix, PayoffMatrixCreate, PayoffMatrixUpdate } from "@/types";

export const payoffMatrixApi = {
  list: () => get<PayoffMatrix[]>("/payoff-matrices"),

  getById: (id: string) => get<PayoffMatrix>(`/payoff-matrices/${id}`),

  create: (payload: PayoffMatrixCreate) => post<PayoffMatrix>("/payoff-matrices", payload),

  update: (id: string, payload: PayoffMatrixUpdate) =>
    put<PayoffMatrix>(`/payoff-matrices/${id}`, payload),

  remove: (id: string) => del<null>(`/payoff-matrices/${id}`),
};
