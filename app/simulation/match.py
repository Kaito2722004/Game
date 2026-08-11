"""Iterated Prisoner's Dilemma match between two strategies."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.game_theory.actions import Action, Outcome
from app.game_theory.payoff import PayoffMatrix
from app.simulation.game import RoundResult, play_round, should_continue
from app.strategies.base import Strategy
from app.strategies.registry import strategy_registry

MAX_ROUNDS_LIMIT = 10_000


class SimulationError(ValueError):
    """Raised when a simulation is asked for something it cannot do."""


@dataclass(frozen=True)
class PlayerMatchStatistics:
    """One player's record within a single match."""

    strategy_id: str
    total_payoff: float
    average_payoff: float
    cooperation_count: int
    defection_count: int
    cooperation_rate: float
    defection_rate: float


@dataclass(frozen=True)
class MatchResult:
    """The complete record of one match."""

    strategy_a_id: str
    strategy_b_id: str
    rounds_played: int
    rounds_requested: int
    continuation_probability: float | None
    seed: int | None
    rounds: list[RoundResult]
    player_a: PlayerMatchStatistics
    player_b: PlayerMatchStatistics
    winner: str | None
    outcome_counts: dict[Outcome, int] = field(default_factory=dict)

    @property
    def is_draw(self) -> bool:
        return self.winner is None


def _player_statistics(
    strategy_id: str, actions: list[Action], payoffs: list[float]
) -> PlayerMatchStatistics:
    rounds = len(actions)
    cooperations = sum(1 for action in actions if action is Action.COOPERATE)
    total = float(sum(payoffs))
    return PlayerMatchStatistics(
        strategy_id=strategy_id,
        total_payoff=total,
        average_payoff=total / rounds if rounds else 0.0,
        cooperation_count=cooperations,
        defection_count=rounds - cooperations,
        cooperation_rate=cooperations / rounds if rounds else 0.0,
        defection_rate=(rounds - cooperations) / rounds if rounds else 0.0,
    )


def _validate(rounds: int, continuation_probability: float | None) -> None:
    if rounds < 1:
        raise SimulationError("rounds must be at least 1")
    if rounds > MAX_ROUNDS_LIMIT:
        raise SimulationError(f"rounds must not exceed {MAX_ROUNDS_LIMIT}")
    if continuation_probability is not None and not 0.0 <= continuation_probability <= 1.0:
        raise SimulationError("continuation_probability must be between 0 and 1")


def play_match(
    strategy_a: Strategy,
    strategy_b: Strategy,
    rounds: int,
    matrix: PayoffMatrix,
    rng: random.Random | None = None,
    continuation_probability: float | None = None,
    seed: int | None = None,
) -> MatchResult:
    """Play an iterated match and return its full record.

    `rounds` is the fixed length of the match, or its upper bound when a
    continuation probability is supplied.
    """
    _validate(rounds, continuation_probability)
    rng = rng or random.Random(seed)

    strategy_a.reset()
    strategy_b.reset()

    history_a: list[Action] = []
    history_b: list[Action] = []
    payoffs_a: list[float] = []
    payoffs_b: list[float] = []
    round_results: list[RoundResult] = []
    outcome_counts: dict[Outcome, int] = {outcome: 0 for outcome in Outcome}

    round_number = 0
    while True:
        round_number += 1
        result = play_round(
            round_number, strategy_a, strategy_b, history_a, history_b, matrix
        )
        history_a.append(result.player_a_action)
        history_b.append(result.player_b_action)
        payoffs_a.append(result.player_a_payoff)
        payoffs_b.append(result.player_b_payoff)
        outcome_counts[result.outcome] += 1
        round_results.append(result)

        if not should_continue(round_number, rounds, continuation_probability, rng):
            break

    stats_a = _player_statistics(strategy_a.id, history_a, payoffs_a)
    stats_b = _player_statistics(strategy_b.id, history_b, payoffs_b)

    if stats_a.total_payoff > stats_b.total_payoff:
        winner: str | None = strategy_a.id
    elif stats_b.total_payoff > stats_a.total_payoff:
        winner = strategy_b.id
    else:
        winner = None

    return MatchResult(
        strategy_a_id=strategy_a.id,
        strategy_b_id=strategy_b.id,
        rounds_played=len(round_results),
        rounds_requested=rounds,
        continuation_probability=continuation_probability,
        seed=seed,
        rounds=round_results,
        player_a=stats_a,
        player_b=stats_b,
        winner=winner,
        outcome_counts=outcome_counts,
    )


def simulate_match(
    strategy_a_id: str,
    strategy_b_id: str,
    rounds: int,
    matrix: PayoffMatrix,
    seed: int | None = None,
    continuation_probability: float | None = None,
) -> MatchResult:
    """Build both strategies from the registry and play a match.

    Both strategies share one seeded RNG, so the whole match replays exactly
    from the same seed.
    """
    rng = random.Random(seed)
    strategy_a = strategy_registry.create(strategy_a_id, rng=rng)
    strategy_b = strategy_registry.create(strategy_b_id, rng=rng)
    return play_match(
        strategy_a,
        strategy_b,
        rounds=rounds,
        matrix=matrix,
        rng=rng,
        continuation_probability=continuation_probability,
        seed=seed,
    )
