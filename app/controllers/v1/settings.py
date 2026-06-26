from typing import Any

from fastapi import Request

from app.controllers import base
from app.controllers.v1.base import new_router
from app.db import postgres as pg
from app.models.exception import HttpException
from app.models.schema import SettingResponse, SettingsListResponse, SettingUpsertRequest
from app.utils import utils

router = new_router()


def _require_postgres(request_id: str) -> None:
    if not pg.is_postgres_enabled():
        raise HttpException(
            task_id=request_id,
            status_code=503,
            message=f"{request_id}: postgres is not enabled",
        )


@router.get(
    "/settings",
    response_model=SettingsListResponse,
    summary="List persisted app settings",
)
def list_settings(request: Request):
    request_id = base.get_task_id(request)
    _require_postgres(request_id)
    return utils.get_response(200, {"settings": pg.list_settings()})


@router.get(
    "/settings/{key}",
    response_model=SettingResponse,
    summary="Get a persisted app setting",
)
def get_setting(request: Request, key: str):
    request_id = base.get_task_id(request)
    _require_postgres(request_id)
    value = pg.get_setting(key)
    if value is None:
        raise HttpException(
            task_id=request_id,
            status_code=404,
            message=f"{request_id}: setting not found",
        )
    return utils.get_response(200, {"key": key, "value": value})


@router.put(
    "/settings/{key}",
    response_model=SettingResponse,
    summary="Create or update a persisted app setting",
)
def upsert_setting(request: Request, key: str, body: SettingUpsertRequest):
    request_id = base.get_task_id(request)
    _require_postgres(request_id)
    pg.set_setting(key, body.value)
    return utils.get_response(200, {"key": key, "value": body.value})
