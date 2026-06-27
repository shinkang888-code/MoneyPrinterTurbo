from typing import Callable, List, Optional

from app.config import config

STOCK_SOURCES: List[str] = ["pexels", "pixabay", "coverr", "higgsfield"]
SOURCE_CONFIG_KEYS = {
    "pexels": "pexels_api_keys",
    "pixabay": "pixabay_api_keys",
    "coverr": "coverr_api_keys",
    "higgsfield": "higgsfield_api_keys",
}


def _normalize_api_keys(raw_value) -> List[str]:
    if not raw_value:
        return []
    if isinstance(raw_value, str):
        raw_value = raw_value.replace(" ", "")
        return [raw_value] if raw_value else []
    return [str(item).strip() for item in raw_value if str(item).strip()]


def has_source_api_key(app_config: dict, source: str) -> bool:
    cfg_key = SOURCE_CONFIG_KEYS.get(source)
    if not cfg_key:
        return False
    return bool(_normalize_api_keys(app_config.get(cfg_key)))


def get_configured_stock_sources(app_config: Optional[dict] = None) -> List[str]:
    app_config = app_config or config.app
    return [
        source
        for source in STOCK_SOURCES
        if has_source_api_key(app_config, source)
    ]


def resolve_video_source(source: str, app_config: Optional[dict] = None) -> str:
    if source != "auto":
        return source

    configured = get_configured_stock_sources(app_config)
    if configured:
        return configured[0]
    return "pexels"


def get_sources_for_download(source: str, app_config: Optional[dict] = None) -> List[str]:
    app_config = app_config or config.app
    if source == "local":
        return ["local"]
    if source != "auto":
        return [source]
    configured = get_configured_stock_sources(app_config)
    return configured or ["pexels"]


def format_source_labels(
    sources: List[str], label_fn: Callable[[str], str]
) -> str:
    return ", ".join(label_fn(source) for source in sources)
