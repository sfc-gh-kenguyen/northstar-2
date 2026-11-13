"""Shared navigation buttons — consistent primary/secondary styling."""

from __future__ import annotations

import streamlit as st


def nav_button(
    page: str,
    label: str,
    *,
    primary: bool = False,
    icon: str | None = None,
    key: str | None = None,
) -> None:
    """In-app navigation with outlined (secondary) or filled (primary) styling."""
    kwargs: dict = {"type": "primary" if primary else "secondary"}
    if icon:
        kwargs["icon"] = icon
    if key:
        kwargs["key"] = key
    if st.button(label, **kwargs):
        st.switch_page(page)


def go_to_auto_grader(workshop: str) -> None:
    """Open Auto-Grader with ``workshop`` pre-selected."""
    st.session_state["auto_grader_workshop_preset"] = workshop
    st.query_params["workshop"] = workshop
    st.switch_page("pages/3_Auto-Grader.py")


def external_link_button(
    label: str,
    url: str,
    *,
    primary: bool = True,
    key: str | None = None,
) -> None:
    """External URL button — primary by default for step CTAs."""
    kwargs: dict = {"type": "primary" if primary else "secondary"}
    if key:
        kwargs["key"] = key
    st.link_button(label, url, **kwargs)
