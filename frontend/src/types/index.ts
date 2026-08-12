/**
 * Types mirroring the FastAPI backend's schemas.
 *
 * The backend is the source of truth for every game-theoretic result. These
 * types describe what it returns; the frontend never recomputes them.
 */

/* ------------------------------------------------------------------ core -- */

export type Action = "COOPERATE" | "DEFECT";
export type Outcome = "CC" | "CD" | "DC" | "DD";
export type Player = "A" | "B";
export type DominanceType = "STRICT" | "WEAK";
export type StrategyCategory = "NICE" | "NASTY" | "STOCHASTIC";
export type UserRole = "ADMIN" | "TEACHER" | "STUDENT";
export type TournamentStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
export type ExperimentStatus = "DRAFT" | "RUNNING" | "COMPLETED";
export type SurveyQuestionType = "EXPECTED_COOPERATION" | "TRUST_AFTER";

/* -------------------------------------------------------------- envelope -- */

/** Every successful backend response uses this envelope. */
export interface ApiResponse<T> {
  success: true;
  data: T;
  message: string | null;
}

/** Every backend error uses this envelope. */
export interface ApiErrorBody {
  success: false;
  data: null;
  message: string;
  errors: unknown[];
}

/** Normalised error the UI works with, produced by the API client. */
export interface ApiError {
  status: number;
  message: string;
  details: string[];
  isNetworkError: boolean;
}

/* ----------------------------------------------------------------- auth -- */

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest extends LoginRequest {
  full_name: string;
  role?: UserRole;
}

/* --------------------------------------------------------- payoff matrix -- */

export interface PayoffCell {
  player_a_payoff: number;
  player_b_payoff: number;
}

/** A 2x2 matrix as sent to, or received from, the backend. */
export interface PayoffMatrixInput {
  cc: PayoffCell;
  cd: PayoffCell;
  dc: PayoffCell;
  dd: PayoffCell;
}

export interface PayoffMatrix extends PayoffMatrixInput {
  id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface PayoffMatrixCreate extends PayoffMatrixInput {
  name: string;
  description?: string | null;
  is_default?: boolean;
}

export type PayoffMatrixUpdate = Partial<PayoffMatrixCreate>;

/* ----------------------------------------------------------- game theory -- */

export interface PayoffOrdering {
  player: Player;
  /** T: defecting against a cooperator. */
  temptation: number;
  /** R: mutual cooperation. */
  reward: number;
  /** P: mutual defection. */
  punishment: number;
  /** S: cooperating against a defector. */
  sucker: number;
  ordering_holds: boolean;
  averaging_condition_holds: boolean;
}

export interface DilemmaConditions {
  is_prisoners_dilemma: boolean;
  ordering_holds: boolean;
  averaging_condition_holds: boolean;
  is_symmetric: boolean;
  player_a: PayoffOrdering;
  player_b: PayoffOrdering;
  failed_conditions: string[];
}

export interface DominantStrategy {
  player: Player;
  exists: boolean;
  action: Action | null;
  dominance: DominanceType | null;
  explanation: string;
}

export interface NashEquilibrium {
  outcome: Outcome;
  player_a_action: Action;
  player_b_action: Action;
  player_a_payoff: number;
  player_b_payoff: number;
  explanation: string;
}

export interface ParetoStatus {
  outcome: Outcome;
  player_a_payoff: number;
  player_b_payoff: number;
  is_pareto_optimal: boolean;
  dominated_by: Outcome[];
  explanation: string;
}

export interface GameAnalysis {
  matrix: PayoffMatrixInput;
  conditions: DilemmaConditions;
  dominant_strategy_player_a: DominantStrategy;
  dominant_strategy_player_b: DominantStrategy;
  nash_equilibria: NashEquilibrium[];
  pareto_analysis: ParetoStatus[];
  pareto_optimal_outcomes: Outcome[];
  pareto_inferior_outcomes: Outcome[];
  mutual_cooperation_pareto_superior_to_mutual_defection: boolean;
  equilibrium_is_pareto_inferior: boolean;
  summary: string;
}

export interface AnalyzeGameRequest {
  matrix?: PayoffMatrixInput;
  payoff_matrix_id?: string;
}

/* ------------------------------------------------------------ strategies -- */

export interface Strategy {
  id: string;
  name: string;
  description: string;
  rules: string[];
  category: StrategyCategory;
  is_deterministic: boolean;
}

/* --------------------------------------------------------------- matches -- */

export interface MatchRequest {
  strategy_a_id: string;
  strategy_b_id: string;
  rounds: number;
  seed?: number | null;
  continuation_probability?: number | null;
  matrix?: PayoffMatrixInput;
  payoff_matrix_id?: string;
  persist?: boolean;
}

export interface RoundResult {
  round_number: number;
  player_a_action: Action;
  player_b_action: Action;
  player_a_payoff: number;
  player_b_payoff: number;
  outcome: Outcome;
}

export interface PlayerMatchStatistics {
  strategy_id: string;
  total_payoff: number;
  average_payoff: number;
  cooperation_count: number;
  defection_count: number;
  cooperation_rate: number;
  defection_rate: number;
}

export interface CumulativePoint {
  round_number: number;
  player_a_cumulative: number;
  player_b_cumulative: number;
}

export interface MatchResult {
  id: string | null;
  strategy_a_id: string;
  strategy_b_id: string;
  rounds_played: number;
  rounds_requested: number;
  continuation_probability: number | null;
  seed: number | null;
  player_a: PlayerMatchStatistics;
  player_b: PlayerMatchStatistics;
  winner: string | null;
  is_draw: boolean;
  outcome_counts: Record<string, number>;
  rounds: RoundResult[];
  cumulative_scores: CumulativePoint[];
  matrix: PayoffMatrixInput;
}

/* ----------------------------------------------------------- tournaments -- */

export interface TournamentCreateRequest {
  name: string;
  description?: string | null;
  strategy_ids: string[];
  rounds_per_match: number;
  repetitions?: number;
  seed?: number | null;
  continuation_probability?: number | null;
  include_self_play?: boolean;
  matrix?: PayoffMatrixInput;
  payoff_matrix_id?: string;
}

export interface Tournament {
  id: string;
  name: string;
  description: string | null;
  status: TournamentStatus;
  strategy_codes: string[];
  rounds_per_match: number;
  repetitions: number;
  seed: number | null;
  continuation_probability: number | null;
  include_self_play: boolean;
  payoff_matrix_id: string;
  matches_played: number;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface TournamentRanking {
  rank: number;
  strategy_id: string;
  strategy_name: string;
  total_score: number;
  average_score: number;
  matches_played: number;
  rounds_played: number;
  wins: number;
  draws: number;
  losses: number;
  cooperation_count: number;
  defection_count: number;
  cooperation_rate: number;
  defection_rate: number;
}

export interface TournamentResults {
  tournament_id: string;
  status: TournamentStatus;
  winner_strategy_id: string | null;
  rankings: TournamentRanking[];
  matches_played: number;
  rounds_per_match: number;
  repetitions: number;
  seed: number | null;
  note: string;
}

export interface TournamentMatch {
  id: string;
  sequence: number;
  repetition: number;
  strategy_a_id: string;
  strategy_b_id: string;
  rounds_played: number;
  player_a_score: number;
  player_b_score: number;
  player_a_cooperation_count: number;
  player_b_cooperation_count: number;
  winner: string | null;
}

export interface TournamentMatchDetail extends TournamentMatch {
  rounds: RoundResult[];
}

/* ------------------------------------------------------------ statistics -- */

export interface DescriptiveStatistics {
  count: number;
  mean: number;
  median: number;
  standard_deviation: number;
  minimum: number;
  maximum: number;
  total: number;
}

export interface CooperationByRound {
  round_number: number;
  cooperation_rate: number;
}

export interface HeadToHeadEntry {
  strategy_id: string;
  opponent_id: string;
  average_payoff: number;
}

export interface TournamentStatistics {
  tournament_id: string;
  matches_played: number;
  rounds_per_match: number;
  repetitions: number;
  score_statistics: DescriptiveStatistics;
  cooperation_rate_statistics: DescriptiveStatistics;
  outcome_frequency: Record<string, number>;
  outcome_rates: Record<string, number>;
  cooperation_by_round: CooperationByRound[];
  head_to_head: HeadToHeadEntry[];
}

/* ----------------------------------------------------------- experiments -- */

export interface ExperimentCreateRequest {
  name: string;
  description?: string | null;
  rounds: number;
  anonymous_mode: boolean;
  trust_survey_enabled: boolean;
  payoff_matrix_id?: string | null;
}

export interface Experiment {
  id: string;
  name: string;
  description: string | null;
  status: ExperimentStatus;
  rounds: number;
  anonymous_mode: boolean;
  trust_survey_enabled: boolean;
  payoff_matrix_id: string;
  participant_count: number;
  pair_count: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface Participant {
  id: string;
  code: string;
  display_name: string | null;
  created_at: string;
}

export interface HumanMatch {
  id: string;
  pair_number: number;
  participant_a_id: string;
  participant_b_id: string;
  participant_a_label: string;
  participant_b_label: string;
  player_a_score: number;
  player_b_score: number;
  rounds_recorded: number;
  is_complete: boolean;
}

export interface ExperimentStart {
  experiment_id: string;
  status: ExperimentStatus;
  pairs: HumanMatch[];
  unpaired_participant_ids: string[];
}

export interface HumanRound {
  id: string;
  experiment_id: string;
  match_id: string;
  round_number: number;
  player_a_id: string;
  player_b_id: string;
  player_a_action: Action;
  player_b_action: Action;
  player_a_payoff: number;
  player_b_payoff: number;
}

export interface RoundSubmission {
  match_id: string;
  round_number: number;
  player_a_action: Action;
  player_b_action: Action;
}

export interface ExperimentResults {
  experiment_id: string;
  status: ExperimentStatus;
  rounds_configured: number;
  matches: HumanMatch[];
  rounds: HumanRound[];
}

export interface RateByRound {
  round_number: number;
  cooperation_rate?: number | null;
  defection_rate?: number | null;
  average_payoff?: number | null;
  total_payoff?: number | null;
}

export interface ExperimentStatistics {
  experiment_id: string;
  rounds_recorded: number;
  decisions_recorded: number;
  cooperation_rate: number;
  defection_rate: number;
  mutual_cooperation_rate: number;
  mutual_defection_rate: number;
  cd_rate: number;
  dc_rate: number;
  average_payoff: number;
  total_payoff: number;
  payoff_statistics: DescriptiveStatistics;
  outcome_frequency: Record<string, number>;
  cooperation_rate_by_round: RateByRound[];
  defection_rate_by_round: RateByRound[];
  payoff_by_round: RateByRound[];
  nash_prediction_cooperation_rate: number;
  nash_prediction_applies: boolean;
}

/* --------------------------------------------------------------- surveys -- */

export interface TrustSurveyRequest {
  experiment_id: string;
  participant_id: string;
  question_type: SurveyQuestionType;
  score: number;
}

export interface TrustSurvey {
  id: string;
  experiment_id: string;
  participant_id: string;
  question_type: SurveyQuestionType;
  score: number;
  created_at: string;
}

export interface TrustSurveyStatistics {
  experiment_id: string;
  responses: number;
  expected_cooperation_responses: number;
  trust_after_responses: number;
  average_expected_cooperation: number | null;
  average_trust_after: number | null;
  expected_cooperation_statistics: DescriptiveStatistics;
  trust_after_statistics: DescriptiveStatistics;
  actual_cooperation_rate: number;
  correlation_expected_vs_actual: number | null;
  correlation_trust_after_vs_actual: number | null;
  interpretation_note: string;
}

/* ----------------------------------------------------------------- history -- */

export type HistoryKind = "TOURNAMENT" | "EXPERIMENT" | "SIMULATED_MATCH";

/** One thing that was played, in a shape common to all three kinds. */
export interface HistoryEntry {
  id: string;
  kind: HistoryKind;
  title: string;
  subtitle: string | null;
  status: string;
  occurred_at: string;
  matches: number;
  rounds: number;
  cooperation_rate: number | null;
  headline: string | null;
  parent_id: string | null;
}

export interface HistoryTotals {
  tournaments: number;
  tournament_matches: number;
  tournament_rounds: number;
  experiments: number;
  human_pairs: number;
  human_rounds: number;
  simulated_matches: number;
  survey_responses: number;
  total_rounds_played: number;
}

export interface HistoryResponse {
  totals: HistoryTotals;
  entries: HistoryEntry[];
}
