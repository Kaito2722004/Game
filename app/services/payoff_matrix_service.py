"""CRUD for stored payoff matrices."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.game_theory.payoff import PayoffMatrix as DomainPayoffMatrix
from app.models.payoff_matrix import PayoffMatrix
from app.models.user import User
from app.repositories.payoff_matrix import PayoffMatrixRepository
from app.schemas.payoff_matrix import (
    PayoffMatrixCreate,
    PayoffMatrixResponse,
    PayoffMatrixUpdate,
)

DEFAULT_MATRIX_NAME = "Classic Prisoner's Dilemma"


class PayoffMatrixService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = PayoffMatrixRepository(db)

    def list(self, limit: int = 100, offset: int = 0) -> list[PayoffMatrixResponse]:
        return [
            PayoffMatrixResponse.from_model(row)
            for row in self.repository.list(limit=limit, offset=offset)
        ]

    def get(self, matrix_id: uuid.UUID) -> PayoffMatrixResponse:
        return PayoffMatrixResponse.from_model(self.get_model(matrix_id))

    def get_model(self, matrix_id: uuid.UUID) -> PayoffMatrix:
        matrix = self.repository.get(matrix_id)
        if matrix is None:
            raise NotFoundError(f"Payoff matrix {matrix_id} was not found")
        return matrix

    def get_default_model(self) -> PayoffMatrix:
        """The matrix used when a request does not name one."""
        matrix = self.repository.get_default()
        if matrix is None:
            raise NotFoundError(
                "No default payoff matrix is configured. Run the seed command "
                "or create a matrix with is_default set."
            )
        return matrix

    def resolve_domain_matrix(
        self,
        inline_matrix,
        matrix_id: uuid.UUID | None,
    ) -> tuple[DomainPayoffMatrix, PayoffMatrix | None]:
        """Pick the matrix a simulation should use.

        Precedence: an inline matrix, then a stored one by id, then the
        default. Returns the domain object and the stored row when there is
        one, because tournaments record which stored matrix they used.
        """
        if inline_matrix is not None:
            return inline_matrix.to_domain(), None
        if matrix_id is not None:
            stored = self.get_model(matrix_id)
            return stored.to_domain(), stored
        stored = self.get_default_model()
        return stored.to_domain(), stored

    def create(
        self, payload: PayoffMatrixCreate, actor: User | None = None
    ) -> PayoffMatrixResponse:
        if self.repository.get_by_name(payload.name) is not None:
            raise ConflictError(f"A payoff matrix named {payload.name!r} already exists")

        matrix = PayoffMatrix(
            name=payload.name,
            description=payload.description,
            cc_player_a=payload.cc.player_a_payoff,
            cc_player_b=payload.cc.player_b_payoff,
            cd_player_a=payload.cd.player_a_payoff,
            cd_player_b=payload.cd.player_b_payoff,
            dc_player_a=payload.dc.player_a_payoff,
            dc_player_b=payload.dc.player_b_payoff,
            dd_player_a=payload.dd.player_a_payoff,
            dd_player_b=payload.dd.player_b_payoff,
            is_default=payload.is_default,
            created_by_id=actor.id if actor else None,
        )
        self.repository.add(matrix)
        if payload.is_default:
            self.repository.clear_default(except_id=matrix.id)
        self.db.commit()
        self.db.refresh(matrix)
        return PayoffMatrixResponse.from_model(matrix)

    def update(
        self, matrix_id: uuid.UUID, payload: PayoffMatrixUpdate
    ) -> PayoffMatrixResponse:
        matrix = self.get_model(matrix_id)

        if payload.name is not None and payload.name != matrix.name:
            existing = self.repository.get_by_name(payload.name)
            if existing is not None and existing.id != matrix.id:
                raise ConflictError(
                    f"A payoff matrix named {payload.name!r} already exists"
                )
            matrix.name = payload.name

        if payload.description is not None:
            matrix.description = payload.description

        for cell_name in ("cc", "cd", "dc", "dd"):
            cell = getattr(payload, cell_name)
            if cell is not None:
                setattr(matrix, f"{cell_name}_player_a", cell.player_a_payoff)
                setattr(matrix, f"{cell_name}_player_b", cell.player_b_payoff)

        if payload.is_default is not None:
            matrix.is_default = payload.is_default
            if payload.is_default:
                self.repository.clear_default(except_id=matrix.id)

        self.db.commit()
        self.db.refresh(matrix)
        return PayoffMatrixResponse.from_model(matrix)

    def delete(self, matrix_id: uuid.UUID) -> None:
        """Delete a matrix.

        The default matrix cannot be deleted, and neither can one that a
        tournament or experiment still references: those records would lose
        the payoffs their results were computed with.
        """
        matrix = self.get_model(matrix_id)
        if matrix.is_default:
            raise ConflictError(
                "The default payoff matrix cannot be deleted. Make another "
                "matrix the default first."
            )

        from app.models.experiment import Experiment  # local import avoids a cycle
        from app.models.tournament import Tournament

        for model, label in ((Tournament, "tournament"), (Experiment, "experiment")):
            in_use = (
                self.db.query(model).filter(model.payoff_matrix_id == matrix.id).first()
            )
            if in_use is not None:
                raise ConflictError(
                    f"This payoff matrix is used by at least one {label} and "
                    "cannot be deleted."
                )

        self.repository.delete(matrix)
        self.db.commit()

    def ensure_default_exists(self) -> PayoffMatrix:
        """Create the classic matrix as the default if nothing is configured."""
        existing = self.repository.get_default()
        if existing is not None:
            return existing

        classic = DomainPayoffMatrix.classic()
        matrix = PayoffMatrix(
            name=DEFAULT_MATRIX_NAME,
            description=(
                "The classic Prisoner's Dilemma payoff matrix with T=5, R=3, "
                "P=1, S=0."
            ),
            is_default=True,
        )
        matrix.apply_domain(classic)
        self.repository.add(matrix)
        self.db.commit()
        self.db.refresh(matrix)
        return matrix
