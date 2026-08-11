"""CSV export of tournament and experiment data."""

from __future__ import annotations

import csv
import io
import uuid
from typing import Iterable, Sequence

from sqlalchemy.orm import Session

from app.repositories.experiment import ExperimentRepository
from app.repositories.tournament import TournamentRepository
from app.services.experiment_service import ExperimentService
from app.services.tournament_service import TournamentService


def _to_csv(header: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


class ExportService:
    """Builds CSV documents from stored results.

    Each method returns the CSV text; the route wraps it in a download
    response with the right filename.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.tournaments = TournamentService(db)
        self.tournament_repository = TournamentRepository(db)
        self.experiments = ExperimentService(db)
        self.experiment_repository = ExperimentRepository(db)

    def tournament_results_csv(self, tournament_id: uuid.UUID) -> str:
        results = self.tournaments.results(tournament_id)
        return _to_csv(
            [
                "rank",
                "strategy_id",
                "strategy_name",
                "total_score",
                "average_score",
                "matches_played",
                "rounds_played",
                "wins",
                "draws",
                "losses",
                "cooperation_count",
                "defection_count",
                "cooperation_rate",
                "defection_rate",
            ],
            [
                [
                    row.rank,
                    row.strategy_id,
                    row.strategy_name,
                    row.total_score,
                    round(row.average_score, 6),
                    row.matches_played,
                    row.rounds_played,
                    row.wins,
                    row.draws,
                    row.losses,
                    row.cooperation_count,
                    row.defection_count,
                    round(row.cooperation_rate, 6),
                    round(row.defection_rate, 6),
                ]
                for row in results.rankings
            ],
        )

    def tournament_rounds_csv(self, tournament_id: uuid.UUID) -> str:
        """Every round of every match: the raw data behind the results."""
        self.tournaments.get_model(tournament_id)
        matches = {
            match.id: match
            for match in self.tournament_repository.list_matches(tournament_id)
        }
        rounds = self.tournament_repository.list_rounds_for_tournament(tournament_id)
        return _to_csv(
            [
                "match_sequence",
                "repetition",
                "strategy_a",
                "strategy_b",
                "round_number",
                "player_a_action",
                "player_b_action",
                "player_a_payoff",
                "player_b_payoff",
            ],
            [
                [
                    matches[row.match_id].sequence,
                    matches[row.match_id].repetition,
                    matches[row.match_id].strategy_a_code,
                    matches[row.match_id].strategy_b_code,
                    row.round_number,
                    row.player_a_action.value,
                    row.player_b_action.value,
                    row.player_a_payoff,
                    row.player_b_payoff,
                ]
                for row in rounds
            ],
        )

    def experiment_rounds_csv(self, experiment_id: uuid.UUID) -> str:
        experiment = self.experiments.get_model(experiment_id)
        anonymous = experiment.anonymous_mode
        participants = {
            row.id: row.public_label(anonymous)
            for row in self.experiment_repository.list_participants(experiment_id)
        }
        matches = {
            match.id: match
            for match in self.experiment_repository.list_matches(experiment_id)
        }
        rounds = self.experiment_repository.list_rounds(experiment_id)
        return _to_csv(
            [
                "pair_number",
                "round_number",
                "player_a",
                "player_b",
                "player_a_action",
                "player_b_action",
                "player_a_payoff",
                "player_b_payoff",
            ],
            [
                [
                    matches[row.match_id].pair_number,
                    row.round_number,
                    participants.get(row.player_a_id, str(row.player_a_id)),
                    participants.get(row.player_b_id, str(row.player_b_id)),
                    row.player_a_action.value,
                    row.player_b_action.value,
                    row.player_a_payoff,
                    row.player_b_payoff,
                ]
                for row in rounds
            ],
        )

    def experiment_surveys_csv(self, experiment_id: uuid.UUID) -> str:
        experiment = self.experiments.get_model(experiment_id)
        anonymous = experiment.anonymous_mode
        participants = {
            row.id: row.public_label(anonymous)
            for row in self.experiment_repository.list_participants(experiment_id)
        }
        cooperation = self.experiments.cooperation_by_participant(experiment_id)
        surveys = self.experiment_repository.list_surveys(experiment_id)
        return _to_csv(
            ["participant", "question_type", "score", "cooperation_rate"],
            [
                [
                    participants.get(row.participant_id, str(row.participant_id)),
                    row.question_type.value,
                    row.score,
                    cooperation.get(str(row.participant_id), ""),
                ]
                for row in surveys
            ],
        )
