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

/**
 * Chart colours for the dark theme.
 *
 * Violet leads, with pink and cyan as supporting series. Cooperate green and
 * defect red keep their meaning and are never used for anything else. All of
 * these clear 3:1 contrast against the card background.
 */
export const CHART_COLORS = {
  cooperate: "#34d399",
  defect: "#fb7185",
  neutral: "#a855f7",
  muted: "#756a86",
  accent: "#8b5cf6",
  playerA: "#a78bfa",
  playerB: "#22d3ee",
} as const;

export const OUTCOME_COLORS: Record<Outcome, string> = {
  CC: "#34d399",
  CD: "#fbbf24",
  DC: "#22d3ee",
  DD: "#fb7185",
};

export const SERIES_PALETTE = [
  "#a855f7",
  "#22d3ee",
  "#ec4899",
  "#34d399",
  "#818cf8",
  "#fbbf24",
  "#fb7185",
  "#c4b5fd",
];
