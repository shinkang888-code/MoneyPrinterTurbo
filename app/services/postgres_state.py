import copy
import threading

from app.db import postgres as pg
from app.models import const
from app.services.base_state import BaseState


def flatten_task_row(row: dict) -> dict:
    extra = pg.from_jsonb(row.get("extra"))
    if not isinstance(extra, dict):
        extra = {}
    return {
        "task_id": row["task_id"],
        "state": row["state"],
        "progress": row["progress"],
        **extra,
    }


class PostgresState(BaseState):
    def __init__(self, conninfo: str):
        self._conninfo = conninfo.strip()
        self._lock = threading.RLock()
        pg.ensure_schema(self._conninfo)

    def _connect(self):
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self._conninfo, row_factory=dict_row)

    def get_all_tasks(self, page: int, page_size: int):
        offset = (page - 1) * page_size

        with self._lock:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) AS total FROM video_tasks")
                    total = int(cur.fetchone()["total"])

                    cur.execute(
                        """
                        SELECT task_id, state, progress, extra
                        FROM video_tasks
                        ORDER BY updated_at DESC
                        LIMIT %s OFFSET %s
                        """,
                        (page_size, offset),
                    )
                    rows = cur.fetchall()

        tasks = [copy.deepcopy(flatten_task_row(row)) for row in rows]
        return tasks, total

    def update_task(
        self,
        task_id: str,
        state: int = const.TASK_STATE_PROCESSING,
        progress: int = 0,
        **kwargs,
    ):
        progress = int(progress)
        if progress > 100:
            progress = 100

        extra_payload = pg.to_jsonb(kwargs)

        with self._lock:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO video_tasks (
                            task_id, state, progress, extra, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s::jsonb, NOW(), NOW())
                        ON CONFLICT (task_id) DO UPDATE
                        SET state = EXCLUDED.state,
                            progress = EXCLUDED.progress,
                            extra = EXCLUDED.extra,
                            updated_at = NOW()
                        """,
                        (task_id, state, progress, extra_payload),
                    )
                conn.commit()

    def get_task(self, task_id: str):
        with self._lock:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT task_id, state, progress, extra
                        FROM video_tasks
                        WHERE task_id = %s
                        """,
                        (task_id,),
                    )
                    row = cur.fetchone()

        if not row:
            return None
        return copy.deepcopy(flatten_task_row(row))

    def delete_task(self, task_id: str):
        with self._lock:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM video_tasks WHERE task_id = %s",
                        (task_id,),
                    )
                conn.commit()
