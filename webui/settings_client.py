from __future__ import annotations

import os
from typing import Any, Callable

import requests
from loguru import logger

from app.config import config
from app.db import postgres as pg
from app.models import const

WEBUI_PREFS_KEY = "webui_prefs"


def is_settings_sync_enabled() -> bool:
    return pg.is_postgres_enabled() or bool(get_api_base_url())


def get_api_base_url() -> str:
    return (
        os.getenv(
            "MPT_WEBUI_API_BASE_URL",
            config.app.get(
                "webui_api_base_url",
                f"http://127.0.0.1:{config.listen_port}",
            ),
        )
        .strip()
        .rstrip("/")
    )


def _unwrap_api_payload(response: requests.Response) -> Any:
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def get_setting(key: str) -> Any | None:
    if pg.is_postgres_enabled():
        return pg.get_setting(key)

    base_url = get_api_base_url()
    if not base_url:
        return None

    try:
        data = _unwrap_api_payload(
            requests.get(f"{base_url}/api/v1/settings/{key}", timeout=10)
        )
        if isinstance(data, dict):
            return data.get("value")
        return data
    except Exception as exc:
        logger.warning(f"failed to load setting {key} via API: {exc}")
        return None


def set_setting(key: str, value: Any) -> bool:
    if pg.is_postgres_enabled():
        pg.set_setting(key, value)
        return True

    base_url = get_api_base_url()
    if not base_url:
        return False

    try:
        requests.put(
            f"{base_url}/api/v1/settings/{key}",
            json={"value": value},
            timeout=10,
        ).raise_for_status()
        return True
    except Exception as exc:
        logger.warning(f"failed to save setting {key} via API: {exc}")
        return False


def load_webui_prefs() -> dict[str, Any]:
    prefs = get_setting(WEBUI_PREFS_KEY)
    return prefs if isinstance(prefs, dict) else {}


def collect_webui_prefs(
    ui_language: str,
    hide_config: bool,
    hide_log: bool,
    match_materials_to_script: bool,
) -> dict[str, Any]:
    return {
        "ui_language": ui_language,
        "hide_config": hide_config,
        "hide_log": hide_log,
        "match_materials_to_script": match_materials_to_script,
    }


def apply_webui_prefs(prefs: dict[str, Any]) -> None:
    if not prefs:
        return

    if prefs.get("ui_language"):
        config.ui["language"] = prefs["ui_language"]
    if "hide_config" in prefs:
        config.app["hide_config"] = bool(prefs["hide_config"])
    if "hide_log" in prefs:
        config.ui["hide_log"] = bool(prefs["hide_log"])
    if "match_materials_to_script" in prefs:
        config.app["match_materials_to_script"] = bool(
            prefs["match_materials_to_script"]
        )


def sync_webui_prefs(
    ui_language: str,
    hide_config: bool,
    hide_log: bool,
    match_materials_to_script: bool,
) -> bool:
    if not is_settings_sync_enabled():
        return False

    prefs = collect_webui_prefs(
        ui_language=ui_language,
        hide_config=hide_config,
        hide_log=hide_log,
        match_materials_to_script=match_materials_to_script,
    )
    return set_setting(WEBUI_PREFS_KEY, prefs)


def fetch_recent_tasks(page: int = 1, page_size: int = 10) -> tuple[list[dict], int]:
    if pg.is_postgres_enabled():
        from app.services import state as sm

        return sm.state.get_all_tasks(page, page_size)

    base_url = get_api_base_url()
    if not base_url:
        return [], 0

    try:
        data = _unwrap_api_payload(
            requests.get(
                f"{base_url}/api/v1/tasks",
                params={"page": page, "page_size": page_size},
                timeout=10,
            )
        )
        if isinstance(data, dict):
            tasks = data.get("tasks", [])
            total = int(data.get("total", len(tasks)))
            return tasks if isinstance(tasks, list) else [], total
    except Exception as exc:
        logger.warning(f"failed to fetch task history via API: {exc}")

    return [], 0


def task_state_label(state: int, tr: Callable[[str], str]) -> str:
    if state == const.TASK_STATE_COMPLETE:
        return tr("Task Complete")
    if state == const.TASK_STATE_FAILED:
        return tr("Task Failed")
    return tr("Task Processing")
