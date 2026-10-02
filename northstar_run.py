"""Shared Streamlit navigation entry for all Northstar Community Cloud instances."""

from __future__ import annotations

import streamlit as st

from app_bootstrap import init_app
from event_hubs import hub_page_path, load_event_hub_configs


def run_app() -> None:
    init_app()
    st.session_state["_northstar_nav_root"] = True

    pages = [
        st.Page("home_page.py", title="Home", icon="❄️", default=True),
        st.Page("pages/1_Event_Page.py", title="Event Page", icon="📝"),
        st.Page("pages/2_Guides_and_Answer_Keys.py", title="Guides & Answer Keys", icon="📚"),
        st.Page("pages/3_Auto-Grader.py", title="Auto-Grader", icon="⚙️"),
        st.Page("pages/4_Badge_Status.py", title="Badge status", icon="🏅"),
    ]

    insert_at = 1
    for hub in load_event_hub_configs():
        path = hub_page_path(hub)
        if not path:
            continue
        pages.insert(
            insert_at,
            st.Page(path, title=hub["nav_title"], icon="🎯"),
        )
        insert_at += 1

    nav = st.navigation(pages)
    nav.run()
