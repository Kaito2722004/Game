"""Payoff matrix CRUD endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.dependencies import AdminUser, DbSession, PaginationParams, TeacherUser
from app.schemas.common import ERROR_RESPONSES, APIResponse, success
from app.schemas.payoff_matrix import (
    PayoffMatrixCreate,
    PayoffMatrixResponse,
    PayoffMatrixUpdate,
)
from app.services.payoff_matrix_service import PayoffMatrixService

router = APIRouter(prefix="/payoff-matrices", tags=["Payoff Matrices"])


@router.get(
    "",
    response_model=APIResponse[list[PayoffMatrixResponse]],
    summary="List stored payoff matrices",
)
def list_matrices(
    db: DbSession, pagination: PaginationParams
) -> APIResponse[list[PayoffMatrixResponse]]:
    return success(
        PayoffMatrixService(db).list(limit=pagination.limit, offset=pagination.offset)
    )


@router.get(
    "/{matrix_id}",
    response_model=APIResponse[PayoffMatrixResponse],
    responses=ERROR_RESPONSES,
    summary="Get one payoff matrix",
)
def get_matrix(matrix_id: uuid.UUID, db: DbSession) -> APIResponse[PayoffMatrixResponse]:
    return success(PayoffMatrixService(db).get(matrix_id))


@router.post(
    "",
    response_model=APIResponse[PayoffMatrixResponse],
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
    summary="Create a payoff matrix",
    description=(
        "Requires a TEACHER or ADMIN account. Any 2x2 matrix may be stored; "
        "it does not have to be a Prisoner's Dilemma."
    ),
)
def create_matrix(
    payload: PayoffMatrixCreate, db: DbSession, actor: TeacherUser
) -> APIResponse[PayoffMatrixResponse]:
    return success(PayoffMatrixService(db).create(payload, actor), "Payoff matrix created")


@router.put(
    "/{matrix_id}",
    response_model=APIResponse[PayoffMatrixResponse],
    responses=ERROR_RESPONSES,
    summary="Update a payoff matrix",
    description="Requires an ADMIN account, since stored matrices are global.",
)
def update_matrix(
    matrix_id: uuid.UUID,
    payload: PayoffMatrixUpdate,
    db: DbSession,
    actor: AdminUser,
) -> APIResponse[PayoffMatrixResponse]:
    return success(PayoffMatrixService(db).update(matrix_id, payload), "Payoff matrix updated")


@router.delete(
    "/{matrix_id}",
    response_model=APIResponse[None],
    responses=ERROR_RESPONSES,
    summary="Delete a payoff matrix",
    description=(
        "Requires an ADMIN account. The default matrix cannot be deleted, and "
        "neither can a matrix still referenced by a tournament or experiment."
    ),
)
def delete_matrix(
    matrix_id: uuid.UUID, db: DbSession, actor: AdminUser
) -> APIResponse[None]:
    PayoffMatrixService(db).delete(matrix_id)
    return success(None, "Payoff matrix deleted")
