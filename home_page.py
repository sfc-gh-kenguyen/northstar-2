import streamlit as st

# Home.py calls init_app() then loads this file via st.navigation — do not init again
# (duplicate selectbox key "selected_event"). Backup Cloud entry uses home_page.py alone.
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
    st.subheader("📝 Trial Sign Up")
    st.markdown("Sign up for a Snowflake trial account for your event.")
    st.page_link("pages/1_Trial_Sign_Up.py", label="Go to Trial Sign Up", icon="➡️")

with col2:
    st.subheader("⚙️ Auto-Grader")
    st.markdown("Generate your auto-grader SQL script.")
    st.page_link("pages/3_Auto-Grader.py", label="Go to Auto-Grader", icon="➡️")

st.divider()

c3, c4 = st.columns(2)
with c3:
    st.subheader("🏅 Badge status")
    st.markdown("Check the badging status of your event.")
    st.page_link("pages/4_Badge_Status.py", label="Go to Badge status", icon="➡️")
with c4:
    st.subheader("📚 Guides & answer keys")
    st.markdown("Workshop guides and answer key scripts.")
    st.page_link("pages/2_Guides_and_Answer_Keys.py", label="Go to Guides & Answer Keys", icon="➡️")

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
st.page_link(
    "pages/3_Auto-Grader.py",
    label="Go to Auto-Grader",
    icon="⚙️",
)

st.divider()

st.subheader("Badge Support")
st.info(
    "Learners can email **developer-badges-DL@snowflake.com** if you want to inquire "
    "about a missing badge. Badges will be sent within 7 business days of the event. "
    "We can only support learners if inquired within 30 days of the event. "
    "After 30 days, we cannot guarantee support.",
    icon="📧",
)
