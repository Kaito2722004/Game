"""Human classroom experiment: setup, pairing, round recording, statistics."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.experiment import (
    Experiment,
    ExperimentParticipant,
    ExperimentStatus,
    HumanMatch,
    HumanRound,
)
from app.models.user import User
from app.repositories.experiment import ExperimentRepository
from app.schemas.experiment import (
    ExperimentCreateRequest,
    ExperimentResponse,
    ExperimentResultsResponse,
    ExperimentStartResponse,
    ExperimentStatisticsResponse,
    ExperimentUpdateRequest,
    HumanMatchResponse,
    HumanRoundResponse,
    ParticipantCreateRequest,
    ParticipantResponse,
    RateByRound,
    RoundSubmissionRequest,
)
from app.schemas.statistics import DescriptiveStatisticsResponse
from app.services.game_theory_service import GameTheoryService
from app.services.payoff_matrix_service import PayoffMatrixService
from app.statistics.experiment_analysis import (
    HumanRoundRecord,
    cooperation_rate_by_participant,
    experiment_statistics,
)


class ExperimentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ExperimentRepository(db)
        self.matrices = PayoffMatrixService(db)

    # ------------------------------------------------------------- CRUD ----
    def create(
        self, payload: ExperimentCreateRequest, actor: User | None = None
    ) -> ExperimentResponse:
        matrix = (
            self.matrices.get_model(payload.payoff_matrix_id)
            if payload.payoff_matrix_id
            else self.matrices.get_default_model()
        )
        experiment = Experiment(
            name=payload.name,
            description=payload.description,
            status=ExperimentStatus.DRAFT,
            rounds=payload.rounds,
            anonymous_mode=payload.anonymous_mode,
            trust_survey_enabled=payload.trust_survey_enabled,
            payoff_matrix_id=matrix.id,
            created_by_id=actor.id if actor else None,
        )
        self.repository.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)
        return self.to_response(experiment)

    def get_model(self, experiment_id: uuid.UUID) -> Experiment:
        experiment = self.repository.get(experiment_id)
        if experiment is None:
            raise NotFoundError(f"Experiment {experiment_id} was not found")
        return experiment

    def get(self, experiment_id: uuid.UUID) -> ExperimentResponse:
        return self.to_response(self.get_model(experiment_id))

    def list(self, limit: int = 100, offset: int = 0) -> list[ExperimentResponse]:
        return [
            self.to_response(row)
            for row in self.repository.list(limit=limit, offset=offset)
        ]

    def update(
        self, experiment_id: uuid.UUID, payload: ExperimentUpdateRequest
    ) -> ExperimentResponse:
        experiment = self.get_model(experiment_id)
        if experiment.status is not ExperimentStatus.DRAFT:
            raise ConflictError(
                "Settings can only be changed while the experiment is a DRAFT"
            )
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(experiment, field, value)
        self.db.commit()
        self.db.refresh(experiment)
        return self.to_response(experiment)

    def to_response(self, experiment: Experiment) -> ExperimentResponse:
        return ExperimentResponse(
            id=experiment.id,
            name=experiment.name,
            description=experiment.description,
            status=experiment.status,
            rounds=experiment.rounds,
            anonymous_mode=experiment.anonymous_mode,
            trust_survey_enabled=experiment.trust_survey_enabled,
            payoff_matrix_id=experiment.payoff_matrix_id,
            participant_count=self.repository.count_participants(experiment.id),
            pair_count=self.repository.count_matches(experiment.id),
            started_at=experiment.started_at,
            completed_at=experiment.completed_at,
            created_at=experiment.created_at,
        )

    # ------------------------------------------------------ participants ----
    def add_participant(
        self, experiment_id: uuid.UUID, payload: ParticipantCreateRequest
    ) -> ParticipantResponse:
        experiment = self.get_model(experiment_id)
        if experiment.status is not ExperimentStatus.DRAFT:
            raise ConflictError(
                "Participants can only be added while the experiment is a DRAFT"
            )
        code = payload.code.strip()
        if self.repository.get_participant_by_code(experiment_id, code) is not None:
            raise ConflictError(
                f"A participant with code {code!r} is already in this experiment"
            )

        participant = ExperimentParticipant(
            experiment_id=experiment_id,
            code=code,
            display_name=payload.display_name,
        )
        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)
        return ParticipantResponse.model_validate(participant)

    def list_participants(self, experiment_id: uuid.UUID) -> list[ParticipantResponse]:
        self.get_model(experiment_id)
        return [
            ParticipantResponse.model_validate(row)
            for row in self.repository.list_participants(experiment_id)
        ]

    def remove_participant(
        self, experiment_id: uuid.UUID, participant_id: uuid.UUID
    ) -> None:
        experiment = self.get_model(experiment_id)
        if experiment.status is not ExperimentStatus.DRAFT:
            raise ConflictError(
                "Participants can only be removed while the experiment is a DRAFT"
            )
        participant = self.repository.get_participant(experiment_id, participant_id)
        if participant is None:
            raise NotFoundError(
                f"Participant {participant_id} is not in experiment {experiment_id}"
            )
        self.db.delete(participant)
        self.db.commit()

    # ------------------------------------------------------------ start ----
    def start(
        self, experiment_id: uuid.UUID, seed: int | None = None
    ) -> ExperimentStartResponse:
        """Pair participants at random and open the experiment for rounds.

        With an odd number of participants one is left unpaired and reported
        in `unpaired_participant_ids`, rather than silently dropped.
        """
        experiment = self.get_model(experiment_id)
        if experiment.status is ExperimentStatus.RUNNING:
            raise ConflictError("This experiment has already been started")
        if experiment.status is ExperimentStatus.COMPLETED:
            raise ConflictError("This experiment has already been completed")

        participants = list(self.repository.list_participants(experiment_id))
        if len(participants) < 2:
            raise ValidationError(
                "At least two participants are needed to start an experiment",
                [f"{len(participants)} participant(s) registered"],
            )

        shuffled = list(participants)
        random.Random(seed).shuffle(shuffled)

        pairs: list[HumanMatch] = []
        for index in range(0, len(shuffled) - 1, 2):
            match = HumanMatch(
                experiment_id=experiment_id,
                pair_number=index // 2 + 1,
                participant_a_id=shuffled[index].id,
                participant_b_id=shuffled[index + 1].id,
            )
            self.db.add(match)
            pairs.append(match)

        unpaired = [shuffled[-1].id] if len(shuffled) % 2 else []

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now(timezone.utc)
        self.db.commit()
        for match in pairs:
            self.db.refresh(match)

        return ExperimentStartResponse(
            experiment_id=experiment.id,
            status=experiment.status,
            pairs=[self._match_response(experiment, match) for match in pairs],
            unpaired_participant_ids=unpaired,
        )

    def complete(self, experiment_id: uuid.UUID) -> ExperimentResponse:
        experiment = self.get_model(experiment_id)
        if experiment.status is not ExperimentStatus.RUNNING:
            raise ConflictError("Only a RUNNING experiment can be completed")
        experiment.status = ExperimentStatus.COMPLETED
        experiment.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(experiment)
        return self.to_response(experiment)

    # ----------------------------------------------------------- rounds ----
    def submit_round(
        self, experiment_id: uuid.UUID, payload: RoundSubmissionRequest
    ) -> HumanRoundResponse:
        """Record one round. The backend computes the payoffs.

        Whatever the client believes the score to be is irrelevant: payoffs
        come from the experiment's own payoff matrix.
        """
        experiment = self.get_model(experiment_id)
        if experiment.status is not ExperimentStatus.RUNNING:
            raise ConflictError(
                "Rounds can only be submitted while the experiment is RUNNING"
            )

        match = self.repository.get_match(experiment_id, payload.match_id)
        if match is None:
            raise NotFoundError(
                f"Match {payload.match_id} is not part of experiment {experiment_id}"
            )
        if payload.round_number > experiment.rounds:
            raise ValidationError(
                f"This experiment is configured for {experiment.rounds} rounds",
                [f"round_number {payload.round_number} exceeds the configured total"],
            )
        if self.repository.get_round(match.id, payload.round_number) is not None:
            raise ConflictError(
                f"Round {payload.round_number} has already been recorded for this pair"
            )

        matrix = experiment.payoff_matrix.to_domain()
        payoff_a, payoff_b = matrix.payoff(payload.player_a_action, payload.player_b_action)

        round_row = HumanRound(
            experiment_id=experiment_id,
            match_id=match.id,
            round_number=payload.round_number,
            player_a_id=match.participant_a_id,
            player_b_id=match.participant_b_id,
            player_a_action=payload.player_a_action,
            player_b_action=payload.player_b_action,
            player_a_payoff=payoff_a,
            player_b_payoff=payoff_b,
        )
        self.db.add(round_row)

        match.player_a_score += payoff_a
        match.player_b_score += payoff_b
        match.is_complete = (
            self.repository.count_rounds_for_match(match.id) + 1
        ) >= experiment.rounds

        self.db.commit()
        self.db.refresh(round_row)
        return HumanRoundResponse.model_validate(round_row)

    # ---------------------------------------------------------- results ----
    def results(self, experiment_id: uuid.UUID) -> ExperimentResultsResponse:
        experiment = self.get_model(experiment_id)
        matches = self.repository.list_matches(experiment_id)
        rounds = self.repository.list_rounds(experiment_id)
        return ExperimentResultsResponse(
            experiment_id=experiment.id,
            status=experiment.status,
            rounds_configured=experiment.rounds,
            matches=[self._match_response(experiment, match) for match in matches],
            rounds=[HumanRoundResponse.model_validate(row) for row in rounds],
        )

    def statistics(self, experiment_id: uuid.UUID) -> ExperimentStatisticsResponse:
        experiment = self.get_model(experiment_id)
        records = self._round_records(experiment_id)
        payload = experiment_statistics(records)

        matrix = experiment.payoff_matrix.to_domain()
        nash_applies = GameTheoryService.nash_predicts_mutual_defection(matrix)

        return ExperimentStatisticsResponse(
            experiment_id=experiment.id,
            rounds_recorded=payload["rounds_recorded"],
            decisions_recorded=payload["decisions_recorded"],
            cooperation_rate=payload["cooperation_rate"],
            defection_rate=payload["defection_rate"],
            mutual_cooperation_rate=payload["mutual_cooperation_rate"],
            mutual_defection_rate=payload["mutual_defection_rate"],
            cd_rate=payload["cd_rate"],
            dc_rate=payload["dc_rate"],
            average_payoff=payload["average_payoff"],
            total_payoff=payload["total_payoff"],
            payoff_statistics=DescriptiveStatisticsResponse.model_validate(
                payload["payoff_statistics"]
            ),
            outcome_frequency=payload["outcome_frequency"],
            cooperation_rate_by_round=[
                RateByRound(**row) for row in payload["cooperation_rate_by_round"]
            ],
            defection_rate_by_round=[
                RateByRound(**row) for row in payload["defection_rate_by_round"]
            ],
            payoff_by_round=[RateByRound(**row) for row in payload["payoff_by_round"]],
            nash_prediction_applies=nash_applies,
        )

    def cooperation_by_participant(self, experiment_id: uuid.UUID) -> dict[str, float]:
        return cooperation_rate_by_participant(self._round_records(experiment_id))

    def _round_records(self, experiment_id: uuid.UUID) -> list[HumanRoundRecord]:
        return [
            HumanRoundRecord(
                round_number=row.round_number,
                player_a_action=row.player_a_action,
                player_b_action=row.player_b_action,
                player_a_payoff=row.player_a_payoff,
                player_b_payoff=row.player_b_payoff,
                match_id=str(row.match_id),
                player_a_id=str(row.player_a_id),
                player_b_id=str(row.player_b_id),
            )
            for row in self.repository.list_rounds(experiment_id)
        ]

    def _match_response(
        self, experiment: Experiment, match: HumanMatch
    ) -> HumanMatchResponse:
        anonymous = experiment.anonymous_mode
        return HumanMatchResponse(
            id=match.id,
            pair_number=match.pair_number,
            participant_a_id=match.participant_a_id,
            participant_b_id=match.participant_b_id,
            participant_a_label=match.participant_a.public_label(anonymous),
            participant_b_label=match.participant_b.public_label(anonymous),
            player_a_score=match.player_a_score,
            player_b_score=match.player_b_score,
            rounds_recorded=self.repository.count_rounds_for_match(match.id),
            is_complete=match.is_complete,
        )
