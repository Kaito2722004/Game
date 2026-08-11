/**
 * Sample data for Demo Mode.
 *
 * These are fixed fixtures, not computed results. The frontend deliberately
 * contains no simulation or game-theory logic, so the mock cannot analyse an
 * arbitrary matrix or play a match — it can only replay a recorded example.
 * Anything shown from here is labelled Demo Mode in the interface.
 */

import type {
  Experiment,
  ExperimentResults,
  ExperimentStatistics,
  GameAnalysis,
  MatchResult,
  Participant,
  PayoffMatrix,
  RoundResult,
  Strategy,
  Tournament,
  TournamentMatch,
  TournamentResults,
  TournamentStatistics,
  TrustSurveyStatistics,
} from "@/types";

export const DEMO_TOURNAMENT_ID = "11111111-1111-4111-8111-111111111111";
export const DEMO_EXPERIMENT_ID = "22222222-2222-4222-8222-222222222222";
export const DEMO_MATRIX_ID = "33333333-3333-4333-8333-333333333333";

const NOW = "2024-01-01T09:00:00Z";

export const MOCK_STRATEGIES: Strategy[] = [
  {
    id: "ALWAYS_COOPERATE",
    name: "Always Cooperate",
    description:
      "Cooperates unconditionally. It is exploited by any strategy that defects, but it never provokes retaliation.",
    rules: ["Play COOPERATE in every round."],
    category: "NICE",
    is_deterministic: true,
  },
  {
    id: "ALWAYS_DEFECT",
    name: "Always Defect",
    description:
      "Defects unconditionally. It plays the dominant action of the one-shot game in every round of the repeated game.",
    rules: ["Play DEFECT in every round."],
    category: "NASTY",
    is_deterministic: true,
  },
  {
    id: "TIT_FOR_TAT",
    name: "Tit-for-Tat",
    description:
      "Opens with cooperation and then copies whatever the opponent did in the previous round.",
    rules: [
      "Play COOPERATE in the first round.",
      "In every later round, repeat the opponent's action from the previous round.",
    ],
    category: "NICE",
    is_deterministic: true,
  },
  {
    id: "GRIM_TRIGGER",
    name: "Grim Trigger",
    description:
      "Cooperates until the opponent's first defection, then defects for the remainder of the match.",
    rules: [
      "Play COOPERATE while the opponent has never defected.",
      "Once the opponent has defected at least once, play DEFECT in every remaining round.",
    ],
    category: "NICE",
    is_deterministic: true,
  },
  {
    id: "TIT_FOR_TWO_TATS",
    name: "Tit-for-Two-Tats",
    description: "Cooperates unless the opponent defected in both of the two previous rounds.",
    rules: [
      "Play COOPERATE in the first two rounds.",
      "Play DEFECT only when the opponent defected in each of the previous two rounds.",
      "Otherwise play COOPERATE.",
    ],
    category: "NICE",
    is_deterministic: true,
  },
  {
    id: "RANDOM",
    name: "Random",
    description:
      "Chooses COOPERATE or DEFECT with probability 0.5 each, independently of the history of the match.",
    rules: ["Play COOPERATE with probability 0.5, otherwise DEFECT."],
    category: "STOCHASTIC",
    is_deterministic: false,
  },
];

export const MOCK_MATRIX: PayoffMatrix = {
  id: DEMO_MATRIX_ID,
  name: "Classic Prisoner's Dilemma (sample)",
  description: "T=5, R=3, P=1, S=0.",
  cc: { player_a_payoff: 3, player_b_payoff: 3 },
  cd: { player_a_payoff: 0, player_b_payoff: 5 },
  dc: { player_a_payoff: 5, player_b_payoff: 0 },
  dd: { player_a_payoff: 1, player_b_payoff: 1 },
  is_default: true,
  created_at: NOW,
  updated_at: NOW,
};

/** Recorded analysis of the classic matrix only. */
export const MOCK_ANALYSIS: GameAnalysis = {
  matrix: {
    cc: MOCK_MATRIX.cc,
    cd: MOCK_MATRIX.cd,
    dc: MOCK_MATRIX.dc,
    dd: MOCK_MATRIX.dd,
  },
  conditions: {
    is_prisoners_dilemma: true,
    ordering_holds: true,
    averaging_condition_holds: true,
    is_symmetric: true,
    player_a: {
      player: "A",
      temptation: 5,
      reward: 3,
      punishment: 1,
      sucker: 0,
      ordering_holds: true,
      averaging_condition_holds: true,
    },
    player_b: {
      player: "B",
      temptation: 5,
      reward: 3,
      punishment: 1,
      sucker: 0,
      ordering_holds: true,
      averaging_condition_holds: true,
    },
    failed_conditions: [],
  },
  dominant_strategy_player_a: {
    player: "A",
    exists: true,
    action: "DEFECT",
    dominance: "STRICT",
    explanation:
      "DEFECT strictly dominates for player A: if the opponent plays COOPERATE, DEFECT pays 5 versus 3; if the opponent plays DEFECT, DEFECT pays 1 versus 0.",
  },
  dominant_strategy_player_b: {
    player: "B",
    exists: true,
    action: "DEFECT",
    dominance: "STRICT",
    explanation:
      "DEFECT strictly dominates for player B: if the opponent plays COOPERATE, DEFECT pays 5 versus 3; if the opponent plays DEFECT, DEFECT pays 1 versus 0.",
  },
  nash_equilibria: [
    {
      outcome: "DD",
      player_a_action: "DEFECT",
      player_b_action: "DEFECT",
      player_a_payoff: 1,
      player_b_payoff: 1,
      explanation:
        "(DEFECT, DEFECT) is a Nash equilibrium: A switching alone would move from 1 to 0, and B switching alone would move from 1 to 0.",
    },
  ],
  pareto_analysis: [
    {
      outcome: "CC",
      player_a_payoff: 3,
      player_b_payoff: 3,
      is_pareto_optimal: true,
      dominated_by: [],
      explanation:
        "CC is Pareto-optimal: no other outcome improves one player without making the other worse off.",
    },
    {
      outcome: "CD",
      player_a_payoff: 0,
      player_b_payoff: 5,
      is_pareto_optimal: true,
      dominated_by: [],
      explanation:
        "CD is Pareto-optimal: no other outcome improves one player without making the other worse off.",
    },
    {
      outcome: "DC",
      player_a_payoff: 5,
      player_b_payoff: 0,
      is_pareto_optimal: true,
      dominated_by: [],
      explanation:
        "DC is Pareto-optimal: no other outcome improves one player without making the other worse off.",
    },
    {
      outcome: "DD",
      player_a_payoff: 1,
      player_b_payoff: 1,
      is_pareto_optimal: false,
      dominated_by: ["CC"],
      explanation: "DD (1,1) is Pareto-inferior to CC (3,3).",
    },
  ],
  pareto_optimal_outcomes: ["CC", "CD", "DC"],
  pareto_inferior_outcomes: ["DD"],
  mutual_cooperation_pareto_superior_to_mutual_defection: true,
  equilibrium_is_pareto_inferior: true,
  summary:
    "This matrix satisfies the Prisoner's Dilemma conditions. Player A has a dominant action (DEFECT) and player B has a dominant action (DEFECT). Pure-strategy Nash equilibria: DD. At least one equilibrium is Pareto-inferior, so individual rationality and collective benefit point to different outcomes.",
};

/** Tit-for-Tat versus Always Defect over 10 rounds. */
function tftVsAdRounds(): RoundResult[] {
  const rounds: RoundResult[] = [
    {
      round_number: 1,
      player_a_action: "COOPERATE",
      player_b_action: "DEFECT",
      player_a_payoff: 0,
      player_b_payoff: 5,
      outcome: "CD",
    },
  ];
  for (let n = 2; n <= 10; n += 1) {
    rounds.push({
      round_number: n,
      player_a_action: "DEFECT",
      player_b_action: "DEFECT",
      player_a_payoff: 1,
      player_b_payoff: 1,
      outcome: "DD",
    });
  }
  return rounds;
}

export function mockMatchResult(): MatchResult {
  const rounds = tftVsAdRounds();
  let a = 0;
  let b = 0;
  const cumulative = rounds.map((round) => {
    a += round.player_a_payoff;
    b += round.player_b_payoff;
    return { round_number: round.round_number, player_a_cumulative: a, player_b_cumulative: b };
  });

  return {
    id: null,
    strategy_a_id: "TIT_FOR_TAT",
    strategy_b_id: "ALWAYS_DEFECT",
    rounds_played: 10,
    rounds_requested: 10,
    continuation_probability: null,
    seed: 42,
    player_a: {
      strategy_id: "TIT_FOR_TAT",
      total_payoff: 9,
      average_payoff: 0.9,
      cooperation_count: 1,
      defection_count: 9,
      cooperation_rate: 0.1,
      defection_rate: 0.9,
    },
    player_b: {
      strategy_id: "ALWAYS_DEFECT",
      total_payoff: 14,
      average_payoff: 1.4,
      cooperation_count: 0,
      defection_count: 10,
      cooperation_rate: 0,
      defection_rate: 1,
    },
    winner: "ALWAYS_DEFECT",
    is_draw: false,
    outcome_counts: { CC: 0, CD: 1, DC: 0, DD: 9 },
    rounds,
    cumulative_scores: cumulative,
    matrix: MOCK_ANALYSIS.matrix,
  };
}

export const MOCK_TOURNAMENT: Tournament = {
  id: DEMO_TOURNAMENT_ID,
  name: "Sample round robin (Demo Mode)",
  description: "Pre-recorded example data. Connect the FastAPI backend to run a real tournament.",
  status: "COMPLETED",
  strategy_codes: MOCK_STRATEGIES.map((strategy) => strategy.id),
  rounds_per_match: 100,
  repetitions: 1,
  seed: 42,
  continuation_probability: null,
  include_self_play: false,
  payoff_matrix_id: DEMO_MATRIX_ID,
  matches_played: 15,
  started_at: NOW,
  completed_at: NOW,
  error_message: null,
  created_at: NOW,
};

export const MOCK_TOURNAMENT_RESULTS: TournamentResults = {
  tournament_id: DEMO_TOURNAMENT_ID,
  status: "COMPLETED",
  winner_strategy_id: "GRIM_TRIGGER",
  matches_played: 15,
  rounds_per_match: 100,
  repetitions: 1,
  seed: 42,
  note: "Sample data for Demo Mode. Real rankings are produced by the backend simulation.",
  rankings: [
    {
      rank: 1,
      strategy_id: "GRIM_TRIGGER",
      strategy_name: "Grim Trigger",
      total_score: 1282,
      average_score: 2.564,
      matches_played: 5,
      rounds_played: 500,
      wins: 1,
      draws: 3,
      losses: 1,
      cooperation_count: 302,
      defection_count: 198,
      cooperation_rate: 0.604,
      defection_rate: 0.396,
    },
    {
      rank: 2,
      strategy_id: "TIT_FOR_TAT",
      strategy_name: "Tit-for-Tat",
      total_score: 1219,
      average_score: 2.438,
      matches_played: 5,
      rounds_played: 500,
      wins: 0,
      draws: 3,
      losses: 2,
      cooperation_count: 350,
      defection_count: 150,
      cooperation_rate: 0.7,
      defection_rate: 0.3,
    },
    {
      rank: 3,
      strategy_id: "TIT_FOR_TWO_TATS",
      strategy_name: "Tit-for-Two-Tats",
      total_score: 1192,
      average_score: 2.384,
      matches_played: 5,
      rounds_played: 500,
      wins: 0,
      draws: 3,
      losses: 2,
      cooperation_count: 372,
      defection_count: 128,
      cooperation_rate: 0.744,
      defection_rate: 0.256,
    },
    {
      rank: 4,
      strategy_id: "ALWAYS_DEFECT",
      strategy_name: "Always Defect",
      total_score: 1128,
      average_score: 2.256,
      matches_played: 5,
      rounds_played: 500,
      wins: 5,
      draws: 0,
      losses: 0,
      cooperation_count: 0,
      defection_count: 500,
      cooperation_rate: 0,
      defection_rate: 1,
    },
    {
      rank: 5,
      strategy_id: "ALWAYS_COOPERATE",
      strategy_name: "Always Cooperate",
      total_score: 1050,
      average_score: 2.1,
      matches_played: 5,
      rounds_played: 500,
      wins: 0,
      draws: 3,
      losses: 2,
      cooperation_count: 500,
      defection_count: 0,
      cooperation_rate: 1,
      defection_rate: 0,
    },
    {
      rank: 6,
      strategy_id: "RANDOM",
      strategy_name: "Random",
      total_score: 1019,
      average_score: 2.038,
      matches_played: 5,
      rounds_played: 500,
      wins: 3,
      draws: 0,
      losses: 2,
      cooperation_count: 248,
      defection_count: 252,
      cooperation_rate: 0.496,
      defection_rate: 0.504,
    },
  ],
};

export const MOCK_TOURNAMENT_MATCHES: TournamentMatch[] = [
  {
    id: "44444444-4444-4444-8444-444444444401",
    sequence: 1,
    repetition: 1,
    strategy_a_id: "TIT_FOR_TAT",
    strategy_b_id: "ALWAYS_DEFECT",
    rounds_played: 100,
    player_a_score: 99,
    player_b_score: 104,
    player_a_cooperation_count: 1,
    player_b_cooperation_count: 0,
    winner: "ALWAYS_DEFECT",
  },
  {
    id: "44444444-4444-4444-8444-444444444402",
    sequence: 2,
    repetition: 1,
    strategy_a_id: "TIT_FOR_TAT",
    strategy_b_id: "ALWAYS_COOPERATE",
    rounds_played: 100,
    player_a_score: 300,
    player_b_score: 300,
    player_a_cooperation_count: 100,
    player_b_cooperation_count: 100,
    winner: null,
  },
];

export const MOCK_TOURNAMENT_STATISTICS: TournamentStatistics = {
  tournament_id: DEMO_TOURNAMENT_ID,
  matches_played: 15,
  rounds_per_match: 100,
  repetitions: 1,
  score_statistics: {
    count: 6,
    mean: 1148.33,
    median: 1160,
    standard_deviation: 97.4,
    minimum: 1019,
    maximum: 1282,
    total: 6890,
  },
  cooperation_rate_statistics: {
    count: 6,
    mean: 0.591,
    median: 0.652,
    standard_deviation: 0.359,
    minimum: 0,
    maximum: 1,
    total: 3.544,
  },
  outcome_frequency: { CC: 706, CD: 220, DC: 220, DD: 354 },
  outcome_rates: { CC: 0.4707, CD: 0.1467, DC: 0.1467, DD: 0.236 },
  cooperation_by_round: Array.from({ length: 10 }, (_, index) => ({
    round_number: index * 10 + 1,
    cooperation_rate: index === 0 ? 0.8 : 0.58,
  })),
  head_to_head: [
    { strategy_id: "TIT_FOR_TAT", opponent_id: "ALWAYS_DEFECT", average_payoff: 0.99 },
    { strategy_id: "ALWAYS_DEFECT", opponent_id: "TIT_FOR_TAT", average_payoff: 1.04 },
    { strategy_id: "TIT_FOR_TAT", opponent_id: "ALWAYS_COOPERATE", average_payoff: 3 },
    { strategy_id: "ALWAYS_COOPERATE", opponent_id: "TIT_FOR_TAT", average_payoff: 3 },
  ],
};

export const MOCK_EXPERIMENT: Experiment = {
  id: DEMO_EXPERIMENT_ID,
  name: "Sample classroom session (Demo Mode)",
  description: "Pre-recorded example data.",
  status: "COMPLETED",
  rounds: 10,
  anonymous_mode: true,
  trust_survey_enabled: true,
  payoff_matrix_id: DEMO_MATRIX_ID,
  participant_count: 4,
  pair_count: 2,
  started_at: NOW,
  completed_at: NOW,
  created_at: NOW,
};

export const MOCK_PARTICIPANTS: Participant[] = ["S01", "S02", "S03", "S04"].map(
  (code, index) => ({
    id: `55555555-5555-4555-8555-55555555550${index + 1}`,
    code,
    display_name: null,
    created_at: NOW,
  }),
);

export const MOCK_EXPERIMENT_RESULTS: ExperimentResults = {
  experiment_id: DEMO_EXPERIMENT_ID,
  status: "COMPLETED",
  rounds_configured: 10,
  matches: [
    {
      id: "66666666-6666-4666-8666-666666666601",
      pair_number: 1,
      participant_a_id: MOCK_PARTICIPANTS[0].id,
      participant_b_id: MOCK_PARTICIPANTS[1].id,
      participant_a_label: "S01",
      participant_b_label: "S02",
      player_a_score: 22,
      player_b_score: 19,
      rounds_recorded: 10,
      is_complete: true,
    },
    {
      id: "66666666-6666-4666-8666-666666666602",
      pair_number: 2,
      participant_a_id: MOCK_PARTICIPANTS[2].id,
      participant_b_id: MOCK_PARTICIPANTS[3].id,
      participant_a_label: "S03",
      participant_b_label: "S04",
      player_a_score: 18,
      player_b_score: 23,
      rounds_recorded: 10,
      is_complete: true,
    },
  ],
  rounds: [],
};

export const MOCK_EXPERIMENT_STATISTICS: ExperimentStatistics = {
  experiment_id: DEMO_EXPERIMENT_ID,
  rounds_recorded: 20,
  decisions_recorded: 40,
  cooperation_rate: 0.55,
  defection_rate: 0.45,
  mutual_cooperation_rate: 0.35,
  mutual_defection_rate: 0.25,
  cd_rate: 0.2,
  dc_rate: 0.2,
  average_payoff: 2.05,
  total_payoff: 82,
  payoff_statistics: {
    count: 40,
    mean: 2.05,
    median: 3,
    standard_deviation: 1.63,
    minimum: 0,
    maximum: 5,
    total: 82,
  },
  outcome_frequency: { CC: 7, CD: 4, DC: 4, DD: 5 },
  cooperation_rate_by_round: Array.from({ length: 10 }, (_, index) => ({
    round_number: index + 1,
    cooperation_rate: Math.max(0.2, 0.75 - index * 0.05),
  })),
  defection_rate_by_round: Array.from({ length: 10 }, (_, index) => ({
    round_number: index + 1,
    defection_rate: Math.min(0.8, 0.25 + index * 0.05),
  })),
  payoff_by_round: Array.from({ length: 10 }, (_, index) => ({
    round_number: index + 1,
    average_payoff: 2.4 - index * 0.06,
    total_payoff: (2.4 - index * 0.06) * 4,
  })),
  nash_prediction_cooperation_rate: 0,
  nash_prediction_applies: true,
};

export const MOCK_SURVEY_STATISTICS: TrustSurveyStatistics = {
  experiment_id: DEMO_EXPERIMENT_ID,
  responses: 8,
  expected_cooperation_responses: 4,
  trust_after_responses: 4,
  average_expected_cooperation: 3.25,
  average_trust_after: 3,
  expected_cooperation_statistics: {
    count: 4,
    mean: 3.25,
    median: 3.5,
    standard_deviation: 0.96,
    minimum: 2,
    maximum: 4,
    total: 13,
  },
  trust_after_statistics: {
    count: 4,
    mean: 3,
    median: 3,
    standard_deviation: 1.15,
    minimum: 2,
    maximum: 4,
    total: 12,
  },
  actual_cooperation_rate: 0.55,
  correlation_expected_vs_actual: 0.62,
  correlation_trust_after_vs_actual: 0.71,
  interpretation_note:
    "Correlations are descriptive summaries of this classroom sample. They do not establish that trust causes cooperation.",
};
