from __future__ import annotations

import streamlit as st

from events import load_event_records

st.title("🏅 Badge status")

st.caption(
    "Badge sending is updated from the workshop roster. "
    "**Issued** = emails have gone out; **Not issued yet** = still within the usual window; "
    "**Not published** = the team has not set a status for this row yet."
)


def _status_label(v: bool | None) -> str:
    if v is True:
        return "Issued"
    if v is False:
        return "Not issued yet"
    return "Not published"


records = load_event_records()
if not records:
    st.info("No events are configured yet.", icon="ℹ️")
    st.stop()

rows = [
    {"Event": name, "Badge status": _status_label(rec["badges_issued"])}
    for name, rec in sorted(records.items(), key=lambda x: x[0].lower())
]

st.dataframe(
    rows,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Event": st.column_config.TextColumn("Event", width="large"),
        "Badge status": st.column_config.TextColumn("Badge status", width="small"),
    },
)

st.divider()
st.markdown(
    "If badges are **issued**, check the email you used for your Snowflake trial (including spam/junk). "
    "Questions about a missing badge? Email **developer-badges-DL@snowflake.com** "
    "(preferably within **30 days** of your event)."
)
