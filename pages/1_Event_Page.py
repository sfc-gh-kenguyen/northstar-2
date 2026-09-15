import streamlit as st

from event_page import render_event_checklist
from events import load_events

EVENTS = load_events()
EVENT_OPTIONS = ["None"] + list(EVENTS.keys())

st.title("📝 Event Page")


def _sync_event_query_param() -> None:
    ev = st.session_state.get("selected_event", "None")
    if ev and ev != "None":
        st.query_params["event"] = ev
    else:
        try:
            del st.query_params["event"]
        except KeyError:
            pass


st.selectbox(
    "Select your event",
    EVENT_OPTIONS,
    key="selected_event",
    on_change=_sync_event_query_param,
)

event = st.session_state["selected_event"]
if not event or event == "None":
    st.info("Choose your event above to see your trial link, lab guide, and auto-grader steps.", icon="ℹ️")
    st.stop()

render_event_checklist(event)
