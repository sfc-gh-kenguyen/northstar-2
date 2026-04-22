import streamlit as st
from events import load_events

EVENTS = load_events()

st.title("📝 Trial Sign Up")

if "selected_event" not in st.session_state:
    st.session_state.selected_event = "None"
event = st.session_state["selected_event"]
if not event or event == "None":
    st.warning("Please select your event from the sidebar to see the trial signup link.", icon="⚠️")
    st.stop()

link = EVENTS.get(event)
if link:
    st.markdown(f"Sign up for a Snowflake trial account for **{event}**:")
    st.link_button("Open Trial Signup", link)
else:
    st.markdown(f"**{event}**")
    st.info("Link coming soon.", icon="🔜")
