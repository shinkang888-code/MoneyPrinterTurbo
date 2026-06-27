from typing import Callable, List, Tuple

import streamlit as st

from app.services import video_source as vs

VIDEO_SOURCE_IDS = ["auto", "pexels", "pixabay", "coverr", "local"]

SOURCE_I18N_KEYS = {
    "auto": "Auto Mode",
    "pexels": "Pexels",
    "pixabay": "Pixabay",
    "coverr": "Coverr",
    "local": "Local file",
}


def _label_for_source(source_id: str, tr: Callable[[str], str]) -> str:
    return tr(SOURCE_I18N_KEYS[source_id])


def _get_keys_from_config(app_config: dict, cfg_key: str) -> str:
    api_keys = app_config.get(cfg_key, [])
    if isinstance(api_keys, str):
        api_keys = [api_keys]
    return ", ".join(api_keys)


def _save_keys_to_config(app_config: dict, cfg_key: str, value: str) -> None:
    value = value.replace(" ", "")
    if value:
        app_config[cfg_key] = value.split(",")
    else:
        app_config[cfg_key] = []


def render_video_source_toggle(
    tr: Callable[[str], str],
    app_config: dict,
) -> str:
    labels = [_label_for_source(source_id, tr) for source_id in VIDEO_SOURCE_IDS]
    label_to_id = {
        _label_for_source(source_id, tr): source_id for source_id in VIDEO_SOURCE_IDS
    }

    saved_source = app_config.get("video_source", "auto")
    if saved_source not in VIDEO_SOURCE_IDS:
        saved_source = "auto"

    default_label = _label_for_source(saved_source, tr)

    selected_label = st.segmented_control(
        tr("Video Source"),
        options=labels,
        default=default_label,
        key="video_source_segment",
    )
    selected_source = label_to_id[selected_label]
    app_config["video_source"] = selected_source
    return selected_source


def render_source_api_key_fields(
    tr: Callable[[str], str],
    app_config: dict,
    selected_source: str,
) -> None:
    if selected_source == "auto":
        configured = vs.get_configured_stock_sources(app_config)
        if configured:
            source_names = vs.format_source_labels(
                configured,
                lambda source_id: _label_for_source(source_id, tr),
            )
            st.caption(tr("Auto Mode Active Sources").format(sources=source_names))
        else:
            st.warning(tr("Auto Mode No API Keys"))
        st.caption(tr("Auto Mode Help"))
        _render_all_stock_api_keys(tr, app_config)
        return

    if selected_source == "local":
        st.caption(tr("Local Video Source Help"))
        return

    cfg_key = vs.SOURCE_CONFIG_KEYS.get(selected_source)
    if not cfg_key:
        return

    api_key = st.text_input(
        tr(f"{SOURCE_I18N_KEYS[selected_source]} API Key"),
        value=_get_keys_from_config(app_config, cfg_key),
        type="password",
        key=f"video_source_api_key_{selected_source}",
    )
    _save_keys_to_config(app_config, cfg_key, api_key)


def _render_all_stock_api_keys(tr: Callable[[str], str], app_config: dict) -> None:
    with st.expander(tr("Video Source API Keys"), expanded=not vs.get_configured_stock_sources(app_config)):
        for source_id in vs.STOCK_SOURCES:
            cfg_key = vs.SOURCE_CONFIG_KEYS[source_id]
            api_key = st.text_input(
                tr(f"{SOURCE_I18N_KEYS[source_id]} API Key"),
                value=_get_keys_from_config(app_config, cfg_key),
                type="password",
                key=f"auto_mode_api_key_{source_id}",
            )
            _save_keys_to_config(app_config, cfg_key, api_key)


def validate_video_source(
    tr: Callable[[str], str],
    app_config: dict,
    selected_source: str,
    has_local_materials: bool,
) -> Tuple[bool, str]:
    if selected_source == "local":
        if has_local_materials:
            return True, ""
        return False, tr("Please Upload Local Video Files")

    if selected_source == "auto":
        if vs.get_configured_stock_sources(app_config):
            return True, ""
        return False, tr("Please Configure At Least One Video Source API Key")

    if not vs.has_source_api_key(app_config, selected_source):
        i18n_key = f"Please Enter the {SOURCE_I18N_KEYS[selected_source]} API Key"
        return False, tr(i18n_key)

    return True, ""
