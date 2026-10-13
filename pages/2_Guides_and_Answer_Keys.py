import streamlit as st

from lab_resources_ui import render_lab_resources_for_workshop
from nav_helpers import external_link_button, go_to_auto_grader
from workshops import load_workshop_rows, workshop_has_answer_key


st.title("📚 Workshop Guides and Answer Keys")

rows = load_workshop_rows()
if not rows:
    st.info(
        "No workshops are configured yet. Add a **Guides & Answer Keys** tab to your Google Sheet "
        "(see column headers below), set **SHEET_GUIDES** in Apps Script to that tab’s name, then run "
        "**GitHub Sync → Push events & guides to GitHub**, or edit **workshops.json** in this repository.",
        icon="ℹ️",
    )
    st.markdown(
        """
**Sheet tab (when using sync):** create a tab (e.g. `Guides & Answer Keys`) and set `SHEET_GUIDES` in Apps Script to match its name.

| Column | Required |
|--------|----------|
| **Workshop** (or **Course name** / **Title**) | Yes — full title (must match Auto-Grader once an answer key exists) |
| **Guide URL** | No — leave blank for **Coming soon** in the Guide column |
| **Answer Key URL** | No — leave blank until the script is ready (**Coming soon** on the page; row stays out of the Auto-Grader list until filled) |
| **Guide link text** | No — link label when Guide URL is set (default `View Guide`) |
| **Answer Key link text** | No — link label when Answer Key URL is set (default: file name from URL) |
| **Guide placeholder** | No — overrides *Coming soon* when Guide URL is empty |
| **Answer Key placeholder** | No — overrides *Coming soon* when Answer Key URL is empty |
        """.strip()
    )
    st.stop()

for i, r in enumerate(rows):
    st.markdown(f"**{r['workshop']}**")
    if not workshop_has_answer_key(r["workshop"]):
        st.caption("Prerequisite — no auto-grader for this guide.")
    guide_col, key_col, grader_col = st.columns(3)
    with guide_col:
        guide_url = (r.get("guide_url") or "").strip()
        if guide_url:
            external_link_button(
                r.get("guide_label") or "View Guide",
                guide_url,
                key=f"guide_{i}",
            )
        else:
            st.caption(r.get("guide_pending_text") or "Coming soon")
    with key_col:
        answer_url = (r.get("answer_key_url") or "").strip()
        if answer_url:
            external_link_button(
                r.get("answer_key_label") or "View Answer Key",
                answer_url,
                primary=False,
                key=f"answer_{i}",
            )
        else:
            st.caption(r.get("answer_key_pending_text") or "Coming soon")
    with grader_col:
        if workshop_has_answer_key(r["workshop"]):
            if st.button(
                "Auto-Grader",
                type="primary",
                icon="⚙️",
                key=f"grader_{i}",
            ):
                go_to_auto_grader(r["workshop"])
    render_lab_resources_for_workshop(r["workshop"], key_prefix=f"guides_{i}")
    if i < len(rows) - 1:
        st.divider()
