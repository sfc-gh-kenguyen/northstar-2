"""Identify which traffic-mirror instance this deployment is (optional).

Set per app in Streamlit **Secrets** as ``NORTHSTAR_INSTANCE`` (e.g. ``"3"``), or use
``Instance3.py`` / ``Instance4.py`` as the main file (sets env automatically).
"""

from __future__ import annotations

import os
import re

_INSTANCE_ENV = "NORTHSTAR_INSTANCE"

# Hostname substrings → instance label (first match wins).
_HOST_INSTANCE_HINTS: tuple[tuple[str, str], ...] = (
    ("northstar-6", "6"),
    ("northstar6", "6"),
    ("northstar-5", "5"),
    ("northstar5", "5"),
    ("northstar-4", "4"),
    ("northstar4", "4"),
    ("northstar-3", "3"),
    ("northstar3", "3"),
    ("northstar-2", "2"),
    ("northstar2", "2"),
    ("northstar-1", "1"),
    ("northstar1", "1"),
)


def _from_streamlit_secrets() -> str | None:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return None
    if get_script_run_ctx() is None:
        return None
    try:
        import streamlit as st

        raw = st.secrets.get(_INSTANCE_ENV)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    except Exception:
        pass
    return None


def _from_request_host() -> str | None:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return None
    if get_script_run_ctx() is None:
        return None
    try:
        import streamlit as st
        from urllib.parse import urlparse

        host = ""
        try:
            host = (urlparse(st.context.url).hostname or "").lower()
        except Exception:
            pass
        if not host:
            raw = st.context.headers.get("Host") or st.context.headers.get("host") or ""
            host = str(raw).lower().split(":")[0]
        if not host:
            return None
        for needle, label in _HOST_INSTANCE_HINTS:
            if needle in host:
                return label
        if host in ("northstar.streamlit.app", "northstar.streamlit.cloud"):
            return "1"
    except Exception:
        pass
    return None


def get_instance_label() -> str | None:
    """Return instance id string (e.g. ``"3"``) or None if not configured."""
    env = os.environ.get(_INSTANCE_ENV, "").strip()
    if env:
        return env
    secret = _from_streamlit_secrets()
    if secret:
        return secret
    return _from_request_host()


def instance_page_title_suffix() -> str:
    """Suffix for ``st.set_page_config`` title when running a numbered mirror."""
    label = get_instance_label()
    if not label or label == "1":
        return ""
    return f" ({label})"
