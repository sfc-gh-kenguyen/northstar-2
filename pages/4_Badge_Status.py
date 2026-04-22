from __future__ import annotations

from datetime import datetime

import streamlit as st

from events import load_event_records

st.title("🏅 Badge status")


def _cell(val: str | None) -> str:
    return val if val else "—"


def _status_label(v: bool | None) -> str:
    if v is True:
        return "Issued"
    if v is False:
        return "Not issued yet"
    return "Not published"


def _event_date_for_sort(raw: str | None) -> datetime:
    """Parse common date strings for sorting; missing or invalid sorts last."""
    if not raw:
        return datetime.min
    s = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.min


records = load_event_records()
archived = {n: r for n, r in records.items() if r.get("archived")}
if not records:
    st.info("No events are configured yet.", icon="ℹ️")
    st.stop()
if not archived:
    st.info(
        "No archived events yet. Move finished events to your **archive** tab in the Google Sheet, "
        "then run **GitHub Sync → Push events to GitHub** (and ensure **SHEET_ARCHIVE** is set in Apps Script).",
        icon="ℹ️",
    )
    st.stop()

ordered = sorted(
    archived.items(),
    key=lambda item: (_event_date_for_sort(item[1].get("event_date")), item[0].lower()),
    reverse=True,
)

rows = [
    {
        "Event": name,
        "Event date": _cell(rec.get("event_date")),
        "Issued date": _cell(rec.get("issued_date")),
        "Badge status": _status_label(rec["badges_issued"]),
    }
    for name, rec in ordered
]

st.dataframe(
    rows,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Event": st.column_config.TextColumn("Event", width="large"),
        "Event date": st.column_config.TextColumn("Event date", width="small"),
        "Issued date": st.column_config.TextColumn("Issued date", width="medium"),
        "Badge status": st.column_config.TextColumn("Badge status", width="small"),
    },
)

st.divider()
st.markdown(
    "Please allow **7 business days** from the day of your event for the badges to be issued. "
    "If badges are listed as **issued** for your event, check the email you used for your "
    "Snowflake trial (including spam/junk) for your badge. If your event is listed as **Issued**, "
    "but you have not received your badge, please reach out to **developer-badges-DL@snowflake.com** "
    "(within 30 days of your event)."
)
