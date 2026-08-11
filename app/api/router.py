"""Aggregates every versioned route module."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    auth,
    experiments,
    game_theory,
    matches,
    payoff_matrices,
    strategies,
    surveys,
    tournaments,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(game_theory.router)
api_router.include_router(payoff_matrices.router)
api_router.include_router(strategies.router)
api_router.include_router(matches.router)
api_router.include_router(tournaments.router)
api_router.include_router(experiments.router)
api_router.include_router(surveys.router)
