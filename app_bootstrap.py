"""Shared setup for both Home.py and home_page.py entrypoints.

Streamlit Cloud may use either file as the main script; this module ensures
page config, event list, and session state are initialized exactly once per
session (set_page_config must not run twice).
"""

from __future__ import annotations

import json
from html import escape
from urllib.parse import urlencode, urlparse, urlunparse

import streamlit as st
import streamlit.components.v1 as components

from events import load_events

_LEGACY_STREAMLIT_HOST = "northstarautograder.streamlit.app"
_CANONICAL_STREAMLIT_HOST = "northstar.streamlit.app"


def maybe_redirect_legacy_streamlit_domain() -> None:
    """If this deployment is still reachable on the old *.streamlit.app host, send users to the canonical app."""
    try:
        current = st.context.url
    except Exception:
        return
    try:
        parsed = urlparse(current)
    except Exception:
        return
    if (parsed.hostname or "").lower() != _LEGACY_STREAMLIT_HOST:
        return

    path = parsed.path or "/"
    query_pairs: list[tuple[str, str]] = []
    try:
        qp = st.query_params
        for key in qp:
            if hasattr(qp, "get_all"):
                for v in qp.get_all(key):
                    query_pairs.append((key, str(v)))
            else:
                val = qp[key]
                if isinstance(val, list):
                    for v in val:
                        query_pairs.append((key, str(v)))
                else:
                    query_pairs.append((key, str(val)))
    except Exception:
        pass
    query = urlencode(query_pairs, doseq=True)
    dest = urlunparse(("https", _CANONICAL_STREAMLIT_HOST, path, "", query, ""))

    safe_meta_url = escape(dest, quote=True)
    components.html(
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f'<meta http-equiv="refresh" content="0;url={safe_meta_url}">'
        f"<script>window.top.location.replace({json.dumps(dest)});</script>"
        "</head><body></body></html>",
        height=0,
        scrolling=False,
    )
    st.stop()


def init_app() -> None:
    # set_page_config must run at most once per session; sidebar/widgets must run every rerun.
    if "_northstar_page_config" not in st.session_state:
        st.set_page_config(page_title="Snowflake Northstar", page_icon="❄️", layout="wide")
        st.session_state._northstar_page_config = True

    maybe_redirect_legacy_streamlit_domain()

    events = load_events()
    event_options = ["None"] + list(events.keys())

    if "selected_event" not in st.session_state:
        st.session_state.selected_event = "None"

    with st.sidebar:
        st.selectbox("Select your event", event_options, key="selected_event")
