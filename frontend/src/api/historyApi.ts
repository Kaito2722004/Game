/** Combined activity history. */

import { get } from "./client";
import type { HistoryKind, HistoryResponse } from "@/types";

export const historyApi = {
  /** Everything played, newest first. `kind` narrows the list, not the totals. */
  list: (kind?: HistoryKind, limit = 200) =>
    get<HistoryResponse>(
      `/history?limit=${limit}` + (kind ? `&kind=${kind}` : ""),
    ),
};
