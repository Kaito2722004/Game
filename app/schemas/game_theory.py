"""Schemas for the game-theory analysis endpoint."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, model_validator

from app.game_theory.actions import Action, DominanceType, Outcome, Player
from app.schemas.payoff_matrix import PayoffMatrixInput


class AnalyzeGameRequest(BaseModel):
    """Analyse either an inline matrix or a stored one.

    Exactly one of `matrix` and `payoff_matrix_id` must be supplied.
    """

    matrix: PayoffMatrixInput | None = None
    payoff_matrix_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _exactly_one_source(self) -> "AnalyzeGameRequest":
        if (self.matrix is None) == (self.payoff_matrix_id is None):
            raise ValueError("supply exactly one of 'matrix' or 'payoff_matrix_id'")
        return self


class PayoffOrderingResponse(BaseModel):
    """T, R, P and S as faced by one player."""

    player: Player
    temptation: float = Field(description="T: defect against a cooperator")
    reward: float = Field(description="R: mutual cooperation")
    punishment: float = Field(description="P: mutual defection")
    sucker: float = Field(description="S: cooperate against a defector")
    ordering_holds: bool = Field(description="Whether T > R > P > S")
    averaging_condition_holds: bool = Field(description="Whether R > (S + T) / 2")


class DilemmaConditionsResponse(BaseModel):
    is_prisoners_dilemma: bool
    ordering_holds: bool
    averaging_condition_holds: bool
    is_symmetric: bool
    player_a: PayoffOrderingResponse
    player_b: PayoffOrderingResponse
    failed_conditions: list[str]


class DominantStrategyResponse(BaseModel):
    player: Player
    exists: bool
    action: Action | None
    dominance: DominanceType | None
    explanation: str


class NashEquilibriumResponse(BaseModel):
    outcome: Outcome
    player_a_action: Action
    player_b_action: Action
    player_a_payoff: float
    player_b_payoff: float
    explanation: str


class ParetoStatusResponse(BaseModel):
    outcome: Outcome
    player_a_payoff: float
    player_b_payoff: float
    is_pareto_optimal: bool
    dominated_by: list[Outcome]
    explanation: str


class GameAnalysisResponse(BaseModel):
    """The complete analysis of one matrix, all of it computed."""

    matrix: PayoffMatrixInput
    conditions: DilemmaConditionsResponse
    dominant_strategy_player_a: DominantStrategyResponse
    dominant_strategy_player_b: DominantStrategyResponse
    nash_equilibria: list[NashEquilibriumResponse]
    pareto_analysis: list[ParetoStatusResponse]
    pareto_optimal_outcomes: list[Outcome]
    pareto_inferior_outcomes: list[Outcome]
    mutual_cooperation_pareto_superior_to_mutual_defection: bool
    equilibrium_is_pareto_inferior: bool
    summary: str
