"""Statistics response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class DescriptiveStatisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    count: int
    mean: float
    median: float
    standard_deviation: float
    minimum: float
    maximum: float
    total: float


class CooperationByRound(BaseModel):
    round_number: int
    cooperation_rate: float


class HeadToHeadEntry(BaseModel):
    strategy_id: str
    opponent_id: str
    average_payoff: float


class TournamentStatisticsResponse(BaseModel):
    tournament_id: uuid.UUID
    matches_played: int
    rounds_per_match: int
    repetitions: int
    score_statistics: DescriptiveStatisticsResponse
    cooperation_rate_statistics: DescriptiveStatisticsResponse
    outcome_frequency: dict[str, int]
    outcome_rates: dict[str, float]
    cooperation_by_round: list[CooperationByRound]
    head_to_head: list[HeadToHeadEntry] = Field(
        description="Average payoff per round for each ordered strategy pair"
    )
