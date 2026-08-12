"""Check a database connection string before deploying with it.

A wrong DATABASE_URL costs a full deploy cycle to discover on a hosting
platform. This tries the connection locally and says plainly what is wrong.

Usage:

    python scripts/check_db_url.py "postgresql+psycopg://user:pass@host/db?sslmode=require"

or, to keep the string out of your shell history:

    python scripts/check_db_url.py            # prompts, input hidden

The password is never printed back.
"""

from __future__ import annotations

import getpass
import sys
from urllib.parse import urlsplit


def mask(url: str) -> str:
    """The URL with the password replaced, safe to show or paste in chat."""
    parts = urlsplit(url)
    if parts.password:
        return url.replace(parts.password, "*" * 8, 1)
    return url


def inspect(url: str) -> list[str]:
    """Static problems, found without touching the network."""
    problems: list[str] = []

    if url != "".join(url.split()):
        problems.append(
            "Contains whitespace. A URL cannot hold a raw space — one stray "
            "space makes the username read as ' user' and authentication fails."
        )

    stripped = "".join(url.split())
    parts = urlsplit(stripped)

    if parts.scheme == "postgresql":
        problems.append(
            "Scheme is 'postgresql://', which selects psycopg2. This project "
            "uses psycopg 3 — change it to 'postgresql+psycopg://'."
        )
    elif parts.scheme != "postgresql+psycopg":
        problems.append(
            f"Scheme is '{parts.scheme}://'. Expected 'postgresql+psycopg://'."
        )

    if not parts.username:
        problems.append("No username found before the ':'.")
    if not parts.password:
        problems.append("No password found between ':' and '@'.")
    if not parts.hostname:
        problems.append("No host found after the '@'.")
    if not parts.path.strip("/"):
        problems.append("No database name found after the host.")

    # Characters that silently truncate or split a URL if not percent-encoded.
    if parts.password:
        for character in "#?/@":
            if character in parts.password:
                problems.append(
                    f"The password contains '{character}', which has a special "
                    "meaning in a URL and must be percent-encoded. Reset the "
                    "password to one without it, which is far simpler."
                )
                break

    if parts.hostname and "neon.tech" in parts.hostname and "sslmode" not in stripped:
        problems.append("Neon requires SSL. Add '?sslmode=require' to the end.")

    return problems


def main() -> int:
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = getpass.getpass("Paste the connection string (hidden): ")

    if not url.strip():
        print("Nothing to check.")
        return 2

    print()
    print("Checking:", mask("".join(url.split())))
    print()

    problems = inspect(url)
    if problems:
        print("Problems found in the string itself:")
        for problem in problems:
            print("  -", problem)
        print()

    # Try it for real, using the cleaned form the application would use.
    cleaned = "".join(url.split())
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        print("SQLAlchemy is not installed here; only the static checks ran.")
        return 1 if problems else 0

    try:
        engine = create_engine(cleaned, connect_args={"connect_timeout": 15})
        with engine.connect() as connection:
            version = connection.execute(text("show server_version")).scalar()
            database = connection.execute(text("select current_database()")).scalar()
            user = connection.execute(text("select current_user")).scalar()
    except Exception as exc:  # noqa: BLE001 - the message is the whole point
        message = str(exc)
        print("CONNECTION FAILED")
        print()
        if "password authentication failed" in message:
            print("  The host answered, so the address is right — the password is not.")
            print("  Reset the password in the Neon dashboard and copy the whole")
            print("  connection string again, with the password visible.")
        elif "could not translate host name" in message:
            print("  The host name could not be resolved. Check it for typos.")
        elif "timeout" in message.lower():
            print("  The host did not answer in time. Check the host and port.")
        else:
            print(" ", message.splitlines()[0][:200])
        return 1

    print("CONNECTED")
    print("  server  :", version)
    print("  database:", database)
    print("  user    :", user)
    print()
    print("This string is good. Paste it into Render as DATABASE_URL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
