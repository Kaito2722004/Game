"""Database seeding.

Creates the default payoff matrix, the strategy catalogue rows and a first
admin account. Safe to run repeatedly: existing rows are updated, not
duplicated.

    python -m app.database.seed
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.game_theory.payoff import PayoffMatrix as DomainPayoffMatrix
from app.models.payoff_matrix import PayoffMatrix
from app.models.strategy import Strategy
from app.models.user import User, UserRole
from app.strategies.registry import strategy_registry

logger = logging.getLogger(__name__)

DEFAULT_MATRIX_NAME = "Classic Prisoner's Dilemma"


def seed_payoff_matrices(db: Session) -> PayoffMatrix:
    """Insert or refresh the classic matrix and mark it as the default."""
    matrix = db.execute(
        select(PayoffMatrix).where(PayoffMatrix.name == DEFAULT_MATRIX_NAME)
    ).scalar_one_or_none()

    if matrix is None:
        matrix = PayoffMatrix(
            name=DEFAULT_MATRIX_NAME,
            description=(
                "The classic Prisoner's Dilemma payoff matrix: T=5, R=3, P=1, "
                "S=0. Satisfies T > R > P > S and R > (S + T) / 2."
            ),
            is_default=True,
        )
        db.add(matrix)

    matrix.apply_domain(DomainPayoffMatrix.classic())
    matrix.is_default = True

    # Exactly one matrix may be the default.
    for other in db.execute(
        select(PayoffMatrix).where(PayoffMatrix.name != DEFAULT_MATRIX_NAME)
    ).scalars():
        other.is_default = False

    db.flush()
    return matrix


def seed_strategies(db: Session) -> list[Strategy]:
    """Mirror the code registry into the strategy catalogue table."""
    rows: list[Strategy] = []
    for metadata in strategy_registry.all_metadata():
        row = db.execute(
            select(Strategy).where(Strategy.code == metadata.id)
        ).scalar_one_or_none()
        if row is None:
            row = Strategy(code=metadata.id)
            db.add(row)

        row.name = metadata.name
        row.description = metadata.description
        row.rules = list(metadata.rules)
        row.category = metadata.category
        row.is_deterministic = metadata.is_deterministic
        row.is_active = True
        rows.append(row)

    db.flush()
    return rows


DEFAULT_ADMIN_PASSWORD = "admin12345"


class InsecureSeedError(RuntimeError):
    """Raised when seeding would create a publicly guessable admin account."""


def seed_admin(db: Session) -> User | None:
    """Create the first admin account if it does not already exist.

    The credentials come from FIRST_ADMIN_EMAIL / FIRST_ADMIN_PASSWORD. An
    existing account is never modified, so a changed password is not reset by
    re-running the seed.

    In production the built-in default password is refused outright. It is
    published in this repository, so seeding a reachable deployment with it
    would hand anyone who reads the source a full administrator account.
    """
    if settings.is_production and settings.FIRST_ADMIN_PASSWORD == DEFAULT_ADMIN_PASSWORD:
        raise InsecureSeedError(
            "FIRST_ADMIN_PASSWORD is still the built-in default, which is public "
            "in the source. Set a real password in the environment before "
            "seeding a production deployment."
        )

    email = settings.FIRST_ADMIN_EMAIL.strip().lower()
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing is not None:
        return existing

    admin = User(
        email=email,
        full_name="Administrator",
        hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.flush()
    return admin


def seed_all(db: Session) -> dict[str, int | str]:
    """Run every seeder in one transaction."""
    matrix = seed_payoff_matrices(db)
    strategies = seed_strategies(db)
    admin = seed_admin(db)
    db.commit()
    return {
        "default_matrix": matrix.name,
        "strategies": len(strategies),
        "admin_email": admin.email if admin else "",
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    with SessionLocal() as db:
        summary = seed_all(db)

    logger.info("Seed complete.")
    logger.info("  default payoff matrix : %s", summary["default_matrix"])
    logger.info("  strategies registered : %s", summary["strategies"])
    logger.info("  admin account         : %s", summary["admin_email"])
    if settings.FIRST_ADMIN_PASSWORD == DEFAULT_ADMIN_PASSWORD:
        logger.warning(
            "  the admin password is the built-in default; change "
            "FIRST_ADMIN_PASSWORD before deploying"
        )


if __name__ == "__main__":
    main()
