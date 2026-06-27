import os
from contextlib import contextmanager
from typing import Iterator, List, Optional

from loguru import logger

from app.config import config
from app.models.schema import MaterialInfo, VideoAspect
from app.services.material import get_api_key

DEFAULT_HIGGSFIELD_MODEL = "/jobs/v2/kling3_0_turbo"


def _aspect_ratio(video_aspect: VideoAspect) -> str:
    aspect = VideoAspect(video_aspect)
    if aspect == VideoAspect.portrait:
        return "9:16"
    return "16:9"


def _clip_duration(minimum_duration: int) -> int:
    configured = config.app.get("higgsfield_video_duration", 5)
    try:
        configured = int(configured)
    except (TypeError, ValueError):
        configured = 5
    return max(minimum_duration, configured, 3)


def _model_path() -> str:
    model = str(config.app.get("higgsfield_model", DEFAULT_HIGGSFIELD_MODEL)).strip()
    return model or DEFAULT_HIGGSFIELD_MODEL


@contextmanager
def _higgsfield_credentials(api_key: str) -> Iterator[None]:
    previous = {
        "HF_KEY": os.environ.get("HF_KEY"),
        "HF_API_KEY": os.environ.get("HF_API_KEY"),
        "HF_API_SECRET": os.environ.get("HF_API_SECRET"),
    }
    if ":" in api_key:
        key_id, key_secret = api_key.split(":", 1)
        os.environ["HF_API_KEY"] = key_id
        os.environ["HF_API_SECRET"] = key_secret
        os.environ.pop("HF_KEY", None)
    else:
        os.environ["HF_KEY"] = api_key
        os.environ.pop("HF_API_KEY", None)
        os.environ.pop("HF_API_SECRET", None)
    try:
        yield
    finally:
        for env_name, value in previous.items():
            if value is None:
                os.environ.pop(env_name, None)
            else:
                os.environ[env_name] = value


def _extract_video_url(result: object) -> str:
    if not isinstance(result, dict):
        return ""

    direct_keys = ("rawUrl", "url", "video_url")
    for key in direct_keys:
        value = result.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value

    for collection_key in ("videos", "video", "results", "images"):
        collection = result.get(collection_key)
        if isinstance(collection, list) and collection:
            first = collection[0]
            if isinstance(first, str) and first.startswith("http"):
                return first
            if isinstance(first, dict):
                nested = _extract_video_url(first)
                if nested:
                    return nested
        elif isinstance(collection, dict):
            nested = _extract_video_url(collection)
            if nested:
                return nested

    return ""


def _extract_duration(result: object, fallback: int) -> int:
    if not isinstance(result, dict):
        return fallback

    for key in ("durationSec", "duration", "duration_sec"):
        value = result.get(key)
        if isinstance(value, (int, float)) and value > 0:
            return int(value)

    videos = result.get("videos")
    if isinstance(videos, list) and videos and isinstance(videos[0], dict):
        value = videos[0].get("duration")
        if isinstance(value, (int, float)) and value > 0:
            return int(value)

    return fallback


def generate_higgsfield_clip(
    prompt: str,
    video_aspect: VideoAspect = VideoAspect.portrait,
    minimum_duration: int = 5,
) -> Optional[MaterialInfo]:
    prompt = (prompt or "").strip()
    if not prompt:
        return None

    try:
        import higgsfield_client
    except ImportError:
        logger.error(
            "higgsfield-client is not installed. Run: pip install higgsfield-client"
        )
        return None

    api_key = get_api_key("higgsfield_api_keys")
    duration = _clip_duration(minimum_duration)
    arguments = {
        "prompt": prompt,
        "aspect_ratio": _aspect_ratio(video_aspect),
        "duration": duration,
    }

    logger.info(
        f"generating higgsfield video: model={_model_path()}, prompt={prompt}, duration={duration}"
    )

    try:
        with _higgsfield_credentials(api_key):
            result = higgsfield_client.subscribe(_model_path(), arguments=arguments)
    except Exception as exc:
        logger.error(f"higgsfield video generation failed: {exc}")
        return None

    video_url = _extract_video_url(result)
    if not video_url:
        logger.error(f"higgsfield response missing video url: {result}")
        return None

    item = MaterialInfo()
    item.provider = "higgsfield"
    item.url = video_url
    item.duration = _extract_duration(result, duration)
    logger.success(f"higgsfield video generated: {video_url}")
    return item


def search_videos_higgsfield(
    search_term: str,
    minimum_duration: int,
    video_aspect: VideoAspect = VideoAspect.portrait,
) -> List[MaterialInfo]:
    clip = generate_higgsfield_clip(
        prompt=search_term,
        video_aspect=video_aspect,
        minimum_duration=minimum_duration,
    )
    return [clip] if clip else []
