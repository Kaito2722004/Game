"""Check a database connection string before deploying with it.

A wrong DATABASE_URL costs a full deploy cycle to discover on a hosting
platform. This tries the connection locally and says plainly what is wrong.

Usage:

    python scripts/check_db_url.py "postgresql+psycopg://user:pass@host/db?sslmode=require"

or run it with no argument and paste when prompted:

    python scripts/check_db_url.py

The prompt echoes what you paste. A hidden prompt sounds safer, but several
Windows terminals refuse a Ctrl+V into one and give no sign that nothing
arrived, which is a worse failure than showing the string on your own screen.
The password is masked in everything the script prints afterwards.
"""

from __future__ import annotations

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
        print("Paste the connection string and press Enter.")
        print("(Right-click pastes in PowerShell if Ctrl+V does nothing.)")
        try:
            url = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            print("Cancelled.")
            return 2

    url = url.strip().strip('"').strip("'")

    if not url:
        print()
        print("Nothing was captured — the paste did not arrive.")
        print("Try passing it as an argument instead:")
        print('  python scripts/check_db_url.py "postgresql+psycopg://..."')
        return 2

    if "://" not in url or "@" not in url:
        print()
        print("That does not look like a connection string.")
        print("Only part of it seems to have arrived:", len(url), "characters.")
        print("A Neon URL is usually 100-150 characters and looks like:")
        print("  postgresql+psycopg://user:password@ep-xxx.neon.tech/neondb?sslmode=require")
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
