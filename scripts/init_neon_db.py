#!/usr/bin/env python3
"""Apply Postgres schema and verify Neon connectivity."""

from app.config import config
from app.db import postgres as pg


def main() -> None:
    database_url = (config.app.get("database_url") or "").strip()
    if not database_url:
        raise SystemExit("DATABASE_URL or config app.database_url is required")

    pg.ensure_schema(database_url)
    pg.set_setting("_schema_version", {"version": 1}, database_url)
    settings = pg.list_settings(database_url)
    print(f"postgres ready ({len(settings)} setting(s) in app_settings)")


if __name__ == "__main__":
    main()
