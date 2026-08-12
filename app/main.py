"""FastAPI application factory and entry point.

Run with:  uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.schemas.common import APIResponse, success

DESCRIPTION = """
Backend for the **Prisoner's Dilemma Strategy Tournament** university project.

It provides three things:

* **A game-theory analysis engine.** Give it any 2x2 payoff matrix and it
  computes whether the matrix is a Prisoner's Dilemma, the values of T, R, P
  and S, each player's dominant action, every pure-strategy Nash equilibrium,
  and the Pareto classification of each outcome. None of these results are
  hard-coded.
* **An Axelrod-style simulation engine.** Iterated matches between strategies,
  and round-robin tournaments with configurable strategies, rounds, payoff
  matrix, repetitions, random seed and continuation probability. Rankings come
  from the simulation, never from an assumption about which strategy should
  win.
* **A human classroom experiment module.** Participants, random pairing, round
  recording with backend-computed payoffs, cooperation statistics, and an
  optional short trust survey.

Every response uses the same envelope:
`{"success": true, "data": ..., "message": null}`.

Academic note: this project follows Philip D. Straffin, *Game Theory and
Strategy*. The software demonstrates the theory computationally; it does not
assert that any particular strategy is always best.
"""


def create_app() -> FastAPI:
    """Build and configure the application."""
    # Fails fast rather than serving a deployment anyone could sign into.
    settings.assert_production_ready()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=DESCRIPTION,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={"name": "Prisoner's Dilemma Strategy Tournament"},
        license_info={"name": "MIT"},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["Meta"], summary="API root")
    def root() -> APIResponse[dict]:
        return success(
            {
                "name": settings.PROJECT_NAME,
                "version": "1.0.0",
                "docs": "/docs",
                "openapi": "/openapi.json",
                "api_base": settings.API_V1_PREFIX,
            }
        )

    @app.get("/health", tags=["Meta"], summary="Liveness probe")
    def health() -> APIResponse[dict]:
        return success({"status": "ok", "environment": settings.ENVIRONMENT})

    return app


app = create_app()
