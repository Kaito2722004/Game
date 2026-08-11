"""Axelrod-style round-robin tournament engine."""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field

from app.game_theory.payoff import PayoffMatrix
from app.simulation.match import MatchResult, SimulationError, play_match
from app.strategies.registry import strategy_registry

MAX_STRATEGIES = 50
MAX_REPETITIONS = 1000


@dataclass
class StrategyRecord:
    """Running totals for one strategy across the whole tournament."""

    strategy_id: str
    total_score: float = 0.0
    rounds_played: int = 0
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    cooperation_count: int = 0
    defection_count: int = 0

    @property
    def average_score(self) -> float:
        """Mean payoff per round played."""
        return self.total_score / self.rounds_played if self.rounds_played else 0.0

    @property
    def average_score_per_match(self) -> float:
        return self.total_score / self.matches_played if self.matches_played else 0.0

    @property
    def total_actions(self) -> int:
        return self.cooperation_count + self.defection_count

    @property
    def cooperation_rate(self) -> float:
        return self.cooperation_count / self.total_actions if self.total_actions else 0.0

    @property
    def defection_rate(self) -> float:
        return self.defection_count / self.total_actions if self.total_actions else 0.0


@dataclass(frozen=True)
class RankedStrategy:
    """A strategy's final placing."""

    rank: int
    strategy_id: str
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


@dataclass(frozen=True)
class TournamentResult:
    """Everything produced by one tournament run."""

    strategy_ids: list[str]
    rounds_per_match: int
    repetitions: int
    seed: int | None
    continuation_probability: float | None
    include_self_play: bool
    matches: list[MatchResult]
    rankings: list[RankedStrategy]
    matrix: PayoffMatrix
    records: dict[str, StrategyRecord] = field(default_factory=dict)

    @property
    def matches_played(self) -> int:
        return len(self.matches)

    @property
    def winner_id(self) -> str | None:
        return self.rankings[0].strategy_id if self.rankings else None


def _validate(
    strategy_ids: list[str], rounds: int, repetitions: int, include_self_play: bool
) -> None:
    if not strategy_ids:
        raise SimulationError("a tournament needs at least one strategy")
    if len(strategy_ids) < 2 and not include_self_play:
        raise SimulationError(
            "a tournament needs at least two strategies, or one strategy with "
            "self-play enabled"
        )
    if len(strategy_ids) > MAX_STRATEGIES:
        raise SimulationError(f"at most {MAX_STRATEGIES} strategies are allowed")
    duplicates = {sid for sid in strategy_ids if strategy_ids.count(sid) > 1}
    if duplicates:
        raise SimulationError(
            "duplicate strategies are not allowed: " + ", ".join(sorted(duplicates))
        )
    if rounds < 1:
        raise SimulationError("rounds_per_match must be at least 1")
    if repetitions < 1:
        raise SimulationError("repetitions must be at least 1")
    if repetitions > MAX_REPETITIONS:
        raise SimulationError(f"repetitions must not exceed {MAX_REPETITIONS}")
    for strategy_id in strategy_ids:
        strategy_registry.get(strategy_id)  # raises UnknownStrategyError


def build_rankings(records: dict[str, StrategyRecord]) -> list[RankedStrategy]:
    """Rank strategies by total score, with a deterministic tie-break.

    Ties are broken by average score per round, then cooperation rate, then
    strategy id alphabetically, so two runs of the same tournament always
    produce the same table. Tied strategies share a rank number.
    """
    ordered = sorted(
        records.values(),
        key=lambda record: (
            -record.total_score,
            -record.average_score,
            -record.cooperation_rate,
            record.strategy_id,
        ),
    )

    rankings: list[RankedStrategy] = []
    previous_score: float | None = None
    rank = 0
    for position, record in enumerate(ordered, start=1):
        if previous_score is None or record.total_score != previous_score:
            rank = position
            previous_score = record.total_score
        rankings.append(
            RankedStrategy(
                rank=rank,
                strategy_id=record.strategy_id,
                total_score=record.total_score,
                average_score=record.average_score,
                matches_played=record.matches_played,
                rounds_played=record.rounds_played,
                wins=record.wins,
                draws=record.draws,
                losses=record.losses,
                cooperation_count=record.cooperation_count,
                defection_count=record.defection_count,
                cooperation_rate=record.cooperation_rate,
                defection_rate=record.defection_rate,
            )
        )
    return rankings


def run_tournament(
    strategy_ids: list[str],
    rounds_per_match: int,
    matrix: PayoffMatrix,
    repetitions: int = 1,
    seed: int | None = None,
    continuation_probability: float | None = None,
    include_self_play: bool = False,
) -> TournamentResult:
    """Play every selected strategy against every other and rank the field.

    The ranking is produced entirely by the simulation. No expected ordering
    is encoded anywhere in this module.
    """
    strategy_ids = [sid.strip().upper() for sid in strategy_ids]
    _validate(strategy_ids, rounds_per_match, repetitions, include_self_play)

    rng = random.Random(seed)
    pairings = list(itertools.combinations(strategy_ids, 2))
    if include_self_play:
        pairings += [(sid, sid) for sid in strategy_ids]

    records = {sid: StrategyRecord(strategy_id=sid) for sid in strategy_ids}
    matches: list[MatchResult] = []

    for _ in range(repetitions):
        for id_a, id_b in pairings:
            strategy_a = strategy_registry.create(id_a, rng=rng)
            strategy_b = strategy_registry.create(id_b, rng=rng)
            result = play_match(
                strategy_a,
                strategy_b,
                rounds=rounds_per_match,
                matrix=matrix,
                rng=rng,
                continuation_probability=continuation_probability,
                seed=seed,
            )
            matches.append(result)

            for strategy_id, stats, opponent_total in (
                (id_a, result.player_a, result.player_b.total_payoff),
                (id_b, result.player_b, result.player_a.total_payoff),
            ):
                record = records[strategy_id]
                record.total_score += stats.total_payoff
                record.rounds_played += result.rounds_played
                record.matches_played += 1
                record.cooperation_count += stats.cooperation_count
                record.defection_count += stats.defection_count
                if stats.total_payoff > opponent_total:
                    record.wins += 1
                elif stats.total_payoff < opponent_total:
                    record.losses += 1
                else:
                    record.draws += 1

    return TournamentResult(
        strategy_ids=strategy_ids,
        rounds_per_match=rounds_per_match,
        repetitions=repetitions,
        seed=seed,
        continuation_probability=continuation_probability,
        include_self_play=include_self_play,
        matches=matches,
        rankings=build_rankings(records),
        matrix=matrix,
        records=records,
    )
