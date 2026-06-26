import json
import os
import threading
from pathlib import Path
from typing import Any

from loguru import logger

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")
_schema_lock = threading.Lock()
_schema_initialized = False


def is_postgres_enabled() -> bool:
    from app.config import config

    return bool(config.app.get("enable_postgres")) and bool(
        (config.app.get("database_url") or "").strip()
    )


def get_database_url() -> str:
    from app.config import config

    return (config.app.get("database_url") or "").strip()


def ensure_schema(conninfo: str | None = None) -> None:
    global _schema_initialized

    url = (conninfo or get_database_url()).strip()
    if not url:
        raise ValueError("database_url is not configured")

    with _schema_lock:
        if _schema_initialized:
            return

        import psycopg

        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()

        _schema_initialized = True
        logger.info("postgres schema initialized")


def json_default(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return str(value)


def to_jsonb(value: Any) -> str:
    return json.dumps(value, default=json_default, ensure_ascii=False)


def from_jsonb(value: Any) -> Any:
    if value is None:
        return {}
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return value


def get_setting(key: str, conninfo: str | None = None) -> Any | None:
    import psycopg
    from psycopg.rows import dict_row

    url = (conninfo or get_database_url()).strip()
    ensure_schema(url)

    with psycopg.connect(url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT value FROM app_settings WHERE key = %s",
                (key,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return from_jsonb(row["value"])


def set_setting(key: str, value: Any, conninfo: str | None = None) -> None:
    import psycopg

    url = (conninfo or get_database_url()).strip()
    ensure_schema(url)
    payload = to_jsonb(value)

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value,
                    updated_at = NOW()
                """,
                (key, payload),
            )
        conn.commit()


def list_settings(conninfo: str | None = None) -> dict[str, Any]:
    import psycopg
    from psycopg.rows import dict_row

    url = (conninfo or get_database_url()).strip()
    ensure_schema(url)

    with psycopg.connect(url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM app_settings ORDER BY key")
            rows = cur.fetchall()

    return {row["key"]: from_jsonb(row["value"]) for row in rows}
