"""Guards that stop a public deployment running on published defaults.

The default signing key and admin password are both visible in this
repository, so a reachable deployment that still used them would be open to
anyone who read the source.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.core.config import DEFAULT_SECRET_KEY, Settings
from app.database.seed import DEFAULT_ADMIN_PASSWORD, InsecureSeedError, seed_admin


def _settings(**overrides) -> Settings:
    """Settings built from explicit values, ignoring any local .env file."""
    base = {
        "_env_file": None,
        "ENVIRONMENT": "production",
        "SECRET_KEY": "a-properly-random-production-key",
        "CORS_ORIGINS": "https://example.vercel.app",
    }
    base.update(overrides)
    return Settings(**base)


class TestStartupGuard:
    def test_development_tolerates_the_defaults(self) -> None:
        _settings(ENVIRONMENT="development", SECRET_KEY=DEFAULT_SECRET_KEY).assert_production_ready()

    def test_production_refuses_the_default_secret_key(self) -> None:
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            _settings(SECRET_KEY=DEFAULT_SECRET_KEY).assert_production_ready()

    def test_production_refuses_empty_cors(self) -> None:
        with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
            _settings(CORS_ORIGINS="").assert_production_ready()

    def test_production_accepts_a_configured_deployment(self) -> None:
        _settings().assert_production_ready()

    def test_every_problem_is_reported_at_once(self) -> None:
        """One restart should reveal everything that is wrong, not just the first."""
        with pytest.raises(RuntimeError) as caught:
            _settings(SECRET_KEY=DEFAULT_SECRET_KEY, CORS_ORIGINS="").assert_production_ready()
        message = str(caught.value)
        assert "SECRET_KEY" in message
        assert "CORS_ORIGINS" in message


class TestSeedGuard:
    def test_refuses_the_default_admin_password_in_production(
        self, db: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("app.database.seed.settings", _settings(), raising=False)
        monkeypatch.setattr(
            "app.database.seed.settings.FIRST_ADMIN_PASSWORD",
            DEFAULT_ADMIN_PASSWORD,
            raising=False,
        )
        with pytest.raises(InsecureSeedError, match="FIRST_ADMIN_PASSWORD"):
            seed_admin(db)

    def test_allows_a_real_password_in_production(
        self, db: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "app.database.seed.settings",
            _settings(FIRST_ADMIN_PASSWORD="a-real-chosen-password"),
            raising=False,
        )
        admin = seed_admin(db)
        assert admin is not None
        assert admin.role.value == "ADMIN"

    def test_development_still_seeds_with_the_default(self, db: Session) -> None:
        """Local setup must stay a one-command affair."""
        admin = seed_admin(db)
        assert admin is not None
