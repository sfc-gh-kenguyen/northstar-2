"""Entrypoint ONLY for the legacy Streamlit hostname ``northstarautograder.streamlit.app``.

If you still operate a separate Streamlit app on that hostname, set its main file to
``LegacyAutograderRedirect.py``. The primary Northstar app should use ``Home.py``.

If this file runs on the wrong host, we show a link instead of redirecting (avoids a reload loop).
"""

from __future__ import annotations

import json
from html import escape
from urllib.parse import urlencode, urlparse, urlunparse

import streamlit as st
import streamlit.components.v1 as components

_LEGACY_HOST = "northstarautograder.streamlit.app"
_CANONICAL_ORIGIN = "https://northstar.streamlit.app"


def _request_host() -> str:
    try:
        h = (urlparse(st.context.url).hostname or "").lower()
        if h:
            return h
    except Exception:
        pass
    try:
        raw = st.context.headers.get("Host") or st.context.headers.get("host") or ""
        return raw.lower().split(":")[0]
    except Exception:
        return ""


st.set_page_config(page_title="Redirecting…", layout="centered")

host = _request_host()
if host != _LEGACY_HOST:
    st.warning("This redirect entrypoint is only used for the legacy Streamlit hostname.")
    st.link_button("Open Northstar", _CANONICAL_ORIGIN)
    st.stop()

path = "/"
try:
    path = urlparse(st.context.url).path or "/"
except Exception:
    pass
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
dest = urlunparse(("https", "northstar.streamlit.app", path, "", query, ""))

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
