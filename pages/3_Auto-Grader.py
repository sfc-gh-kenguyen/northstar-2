from __future__ import annotations

import re

import requests
import streamlit as st
import streamlit.components.v1 as components

ANSWER_KEYS: dict[str, str] = {
    "Data Ingestion, Transformation, and Delivery with Snowflake":
        "https://raw.githubusercontent.com/Snowflake-Labs/builder-workshops/main/data-eng/ingestion-transformation-delivery.sql",
    "Build an Automated Data Pipeline with Snowpipe":
        "https://raw.githubusercontent.com/Snowflake-Labs/builder-workshops/main/data-eng/snowpipe-streaming.sql",
    "Building Intelligent Data Application with Snowflake":
        "https://raw.githubusercontent.com/Snowflake-Labs/builder-workshops/main/gen-ai/snowflake-intelligence.sql",
    "Creating Declarative Data Pipelines with Dynamic Tables":
        "https://raw.githubusercontent.com/Snowflake-Labs/builder-workshops/main/data-eng/dynamic-tables.sql",
    "From Zero to Agents: Building End-To-End Data Pipelines for an AI Agent (Data for Breakfast HOL)":
        "https://raw.githubusercontent.com/Snowflake-Labs/builder-workshops/main/gen-ai/zero-agent.sql",
}

WORKSHOP_OPTIONS = ["None (auto-grader setup only)"] + list(ANSWER_KEYS.keys())

st.title("⚙️ Auto-Grader/Answer Key")


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def sql_string_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


st.divider()

left, right = st.columns([1.1, 1])

with left:
    st.subheader("Attendee Information")
    st.caption("Fields marked with * are required.")

    with st.form("greeting_form"):
        workshop = st.selectbox("Workshop *", WORKSHOP_OPTIONS)
        email = st.text_input("Email *", placeholder="name@company.com")
        c1, c2 = st.columns(2)
        with c1:
            first_raw = st.text_input("First name *", placeholder="")
            middle_raw = st.text_input("Middle name (optional)", placeholder="")
        with c2:
            last_raw = st.text_input("Last name *", placeholder="")

        submitted = st.form_submit_button("Generate SQL", type="primary")

    error_container = st.container()

with right:
    st.subheader("How to Use")
    st.markdown(
        """
1. Select your workshop from the dropdown.
2. Fill in your information, then click "Generate SQL". Be sure to use the same email address that you used to register for the event.
3. Open a new SQL worksheet in the Snowflake account you used to complete the lab.
4. Paste the generated script in the worksheet and run it in full. The script includes both the auto-grader setup and the answer key for your workshop.
        """.strip()
    )

    st.subheader("Rules")
    st.markdown(
        """
- **No middle name?** Leave the field blank.
- **Email must match** what you used to register for the event.
        """.strip()
    )

if not submitted:
    st.info("Fill out the form and click **Generate SQL**.", icon="ℹ️")
    st.stop()

email = normalize_space(email)

# Normalized values for required / quote-only checks; raw strings go into SQL (preserves spacing).
first = normalize_space(first_raw)
middle = normalize_space(middle_raw)
last = normalize_space(last_raw)

# Preserve original input in SQL (including intentional spacing).
first_sql = first_raw or ""
middle_sql = middle_raw or ""
last_sql = last_raw or ""

errors: list[str] = []
if not email:
    errors.append("Email is required.")
elif not EMAIL_RE.match(email):
    errors.append("Email doesn't look valid (expected something like name@company.com).")

if not first:
    errors.append("First name is required.")
elif re.fullmatch(r"['\"\u201c\u201d\u2018\u2019\s]+", first):
    errors.append("First name contains only quote characters \u2014 please enter your actual name.")
if not last:
    errors.append("Last name is required.")
elif re.fullmatch(r"['\"\u201c\u201d\u2018\u2019\s]+", last):
    errors.append("Last name contains only quote characters \u2014 please enter your actual name.")
if middle and re.fullmatch(r"['\"\u201c\u201d\u2018\u2019\s]+", middle):
    errors.append("Middle name contains only quote characters \u2014 leave the field blank if you don't have one.")

if errors:
    with error_container:
        for e in errors:
            st.error(e)
    st.stop()

greeting_call_sql = (
    "select util_db.public.greeting("
    f"{sql_string_literal(email)}, "
    f"{sql_string_literal(first_sql)}, "
    f"{sql_string_literal(middle_sql)}, "
    f"{sql_string_literal(last_sql)}"
    ");"
)

# Always generate the full workshop script (no toggles).
sql_out = f"""--!jinja
use role accountadmin;

create or replace api integration dora_api_integration 
api_provider = aws_api_gateway 
api_aws_role_arn = 'arn:aws:iam::321463406630:role/snowflakeLearnerAssumedRole' 
enabled = true 
api_allowed_prefixes = ('https://awy6hshxy4.execute-api.us-west-2.amazonaws.com/dev/edu_dora');

create database if not exists util_db;
use database util_db;
use schema public;

create or replace external function util_db.public.grader(        
 step varchar     
 , passed boolean     
 , actual integer     
 , expected integer    
 , description varchar) 
 returns variant 
 api_integration = dora_api_integration 
 context_headers = (current_timestamp,current_account, current_statement, current_account_name) 
 as 'https://awy6hshxy4.execute-api.us-west-2.amazonaws.com/dev/edu_dora/grader'  
;  

select grader(step, (actual = expected), actual, expected, description) as graded_results from (SELECT
 'AUTO_GRADER_IS_WORKING' as step
 ,(select 123) as actual
 ,123 as expected
 ,'The Snowflake auto-grader has been successfully set up in your account!' as description
);

create or replace external function util_db.public.greeting(
      email varchar
    , firstname varchar
    , middlename varchar
    , lastname varchar)
returns variant
api_integration = dora_api_integration
context_headers = (current_timestamp, current_account, current_statement, current_account_name) 
as 'https://awy6hshxy4.execute-api.us-west-2.amazonaws.com/dev/edu_dora/greeting'
; 


-- Be sure to follow the rules your session leader presents
-- If you do not have a middle name, use an empty string '' ; do not use "null" in place of any values
-- Double-check your email. You must use the same email for the greeting as you used to register
{greeting_call_sql}
""".strip() + "\n"

answer_key_sql = ""
if workshop != "None (auto-grader setup only)" and workshop in ANSWER_KEYS:
    with st.spinner("Fetching answer key..."):
        try:
            resp = requests.get(ANSWER_KEYS[workshop], timeout=15)
            resp.raise_for_status()
            answer_key_sql = resp.text
        except requests.RequestException:
            st.warning(
                "Could not fetch the answer key from GitHub. "
                "The auto-grader setup script is still included below.",
                icon="⚠️",
            )

if answer_key_sql:
    sql_out += (
        "\n-- ============================================\n"
        f"-- Answer Key: {workshop}\n"
        "-- ============================================\n\n"
        + answer_key_sql.strip() + "\n"
    )

st.divider()
st.markdown('<div id="generated-sql"></div>', unsafe_allow_html=True)
st.subheader("Generated Snowflake SQL")
st.code(sql_out)
st.info(
    "Copy the script above, paste it into a **Snowflake worksheet**, and run it. "
    "You can also download it as a `.sql` file below.",
    icon="ℹ️",
)

st.download_button(
    "Download as .sql",
    data=sql_out.encode("utf-8"),
    file_name="workshop_greeting.sql",
    mime="text/sql",
)

components.html("""
<script>
    function scrollToSQL() {
        const target = window.parent.document.getElementById('generated-sql');
        if (target) {
            target.scrollIntoView({behavior: 'smooth', block: 'start'});
        } else {
            const main = window.parent.document.querySelector('section.main');
            if (main) {
                main.scrollTo({top: main.scrollHeight, behavior: 'smooth'});
            }
        }
    }
    setTimeout(scrollToSQL, 300);
</script>
""", height=0)
