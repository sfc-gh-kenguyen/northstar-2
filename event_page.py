"""Shared event checklist UI — trial, guides, auto-grader, and badge for any event."""

from __future__ import annotations

from typing import Any

import streamlit as st

from events import load_events, load_event_workshops
from event_hubs import get_event_hub
from lab_resources_ui import render_lab_resources_for_workshop
from nav_helpers import external_link_button, go_to_auto_grader, nav_button
from workshops import load_workshop_rows, workshop_has_answer_key

_DEFAULT_INTRO = (
    "Follow the steps below in order. Use the same email for trial signup and the auto-grader."
)


def _workshop_row(workshop_title: str) -> dict[str, str] | None:
    title = workshop_title.strip()
    if not title:
        return None
    rows = load_workshop_rows()
    for row in rows:
        if row.get("workshop") == title:
            return row
    lower = title.lower()
    for row in rows:
        if row.get("workshop", "").strip().lower() == lower:
            return row
    return None


def _render_workshop_guide(workshop: str, *, key_prefix: str) -> None:
    """Guide link (and optional lab resources) for one workshop on the event checklist."""
    workshop_row = _workshop_row(workshop)
    st.markdown(f"**{workshop}**")
    if not workshop_has_answer_key(workshop):
        st.caption("Prerequisite — no auto-grader for this guide.")
    if workshop_row and (workshop_row.get("guide_url") or "").strip():
        external_link_button(
            workshop_row.get("guide_label") or "View Guide",
            workshop_row["guide_url"],
            key=f"{key_prefix}_guide",
        )
    else:
        st.info("Guide link coming soon.", icon="🔜")
    render_lab_resources_for_workshop(workshop, key_prefix=key_prefix)


def _grader_workshops(workshops: list[str]) -> list[str]:
    return [w for w in workshops if workshop_has_answer_key(w)]


def _hub_workshops(hub: dict[str, Any]) -> list[str]:
    workshops = hub.get("workshops")
    if isinstance(workshops, list) and workshops:
        return [str(w).strip() for w in workshops if str(w).strip()]
    single = str(hub.get("workshop") or "").strip()
    return [single] if single else []


def _trial_event_names(hub: dict[str, Any]) -> list[str]:
    trial_events = hub.get("trial_events")
    if isinstance(trial_events, list) and trial_events:
        return [str(e).strip() for e in trial_events if str(e).strip()]
    return [hub["event_name"]]


def resolve_event_config(event_name: str) -> dict[str, Any]:
    """Build display config for ``event_name``.

    ``event_hubs.json`` overrides workshop lists for large events; otherwise workshops
    come from the optional **Workshop** column on the Events sheet.
    """
    hub = get_event_hub(event_name)
    if hub:
        workshops = _hub_workshops(hub) or load_event_workshops(event_name)
        return {
            "event_name": hub["event_name"],
            "title": hub.get("nav_title") or hub["event_name"],
            "intro": hub.get("intro") or _DEFAULT_INTRO,
            "workshops": workshops,
            "trial_events": _trial_event_names(hub),
        }
    sheet_workshops = load_event_workshops(event_name)
    return {
        "event_name": event_name,
        "title": event_name,
        "intro": _DEFAULT_INTRO,
        "workshops": sheet_workshops,
        "trial_events": [event_name],
    }


def render_event_checklist(event_name: str) -> None:
    """Render the full event checklist for ``event_name``."""
    cfg = resolve_event_config(event_name)
    workshops = cfg["workshops"]

    st.header(f"🎯 {cfg['title']}")

    if cfg.get("intro"):
        st.markdown(cfg["intro"])

    st.warning(
        "Create a trial account using **AI Data Cloud**, not **Cortex Code CLI** — "
        "even if using the CLI in the hands-on lab.",
        icon="⚠️",
    )

    events = load_events()
    trial_names = cfg["trial_events"]

    st.divider()

    st.subheader("Step 1 — Snowflake trial")
    trial_links = [(name, events.get(name)) for name in trial_names]
    found = [(name, url) for name, url in trial_links if url]

    if found:
        if len(found) == 1:
            name, url = found[0]
            st.markdown(f"Sign up for a Snowflake trial account for **{name}**.")
            external_link_button("Open Trial Signup", url)
        else:
            st.markdown("Sign up for a Snowflake trial account for this event.")
            for i, (name, url) in enumerate(found):
                external_link_button(
                    f"Open Trial Signup — {name}",
                    url,
                    key=f"trial_{i}",
                )
    else:
        st.info("Trial signup link coming soon.", icon="🔜")

    st.divider()

    st.subheader("Step 2 — Complete your lab")
    if not workshops:
        st.markdown(
            "Open **Guides & Answer Keys** and select the workshop you are attending."
        )
        nav_button("pages/2_Guides_and_Answer_Keys.py", "Guides & Answer Keys", icon="📚")
    elif len(workshops) == 1:
        _render_workshop_guide(workshops[0], key_prefix="event_lab_0")
    else:
        st.markdown("Complete the guides for this event (prerequisites first, then the main lab):")
        for i, workshop in enumerate(workshops):
            _render_workshop_guide(workshop, key_prefix=f"event_lab_{i}")

    st.divider()

    st.subheader("Step 3 — Auto-grader & answer key")
    if not workshops:
        nav_button("pages/3_Auto-Grader.py", "Go to Auto-Grader", icon="⚙️")
    else:
        grader_workshops = _grader_workshops(workshops)
        if not grader_workshops:
            st.info(
                "No auto-grader for the workshop(s) at this event — complete the guide(s) above.",
                icon="ℹ️",
            )
        else:
            st.markdown(
                "Generate your auto-grader SQL script (same email you used to register), "
                "paste it into a Snowflake worksheet, and run it in full."
            )
            if len(grader_workshops) > 1:
                st.markdown("Open the auto-grader for the main lab you completed:")
            elif len(workshops) > len(grader_workshops):
                st.caption("Prerequisite guides at this event do not use the auto-grader.")
            for i, workshop in enumerate(grader_workshops):
                if st.button(
                    f"Auto-Grader — {workshop}",
                    type="primary",
                    icon="⚙️",
                    key=f"grader_{i}",
                ):
                    go_to_auto_grader(workshop)

    st.divider()

    st.subheader("Badge")
    st.markdown(
        "Complete the lab and run the auto-grader script to qualify for your badge. "
        "Allow **7 business days** after the event; check **Badge status** for updates."
    )
    nav_button("pages/4_Badge_Status.py", "Badge status", icon="🏅")
