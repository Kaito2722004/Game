"""Schemas for the combined activity history."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class HistoryKind(str, Enum):
    """What sort of activity an entry records.

    TOURNAMENT is a round robin, EXPERIMENT a classroom session, and
    SIMULATED_MATCH a one-off match run from the simulator and kept.
    """

    TOURNAMENT = "TOURNAMENT"
    EXPERIMENT = "EXPERIMENT"
    SIMULATED_MATCH = "SIMULATED_MATCH"


class HistoryEntry(BaseModel):
    """One thing that was played, in a shape common to all three kinds."""

    id: uuid.UUID
    kind: HistoryKind
    title: str
    subtitle: str | None = None
    status: str
    occurred_at: datetime = Field(
        description="When the activity finished, falling back to when it was created."
    )
    matches: int = Field(default=0, description="Matches or pairs involved")
    rounds: int = Field(default=0, description="Rounds actually recorded")
    cooperation_rate: float | None = Field(
        default=None,
        description="Share of all recorded moves that were COOPERATE, if any were.",
    )
    headline: str | None = Field(
        default=None, description="The single most useful result, e.g. the winner"
    )
    parent_id: uuid.UUID | None = Field(
        default=None,
        description="For a simulated match, the container it is stored under.",
    )


class HistoryTotals(BaseModel):
    """Counts across everything recorded so far."""

    tournaments: int
    tournament_matches: int
    tournament_rounds: int
    experiments: int
    human_pairs: int
    human_rounds: int
    simulated_matches: int
    survey_responses: int
    total_rounds_played: int = Field(
        description="Tournament rounds plus simulated-match rounds plus human rounds"
    )


class HistoryResponse(BaseModel):
    totals: HistoryTotals
    entries: list[HistoryEntry]
