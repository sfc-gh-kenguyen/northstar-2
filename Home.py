import streamlit as st

from app_bootstrap import init_app

init_app()
st.session_state["_northstar_nav_root"] = True

pages = [
    st.Page("home_page.py", title="Home", icon="❄️", default=True),
    st.Page("pages/1_Trial_Sign_Up.py", title="Trial Sign Up", icon="📝"),
    st.Page("pages/2_Guides_and_Answer_Keys.py", title="Guides & Answer Keys", icon="📚"),
    st.Page("pages/3_Auto-Grader.py", title="Auto-Grader", icon="⚙️"),
    st.Page("pages/4_Badge_Status.py", title="Badge status", icon="🏅"),
]

nav = st.navigation(pages)
nav.run()
