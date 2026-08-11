"""The two actions available in a Prisoner's Dilemma, and the four outcomes."""

from __future__ import annotations

from enum import Enum


class Action(str, Enum):
    """A single player's move in one round."""

    COOPERATE = "COOPERATE"
    DEFECT = "DEFECT"

    @property
    def short(self) -> str:
        """Single-letter form used in histories and CSV exports."""
        return "C" if self is Action.COOPERATE else "D"

    @classmethod
    def from_short(cls, value: str) -> "Action":
        normalised = value.strip().upper()
        if normalised in ("C", "COOPERATE"):
            return cls.COOPERATE
        if normalised in ("D", "DEFECT"):
            return cls.DEFECT
        raise ValueError(f"cannot interpret {value!r} as an action")


class Outcome(str, Enum):
    """The four cells of a 2x2 game, named by (player A action, player B action)."""

    CC = "CC"
    CD = "CD"
    DC = "DC"
    DD = "DD"

    @property
    def actions(self) -> tuple[Action, Action]:
        first = Action.COOPERATE if self.value[0] == "C" else Action.DEFECT
        second = Action.COOPERATE if self.value[1] == "C" else Action.DEFECT
        return first, second

    @classmethod
    def from_actions(cls, action_a: Action, action_b: Action) -> "Outcome":
        return cls(action_a.short + action_b.short)


class StrategyCategory(str, Enum):
    """Descriptive grouping used in strategy metadata.

    NICE strategies never defect first, NASTY strategies open with defection,
    and STOCHASTIC strategies use randomness. The labels are descriptive only;
    they carry no weight in scoring.
    """

    NICE = "NICE"
    NASTY = "NASTY"
    STOCHASTIC = "STOCHASTIC"


class DominanceType(str, Enum):
    STRICT = "STRICT"
    WEAK = "WEAK"


class Player(str, Enum):
    A = "A"
    B = "B"
