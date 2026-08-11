"""Payoff matrix schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.game_theory.payoff import PayoffMatrix as DomainPayoffMatrix

PAYOFF_LIMIT = 1_000_000


class PayoffCell(BaseModel):
    """The payoffs awarded to each player for one outcome."""

    player_a_payoff: float = Field(ge=-PAYOFF_LIMIT, le=PAYOFF_LIMIT)
    player_b_payoff: float = Field(ge=-PAYOFF_LIMIT, le=PAYOFF_LIMIT)


class PayoffMatrixInput(BaseModel):
    """A 2x2 matrix supplied inline, without being stored.

    Any 2x2 matrix is accepted. Whether it is a Prisoner's Dilemma is reported
    by the analysis engine rather than enforced here, so that non-dilemma
    games can be analysed too.
    """

    cc: PayoffCell = Field(description="Both players cooperate")
    cd: PayoffCell = Field(description="A cooperates, B defects")
    dc: PayoffCell = Field(description="A defects, B cooperates")
    dd: PayoffCell = Field(description="Both players defect")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cc": {"player_a_payoff": 3, "player_b_payoff": 3},
                "cd": {"player_a_payoff": 0, "player_b_payoff": 5},
                "dc": {"player_a_payoff": 5, "player_b_payoff": 0},
                "dd": {"player_a_payoff": 1, "player_b_payoff": 1},
            }
        }
    )

    def to_domain(self) -> DomainPayoffMatrix:
        return DomainPayoffMatrix.from_tuples(
            cc=(self.cc.player_a_payoff, self.cc.player_b_payoff),
            cd=(self.cd.player_a_payoff, self.cd.player_b_payoff),
            dc=(self.dc.player_a_payoff, self.dc.player_b_payoff),
            dd=(self.dd.player_a_payoff, self.dd.player_b_payoff),
        )

    @classmethod
    def from_domain(cls, matrix: DomainPayoffMatrix) -> "PayoffMatrixInput":
        return cls(
            cc=PayoffCell(player_a_payoff=matrix.cc.player_a, player_b_payoff=matrix.cc.player_b),
            cd=PayoffCell(player_a_payoff=matrix.cd.player_a, player_b_payoff=matrix.cd.player_b),
            dc=PayoffCell(player_a_payoff=matrix.dc.player_a, player_b_payoff=matrix.dc.player_b),
            dd=PayoffCell(player_a_payoff=matrix.dd.player_a, player_b_payoff=matrix.dd.player_b),
        )


class PayoffMatrixCreate(PayoffMatrixInput):
    """A matrix to be stored."""

    name: str = Field(min_length=1, max_length=120, examples=["Classic Prisoner's Dilemma"])
    description: str | None = Field(default=None, max_length=500)
    is_default: bool = False


class PayoffMatrixUpdate(BaseModel):
    """Partial update. Any omitted field is left unchanged."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    cc: PayoffCell | None = None
    cd: PayoffCell | None = None
    dc: PayoffCell | None = None
    dd: PayoffCell | None = None
    is_default: bool | None = None

    @model_validator(mode="after")
    def _require_a_change(self) -> "PayoffMatrixUpdate":
        if not self.model_fields_set:
            raise ValueError("provide at least one field to update")
        return self


class PayoffMatrixResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    cc: PayoffCell
    cd: PayoffCell
    dc: PayoffCell
    dd: PayoffCell
    is_default: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model) -> "PayoffMatrixResponse":
        return cls(
            id=model.id,
            name=model.name,
            description=model.description,
            cc=PayoffCell(player_a_payoff=model.cc_player_a, player_b_payoff=model.cc_player_b),
            cd=PayoffCell(player_a_payoff=model.cd_player_a, player_b_payoff=model.cd_player_b),
            dc=PayoffCell(player_a_payoff=model.dc_player_a, player_b_payoff=model.dc_player_b),
            dd=PayoffCell(player_a_payoff=model.dd_player_a, player_b_payoff=model.dd_player_b),
            is_default=model.is_default,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
