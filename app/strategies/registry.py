"""Strategy registry.

Strategies are looked up by id rather than selected with a chain of if/else
branches, so adding one means writing a module and registering the class.
"""

from __future__ import annotations

import random
from typing import Iterable, Iterator, Type

from app.strategies.always_cooperate import AlwaysCooperate
from app.strategies.always_defect import AlwaysDefect
from app.strategies.base import Strategy, StrategyMetadata
from app.strategies.grim_trigger import GrimTrigger
from app.strategies.random_strategy import RandomStrategy
from app.strategies.tit_for_tat import TitForTat
from app.strategies.tit_for_two_tats import TitForTwoTats


class UnknownStrategyError(KeyError):
    """Raised when a strategy id is not registered."""

    def __init__(self, strategy_id: str, available: Iterable[str]) -> None:
        self.strategy_id = strategy_id
        self.available = sorted(available)
        super().__init__(
            f"unknown strategy {strategy_id!r}; available: {', '.join(self.available)}"
        )


class StrategyRegistry:
    """Maps strategy ids to their implementing classes."""

    def __init__(self) -> None:
        self._strategies: dict[str, Type[Strategy]] = {}

    def register(self, strategy_class: Type[Strategy]) -> Type[Strategy]:
        """Add a strategy class. Returns it, so it can be used as a decorator."""
        metadata = strategy_class.metadata
        if metadata.id in self._strategies:
            raise ValueError(f"strategy id {metadata.id!r} is already registered")
        self._strategies[metadata.id] = strategy_class
        return strategy_class

    def get(self, strategy_id: str) -> Type[Strategy]:
        """Look up a strategy class by id. Case-insensitive."""
        key = strategy_id.strip().upper()
        if key not in self._strategies:
            raise UnknownStrategyError(strategy_id, self._strategies)
        return self._strategies[key]

    def create(self, strategy_id: str, rng: random.Random | None = None) -> Strategy:
        """Build a fresh instance, optionally sharing the caller's RNG."""
        return self.get(strategy_id)(rng=rng)

    def metadata(self, strategy_id: str) -> StrategyMetadata:
        return self.get(strategy_id).metadata

    def all_metadata(self) -> list[StrategyMetadata]:
        return [cls.metadata for cls in self._strategies.values()]

    def ids(self) -> list[str]:
        return list(self._strategies)

    def exists(self, strategy_id: str) -> bool:
        return strategy_id.strip().upper() in self._strategies

    def __len__(self) -> int:
        return len(self._strategies)

    def __iter__(self) -> Iterator[Type[Strategy]]:
        return iter(self._strategies.values())


strategy_registry = StrategyRegistry()

for _strategy_class in (
    AlwaysCooperate,
    AlwaysDefect,
    TitForTat,
    GrimTrigger,
    TitForTwoTats,
    RandomStrategy,
):
    strategy_registry.register(_strategy_class)
