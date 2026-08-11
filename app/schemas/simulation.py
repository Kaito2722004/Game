"""Schemas for strategies, single-match simulation, and tournaments."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.game_theory.actions import Action, Outcome, StrategyCategory
from app.models.tournament import TournamentStatus
from app.schemas.payoff_matrix import PayoffMatrixInput

MAX_ROUNDS = 10_000
MAX_REPETITIONS = 1_000


# --------------------------------------------------------------- strategies --
class StrategyResponse(BaseModel):
    """Catalogue entry for one strategy."""

    id: str = Field(examples=["TIT_FOR_TAT"])
    name: str = Field(examples=["Tit-for-Tat"])
    description: str
    rules: list[str]
    category: StrategyCategory
    is_deterministic: bool


# ------------------------------------------------------------ matrix source --
class _MatrixSource(BaseModel):
    """Mixin for requests that take either an inline or a stored matrix.

    When neither is given, the stored default matrix is used.
    """

    matrix: PayoffMatrixInput | None = None
    payoff_matrix_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _at_most_one_source(self):
        if self.matrix is not None and self.payoff_matrix_id is not None:
            raise ValueError("supply at most one of 'matrix' or 'payoff_matrix_id'")
        return self


# ------------------------------------------------------------------ matches --
class MatchSimulationRequest(_MatrixSource):
    """Simulate one iterated match between two strategies."""

    strategy_a_id: str = Field(examples=["TIT_FOR_TAT"])
    strategy_b_id: str = Field(examples=["ALWAYS_DEFECT"])
    rounds: int = Field(default=100, ge=1, le=MAX_ROUNDS)
    seed: int | None = Field(default=None, description="Set for a reproducible run")
    continuation_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "If set, each round is followed by another with this probability, "
            "up to 'rounds' as an upper bound. Models a repeated game whose "
            "end is uncertain."
        ),
    )
    persist: bool = Field(
        default=False,
        description="Store the match so it can be fetched later by id.",
    )


class RoundResultResponse(BaseModel):
    round_number: int
    player_a_action: Action
    player_b_action: Action
    player_a_payoff: float
    player_b_payoff: float
    outcome: Outcome


class PlayerMatchStatisticsResponse(BaseModel):
    strategy_id: str
    total_payoff: float
    average_payoff: float
    cooperation_count: int
    defection_count: int
    cooperation_rate: float
    defection_rate: float


class MatchResultResponse(BaseModel):
    """A completed match, including every round."""

    id: uuid.UUID | None = None
    strategy_a_id: str
    strategy_b_id: str
    rounds_played: int
    rounds_requested: int
    continuation_probability: float | None
    seed: int | None
    player_a: PlayerMatchStatisticsResponse
    player_b: PlayerMatchStatisticsResponse
    winner: str | None = Field(description="Strategy id of the winner, or null for a draw")
    is_draw: bool
    outcome_counts: dict[str, int]
    rounds: list[RoundResultResponse]
    cumulative_scores: list[dict[str, float]]
    matrix: PayoffMatrixInput


# -------------------------------------------------------------- tournaments --
class TournamentCreateRequest(_MatrixSource):
    """Configuration for a new tournament. Creating does not run it."""

    name: str = Field(min_length=1, max_length=200, examples=["Axelrod-style round robin"])
    description: str | None = Field(default=None, max_length=1000)
    strategy_ids: list[str] = Field(
        min_length=1,
        examples=[
            [
                "ALWAYS_COOPERATE",
                "ALWAYS_DEFECT",
                "TIT_FOR_TAT",
                "GRIM_TRIGGER",
                "TIT_FOR_TWO_TATS",
                "RANDOM",
            ]
        ],
    )
    rounds_per_match: int = Field(default=100, ge=1, le=MAX_ROUNDS)
    repetitions: int = Field(default=1, ge=1, le=MAX_REPETITIONS)
    seed: int | None = None
    continuation_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    include_self_play: bool = Field(
        default=False, description="Also play each strategy against a copy of itself"
    )

    @model_validator(mode="after")
    def _validate_strategies(self) -> "TournamentCreateRequest":
        normalised = [sid.strip().upper() for sid in self.strategy_ids]
        duplicates = {sid for sid in normalised if normalised.count(sid) > 1}
        if duplicates:
            raise ValueError(
                "duplicate strategies are not allowed: " + ", ".join(sorted(duplicates))
            )
        if len(normalised) < 2 and not self.include_self_play:
            raise ValueError(
                "a tournament needs at least two strategies, or one strategy with "
                "include_self_play enabled"
            )
        self.strategy_ids = normalised
        return self


class TournamentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    status: TournamentStatus
    strategy_codes: list[str]
    rounds_per_match: int
    repetitions: int
    seed: int | None
    continuation_probability: float | None
    include_self_play: bool
    payoff_matrix_id: uuid.UUID
    matches_played: int = 0
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime


class TournamentRankingResponse(BaseModel):
    rank: int
    strategy_id: str
    strategy_name: str
    total_score: float
    average_score: float
    matches_played: int
    rounds_played: int
    wins: int
    draws: int
    losses: int
    cooperation_count: int
    defection_count: int
    cooperation_rate: float
    defection_rate: float


class TournamentResultsResponse(BaseModel):
    """Final table for a completed tournament."""

    tournament_id: uuid.UUID
    status: TournamentStatus
    winner_strategy_id: str | None
    rankings: list[TournamentRankingResponse]
    matches_played: int
    rounds_per_match: int
    repetitions: int
    seed: int | None
    note: str = Field(
        default=(
            "Rankings are produced by the simulation. No expected ordering is "
            "assumed by the software."
        )
    )


class TournamentMatchSummaryResponse(BaseModel):
    id: uuid.UUID
    sequence: int
    repetition: int
    strategy_a_id: str
    strategy_b_id: str
    rounds_played: int
    player_a_score: float
    player_b_score: float
    player_a_cooperation_count: int
    player_b_cooperation_count: int
    winner: str | None


class TournamentMatchDetailResponse(TournamentMatchSummaryResponse):
    rounds: list[RoundResultResponse]
