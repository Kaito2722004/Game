/**
 * Presentation helpers for game concepts.
 *
 * These are labels and colours only. Every game-theoretic *result* comes from
 * the backend; nothing here decides an equilibrium or a score.
 */

import type { Action, Outcome } from "@/types";

export const OUTCOME_LABELS: Record<Outcome, string> = {
  CC: "Mutual Cooperation",
  CD: "A cooperates, B defects",
  DC: "A defects, B cooperates",
  DD: "Mutual Defection",
};

export const OUTCOME_DESCRIPTIONS: Record<Outcome, string> = {
  CC: "Both players cooperated. Each earns the reward payoff R.",
  CD: "Player A cooperated while Player B defected. A receives the sucker's payoff S, B the temptation payoff T.",
  DC: "Player A defected while Player B cooperated. A receives the temptation payoff T, B the sucker's payoff S.",
  DD: "Both players defected. Each earns the punishment payoff P.",
};

export const OUTCOME_ORDER: Outcome[] = ["CC", "CD", "DC", "DD"];

export function actionLabel(action: Action): string {
  return action === "COOPERATE" ? "Cooperate" : "Defect";
}

export function actionShort(action: Action): "C" | "D" {
  return action === "COOPERATE" ? "C" : "D";
}

/** Chart colours. Text labels always accompany these in the UI. */
export const CHART_COLORS = {
  cooperate: "#15803d",
  defect: "#b91c1c",
  neutral: "#2563eb",
  muted: "#64748b",
  accent: "#7c3aed",
  playerA: "#2563eb",
  playerB: "#ea580c",
} as const;

export const OUTCOME_COLORS: Record<Outcome, string> = {
  CC: "#15803d",
  CD: "#f59e0b",
  DC: "#8b5cf6",
  DD: "#b91c1c",
};

export const SERIES_PALETTE = [
  "#2563eb",
  "#15803d",
  "#b91c1c",
  "#ea580c",
  "#7c3aed",
  "#0891b2",
  "#ca8a04",
  "#db2777",
];
