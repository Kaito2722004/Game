"""Statistics for the human classroom experiment.

Kept separate from the simulation statistics because the inputs are database
rows recorded by a teacher rather than simulated matches.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd

from app.game_theory.actions import Action, Outcome
from app.statistics.analysis import DescriptiveStatistics, describe, pearson_correlation


@dataclass(frozen=True)
class HumanRoundRecord:
    """One recorded round of human play, independent of the ORM."""

    round_number: int
    player_a_action: Action
    player_b_action: Action
    player_a_payoff: float
    player_b_payoff: float
    match_id: str | None = None
    player_a_id: str | None = None
    player_b_id: str | None = None

    @property
    def outcome(self) -> Outcome:
        return Outcome.from_actions(self.player_a_action, self.player_b_action)


def _decisions_frame(rounds: Sequence[HumanRoundRecord]) -> pd.DataFrame:
    """One row per player-decision, so both seats count equally."""
    rows: list[dict[str, object]] = []
    for record in rounds:
        rows.append(
            {
                "round_number": record.round_number,
                "participant_id": record.player_a_id,
                "action": record.player_a_action.value,
                "payoff": record.player_a_payoff,
                "cooperated": record.player_a_action is Action.COOPERATE,
            }
        )
        rows.append(
            {
                "round_number": record.round_number,
                "participant_id": record.player_b_id,
                "action": record.player_b_action.value,
                "payoff": record.player_b_payoff,
                "cooperated": record.player_b_action is Action.COOPERATE,
            }
        )
    return pd.DataFrame(rows)


def experiment_statistics(rounds: Sequence[HumanRoundRecord]) -> dict[str, object]:
    """Every rate and average the results endpoint reports.

    With no recorded rounds every rate is 0.0 and the by-round series are
    empty, rather than raising: an experiment that has just started is a valid
    thing to ask about.
    """
    if not rounds:
        empty = describe([])
        return {
            "rounds_recorded": 0,
            "decisions_recorded": 0,
            "cooperation_rate": 0.0,
            "defection_rate": 0.0,
            "mutual_cooperation_rate": 0.0,
            "mutual_defection_rate": 0.0,
            "cd_rate": 0.0,
            "dc_rate": 0.0,
            "average_payoff": 0.0,
            "total_payoff": 0.0,
            "payoff_statistics": empty,
            "outcome_frequency": {outcome.value: 0 for outcome in Outcome},
            "cooperation_rate_by_round": [],
            "defection_rate_by_round": [],
            "payoff_by_round": [],
        }

    decisions = _decisions_frame(rounds)
    outcome_counts = {outcome.value: 0 for outcome in Outcome}
    for record in rounds:
        outcome_counts[record.outcome.value] += 1
    total_rounds = len(rounds)

    by_round = decisions.groupby("round_number", as_index=False).agg(
        cooperation_rate=("cooperated", "mean"),
        average_payoff=("payoff", "mean"),
        total_payoff=("payoff", "sum"),
    )
    by_round["cooperation_rate"] = by_round["cooperation_rate"].round(6)
    by_round["defection_rate"] = (1 - by_round["cooperation_rate"]).round(6)
    by_round["average_payoff"] = by_round["average_payoff"].round(6)

    cooperation_rate = float(decisions["cooperated"].mean())

    return {
        "rounds_recorded": total_rounds,
        "decisions_recorded": int(len(decisions)),
        "cooperation_rate": round(cooperation_rate, 6),
        "defection_rate": round(1 - cooperation_rate, 6),
        "mutual_cooperation_rate": round(outcome_counts["CC"] / total_rounds, 6),
        "mutual_defection_rate": round(outcome_counts["DD"] / total_rounds, 6),
        "cd_rate": round(outcome_counts["CD"] / total_rounds, 6),
        "dc_rate": round(outcome_counts["DC"] / total_rounds, 6),
        "average_payoff": round(float(decisions["payoff"].mean()), 6),
        "total_payoff": float(decisions["payoff"].sum()),
        "payoff_statistics": describe(decisions["payoff"].tolist()),
        "outcome_frequency": outcome_counts,
        "cooperation_rate_by_round": by_round[
            ["round_number", "cooperation_rate"]
        ].to_dict("records"),
        "defection_rate_by_round": by_round[["round_number", "defection_rate"]].to_dict(
            "records"
        ),
        "payoff_by_round": by_round[
            ["round_number", "average_payoff", "total_payoff"]
        ].to_dict("records"),
    }


def cooperation_rate_by_participant(
    rounds: Sequence[HumanRoundRecord],
) -> dict[str, float]:
    """Each participant's own cooperation rate, keyed by participant id."""
    frame = _decisions_frame(rounds)
    # An experiment with no rounds yet produces a frame with no columns at all,
    # so check emptiness before naming one.
    if frame.empty:
        return {}
    frame = frame.dropna(subset=["participant_id"])
    if frame.empty:
        return {}
    grouped = frame.groupby("participant_id")["cooperated"].mean()
    return {str(key): round(float(value), 6) for key, value in grouped.items()}


@dataclass(frozen=True)
class TrustSurveyRecord:
    """One survey answer, independent of the ORM."""

    participant_id: str
    question_type: str
    score: int


def trust_survey_statistics(
    surveys: Sequence[TrustSurveyRecord],
    cooperation_by_participant: dict[str, float],
) -> dict[str, object]:
    """Summarise the trust survey and relate it to observed cooperation.

    The correlation reported here is descriptive. A classroom sample cannot
    establish that trust causes cooperation, and the response says so.
    """
    before = [s.score for s in surveys if s.question_type == "EXPECTED_COOPERATION"]
    after = [s.score for s in surveys if s.question_type == "TRUST_AFTER"]

    def _paired(question_type: str) -> tuple[list[float], list[float]]:
        scores: list[float] = []
        rates: list[float] = []
        for survey in surveys:
            if survey.question_type != question_type:
                continue
            rate = cooperation_by_participant.get(survey.participant_id)
            if rate is not None:
                scores.append(float(survey.score))
                rates.append(rate)
        return scores, rates

    expected_scores, expected_rates = _paired("EXPECTED_COOPERATION")
    trust_scores, trust_rates = _paired("TRUST_AFTER")

    observed = list(cooperation_by_participant.values())

    return {
        "responses": len(surveys),
        "expected_cooperation_responses": len(before),
        "trust_after_responses": len(after),
        "average_expected_cooperation": round(sum(before) / len(before), 4)
        if before
        else None,
        "average_trust_after": round(sum(after) / len(after), 4) if after else None,
        "expected_cooperation_statistics": describe(before),
        "trust_after_statistics": describe(after),
        "actual_cooperation_rate": round(sum(observed) / len(observed), 6)
        if observed
        else 0.0,
        "correlation_expected_vs_actual": pearson_correlation(
            expected_scores, expected_rates
        ),
        "correlation_trust_after_vs_actual": pearson_correlation(
            trust_scores, trust_rates
        ),
        "interpretation_note": (
            "Correlations are descriptive summaries of this classroom sample. "
            "They do not establish that trust causes cooperation."
        ),
    }


__all__ = [
    "DescriptiveStatistics",
    "HumanRoundRecord",
    "TrustSurveyRecord",
    "cooperation_rate_by_participant",
    "experiment_statistics",
    "trust_survey_statistics",
]
