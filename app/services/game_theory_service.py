"""Turns the analysis engine's dataclasses into API responses."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.game_theory.analysis import GameAnalysis, analyse_game
from app.game_theory.payoff import PayoffMatrix as DomainPayoffMatrix
from app.repositories.payoff_matrix import PayoffMatrixRepository
from app.schemas.game_theory import (
    AnalyzeGameRequest,
    DilemmaConditionsResponse,
    DominantStrategyResponse,
    GameAnalysisResponse,
    NashEquilibriumResponse,
    ParetoStatusResponse,
    PayoffOrderingResponse,
)
from app.schemas.payoff_matrix import PayoffMatrixInput


class GameTheoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.matrices = PayoffMatrixRepository(db)

    def analyse(self, payload: AnalyzeGameRequest) -> GameAnalysisResponse:
        """Analyse an inline matrix or a stored one."""
        if payload.matrix is not None:
            matrix = payload.matrix.to_domain()
        else:
            stored = self.matrices.get(payload.payoff_matrix_id)
            if stored is None:
                raise NotFoundError(
                    f"Payoff matrix {payload.payoff_matrix_id} was not found"
                )
            matrix = stored.to_domain()
        return self.to_response(analyse_game(matrix))

    def analyse_matrix_id(self, matrix_id: uuid.UUID) -> GameAnalysisResponse:
        stored = self.matrices.get(matrix_id)
        if stored is None:
            raise NotFoundError(f"Payoff matrix {matrix_id} was not found")
        return self.to_response(analyse_game(stored.to_domain()))

    @staticmethod
    def to_response(analysis: GameAnalysis) -> GameAnalysisResponse:
        """Map the domain analysis onto its schema, losing nothing."""
        conditions = analysis.conditions
        return GameAnalysisResponse(
            matrix=PayoffMatrixInput.from_domain(analysis.matrix),
            conditions=DilemmaConditionsResponse(
                is_prisoners_dilemma=conditions.is_prisoners_dilemma,
                ordering_holds=conditions.ordering_holds,
                averaging_condition_holds=conditions.averaging_condition_holds,
                is_symmetric=conditions.is_symmetric,
                player_a=_ordering(conditions.player_a_ordering),
                player_b=_ordering(conditions.player_b_ordering),
                failed_conditions=conditions.failed_conditions,
            ),
            dominant_strategy_player_a=_dominant(analysis.dominant_strategy_a),
            dominant_strategy_player_b=_dominant(analysis.dominant_strategy_b),
            nash_equilibria=[
                NashEquilibriumResponse(
                    outcome=eq.outcome,
                    player_a_action=eq.player_a_action,
                    player_b_action=eq.player_b_action,
                    player_a_payoff=eq.player_a_payoff,
                    player_b_payoff=eq.player_b_payoff,
                    explanation=eq.explanation,
                )
                for eq in analysis.nash_equilibria
            ],
            pareto_analysis=[
                ParetoStatusResponse(
                    outcome=status.outcome,
                    player_a_payoff=status.player_a_payoff,
                    player_b_payoff=status.player_b_payoff,
                    is_pareto_optimal=status.is_pareto_optimal,
                    dominated_by=status.dominated_by,
                    explanation=status.explanation,
                )
                for status in analysis.pareto
            ],
            pareto_optimal_outcomes=[
                status.outcome for status in analysis.pareto if status.is_pareto_optimal
            ],
            pareto_inferior_outcomes=[
                status.outcome
                for status in analysis.pareto
                if not status.is_pareto_optimal
            ],
            mutual_cooperation_pareto_superior_to_mutual_defection=(
                analysis.mutual_cooperation_pareto_superior
            ),
            equilibrium_is_pareto_inferior=analysis.equilibrium_is_pareto_inferior,
            summary=analysis.summary,
        )

    @staticmethod
    def nash_predicts_mutual_defection(matrix: DomainPayoffMatrix) -> bool:
        """True when (D,D) is the only pure-strategy equilibrium of this matrix.

        Used to decide whether reporting "the Nash prediction is 0% cooperation"
        alongside human results is meaningful for the matrix actually used.
        """
        analysis = analyse_game(matrix)
        equilibria = analysis.nash_equilibria
        return len(equilibria) == 1 and equilibria[0].outcome.value == "DD"


def _ordering(ordering) -> PayoffOrderingResponse:
    return PayoffOrderingResponse(
        player=ordering.player,
        temptation=ordering.temptation,
        reward=ordering.reward,
        punishment=ordering.punishment,
        sucker=ordering.sucker,
        ordering_holds=ordering.ordering_holds,
        averaging_condition_holds=ordering.averaging_condition_holds,
    )


def _dominant(dominant) -> DominantStrategyResponse:
    return DominantStrategyResponse(
        player=dominant.player,
        exists=dominant.exists,
        action=dominant.action,
        dominance=dominant.dominance,
        explanation=dominant.explanation,
    )
