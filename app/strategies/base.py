"""The Strategy interface every tournament strategy implements."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from app.game_theory.actions import Action, StrategyCategory

History = Sequence[Action]


@dataclass(frozen=True)
class StrategyMetadata:
    """Describes a strategy to the API without instantiating it."""

    id: str
    name: str
    description: str
    rules: list[str]
    category: StrategyCategory
    is_deterministic: bool


class Strategy(ABC):
    """A rule for choosing an action from the history of a match.

    Implementations receive the complete history of the current match and
    return the next action. They must not look at anything else: a strategy
    cannot see the opponent's current move, and a fresh instance is created
    for every match so nothing leaks between matches.
    """

    metadata: StrategyMetadata

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    @property
    def id(self) -> str:
        return self.metadata.id

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def rng(self) -> random.Random:
        return self._rng

    @abstractmethod
    def choose_action(self, my_history: History, opponent_history: History) -> Action:
        """Return the action to play in the next round.

        `my_history` and `opponent_history` are ordered oldest first and are
        the same length. Both are empty on the opening round.
        """

    def reset(self) -> None:
        """Clear any per-match state.

        The bundled strategies are pure functions of history and need no
        state, but a strategy that caches something can override this. The
        simulation calls it before every match.
        """

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Strategy {self.metadata.id}>"
