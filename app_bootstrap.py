"""Shared setup for both Home.py and home_page.py entrypoints.

Streamlit Cloud may use either file as the main script; this module ensures
page config, event list, and session state are initialized exactly once per
session (set_page_config must not run twice).
"""

from __future__ import annotations

import streamlit as st

from events import load_events


def init_app() -> None:
    # set_page_config must run at most once per session; sidebar/widgets must run every rerun.
    if "_northstar_page_config" not in st.session_state:
        st.set_page_config(page_title="Snowflake Northstar", page_icon="❄️", layout="wide")
        st.session_state._northstar_page_config = True

    events = load_events()
    event_options = ["None"] + list(events.keys())

    if "selected_event" not in st.session_state:
        st.session_state.selected_event = "None"

    with st.sidebar:
        st.selectbox("Select your event", event_options, key="selected_event")
