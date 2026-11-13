import streamlit as st

from nav_helpers import nav_button

# Home.py calls init_app() then loads this file via st.navigation — do not init again.
# Backup Cloud entry uses home_page.py alone (init_app runs there once).
if not st.session_state.get("_northstar_nav_root"):
    from app_bootstrap import init_app

    init_app()

st.title("❄️ Snowflake Northstar")

st.markdown(
    "Welcome to **Snowflake Northstar** — your one-stop hub for workshop instructions, "
    "guides, and auto-grader setup."
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Event Page")
    st.markdown("Select your event for trial signup, lab guide, and auto-grader steps.")
    nav_button("pages/1_Event_Page.py", "Go to Event Page", primary=True, icon="➡️")

with col2:
    st.subheader("⚙️ Auto-Grader")
    st.markdown("Generate your auto-grader SQL script.")
    nav_button("pages/3_Auto-Grader.py", "Go to Auto-Grader", icon="➡️", key="home_nav_grader")

st.divider()

c3, c4 = st.columns(2)
with c3:
    st.subheader("🏅 Badge status")
    st.markdown("Check the badging status of your event.")
    nav_button("pages/4_Badge_Status.py", "Go to Badge status", icon="➡️")
with c4:
    st.subheader("📚 Guides & answer keys")
    st.markdown("Workshop guides and answer key scripts.")
    nav_button("pages/2_Guides_and_Answer_Keys.py", "Go to Guides & Answer Keys", icon="➡️")

st.divider()

st.subheader("📋 How to Earn Your Badge")
st.markdown("There are **2 steps** to complete:")

st.markdown("**Step 1: Register and Complete the Lab**")
st.markdown(
    "Make sure you have registered/checked-in with the Snowflake team "
    "and successfully completed the hands-on lab."
)

st.markdown("**Step 2: Set Up the Auto-grader and Run the Tests**")
st.markdown(
    "After completing the Guide, use the Auto-Grader/Answer Key page to generate a script "
    "that includes both the auto-grader setup and the answer key for your workshop. "
    "Paste the generated script into a Snowflake SQL worksheet and run it in full."
)
nav_button("pages/3_Auto-Grader.py", "Go to Auto-Grader", icon="⚙️", key="home_steps_grader")

st.divider()

st.subheader("Badge Support")
st.info(
    "Learners can email **developer-badges-DL@snowflake.com** if you want to inquire "
    "about a missing badge. Badges will be sent within 7 business days of the event. "
    "We can only support learners if inquired within 30 days of the event. "
    "After 30 days, we cannot guarantee support.",
    icon="📧",
)
