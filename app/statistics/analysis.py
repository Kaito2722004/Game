"""Statistical summaries built with pandas.

Everything the frontend might want to chart is computed here so that no
game-theoretic or statistical work is left to the client.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from app.game_theory.actions import Action, Outcome
from app.simulation.match import MatchResult
from app.simulation.tournament import TournamentResult


@dataclass(frozen=True)
class DescriptiveStatistics:
    """Standard descriptive statistics for one numeric series."""

    count: int
    mean: float
    median: float
    standard_deviation: float
    minimum: float
    maximum: float
    total: float


def describe(values: Sequence[float]) -> DescriptiveStatistics:
    """Mean, median, standard deviation and range for a series.

    Uses the sample standard deviation (ddof=1) and reports 0.0 for a single
    observation, where the sample deviation is undefined.
    """
    series = pd.Series(list(values), dtype="float64")
    if series.empty:
        return DescriptiveStatistics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    deviation = float(series.std(ddof=1)) if len(series) > 1 else 0.0
    return DescriptiveStatistics(
        count=int(series.count()),
        mean=float(series.mean()),
        median=float(series.median()),
        standard_deviation=deviation,
        minimum=float(series.min()),
        maximum=float(series.max()),
        total=float(series.sum()),
    )


def pearson_correlation(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Pearson correlation, or None when it is not defined.

    Returns None for fewer than three paired observations or when either
    series is constant. Correlation here is descriptive only and never
    licenses a causal claim.
    """
    frame = pd.DataFrame({"x": list(x), "y": list(y)}).dropna()
    if len(frame) < 3 or frame["x"].nunique() < 2 or frame["y"].nunique() < 2:
        return None
    value = float(np.corrcoef(frame["x"], frame["y"])[0, 1])
    return None if np.isnan(value) else round(value, 4)


def match_rounds_frame(match: MatchResult) -> pd.DataFrame:
    """Round-by-round record of a match as a DataFrame."""
    return pd.DataFrame(
        [
            {
                "round_number": result.round_number,
                "player_a_action": result.player_a_action.value,
                "player_b_action": result.player_b_action.value,
                "player_a_payoff": result.player_a_payoff,
                "player_b_payoff": result.player_b_payoff,
                "outcome": result.outcome.value,
            }
            for result in match.rounds
        ]
    )


def cumulative_scores(match: MatchResult) -> list[dict[str, float]]:
    """Running totals after each round, for a cumulative-score chart."""
    frame = match_rounds_frame(match)
    if frame.empty:
        return []
    frame["player_a_cumulative"] = frame["player_a_payoff"].cumsum()
    frame["player_b_cumulative"] = frame["player_b_payoff"].cumsum()
    return frame[
        ["round_number", "player_a_cumulative", "player_b_cumulative"]
    ].to_dict("records")


def outcome_frequency(matches: Iterable[MatchResult]) -> dict[str, int]:
    """How often each of the four outcomes occurred across some matches."""
    totals = {outcome.value: 0 for outcome in Outcome}
    for match in matches:
        for outcome, count in match.outcome_counts.items():
            totals[outcome.value] += count
    return totals


def outcome_rates(matches: Iterable[MatchResult]) -> dict[str, float]:
    """Outcome frequencies normalised to rates.

    Deliberately not rounded: rounding each rate independently can push the
    total to 1.000001, which shows up as a broken pie chart on the frontend.
    """
    counts = outcome_frequency(matches)
    total = sum(counts.values())
    if not total:
        return {key: 0.0 for key in counts}
    return {key: value / total for key, value in counts.items()}


def cooperation_by_round(matches: Iterable[MatchResult]) -> list[dict[str, float]]:
    """Cooperation rate in each round number, pooled over matches.

    Shows how cooperation develops across the length of a match.
    """
    rows: list[dict[str, object]] = []
    for match in matches:
        for result in match.rounds:
            rows.append(
                {
                    "round_number": result.round_number,
                    "cooperated": result.player_a_action is Action.COOPERATE,
                }
            )
            rows.append(
                {
                    "round_number": result.round_number,
                    "cooperated": result.player_b_action is Action.COOPERATE,
                }
            )
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    grouped = (
        frame.groupby("round_number", as_index=False)["cooperated"]
        .mean()
        .rename(columns={"cooperated": "cooperation_rate"})
    )
    grouped["cooperation_rate"] = grouped["cooperation_rate"].round(6)
    return grouped.to_dict("records")


def tournament_score_statistics(result: TournamentResult) -> DescriptiveStatistics:
    """Descriptive statistics over the strategies' total scores."""
    return describe([ranking.total_score for ranking in result.rankings])


def head_to_head_matrix(result: TournamentResult) -> list[dict[str, object]]:
    """Average payoff per round for each ordered pair of strategies."""
    rows: list[dict[str, object]] = []
    for match in result.matches:
        rounds = match.rounds_played or 1
        rows.append(
            {
                "strategy_id": match.strategy_a_id,
                "opponent_id": match.strategy_b_id,
                "average_payoff": match.player_a.total_payoff / rounds,
            }
        )
        rows.append(
            {
                "strategy_id": match.strategy_b_id,
                "opponent_id": match.strategy_a_id,
                "average_payoff": match.player_b.total_payoff / rounds,
            }
        )
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    grouped = frame.groupby(["strategy_id", "opponent_id"], as_index=False)[
        "average_payoff"
    ].mean()
    grouped["average_payoff"] = grouped["average_payoff"].round(6)
    return grouped.to_dict("records")


def tournament_statistics(result: TournamentResult) -> dict[str, object]:
    """The full statistics payload for a completed tournament."""
    scores = tournament_score_statistics(result)
    cooperation_rates = [ranking.cooperation_rate for ranking in result.rankings]
    return {
        "matches_played": result.matches_played,
        "rounds_per_match": result.rounds_per_match,
        "repetitions": result.repetitions,
        "score_statistics": scores,
        "cooperation_rate_statistics": describe(cooperation_rates),
        "outcome_frequency": outcome_frequency(result.matches),
        "outcome_rates": outcome_rates(result.matches),
        "cooperation_by_round": cooperation_by_round(result.matches),
        "head_to_head": head_to_head_matrix(result),
    }
