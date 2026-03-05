from __future__ import annotations

import re

import streamlit as st


st.set_page_config(page_title="Auto-grader Set Up", page_icon="👋", layout="wide")
st.title("👋 Auto-grader Set Up")


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def sql_string_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def looks_like_bad_name_case(value: str) -> bool:
    v = normalize_space(value)
    letters = [ch for ch in v if ch.isalpha()]
    # Only enforce the casing rule for multi-letter names.
    # (A single-letter initial shouldn't be blocked by the all-upper/all-lower rule.)
    if len(letters) <= 1:
        return False
    return all(ch.islower() for ch in letters) or all(ch.isupper() for ch in letters)

def is_allowed_single_initial(raw_value: str) -> bool:
    """
    Allow a single uppercase initial *only* when the user includes a trailing space,
    e.g. 'K ' (common workaround for badge-matching quirks).
    """

    if raw_value is None:
        return False
    return re.fullmatch(r"[A-Z]\s+", raw_value) is not None

st.divider()

left, right = st.columns([1.1, 1])

with left:
    st.subheader("Attendee Information")
    st.caption("Fields marked with * are required.")

    with st.form("greeting_form"):
        email = st.text_input("Email *", placeholder="name@company.com")
        c1, c2 = st.columns(2)
        with c1:
            first_raw = st.text_input("First name *", placeholder="")
            middle_raw = st.text_input("Middle name (optional)", placeholder="")
        with c2:
            last_raw = st.text_input("Last name *", placeholder="")

        submitted = st.form_submit_button("Generate SQL", type="primary")

with right:
    st.subheader("Instructions")
    st.markdown(
        """
1. Fill in your information to generate your auto-grader set up, then click "Generate SQL". Copy the full SQL. Be sure to use the same email address that you used to register for the event.
2. Open a new SQL worksheet in the Snowflake account you used to complete the lab.
3. Paste the generated script from Step 1 in the worksheet.
4. Run the script in full.
5. Copy and paste the full answer key relevant to your workshop in a worksheet and run the entire script:
    * [Data Engineering](https://github.com/Snowflake-Labs/builder-workshops/blob/main/data-eng/ingestion-transformation-delivery.sql)
    * [Snowpipe Streaming](https://github.com/Snowflake-Labs/builder-workshops/blob/main/data-eng/snowpipe-streaming.sql)
    * [Snowflake Intelligence](https://github.com/Snowflake-Labs/builder-workshops/blob/main/gen-ai/snowflake-intelligence.sql)
    * [Dynamic Table](https://github.com/Snowflake-Labs/builder-workshops/blob/main/data-eng/dynamic-tables.sql)
    * [From Zero to Agents](https://github.com/Snowflake-Labs/builder-workshops/blob/main/gen-ai/zero-agent.sql)
6. If you passed the lab, you should see an output in the Snowflake console with a message like "You've successfully completed this lab!". Please allow up to 7 business days to receive your badge.
        """.strip()
    )

    st.subheader("Rules")
    st.markdown(
        """
- **Format your name correctly** (no all-lowercase / no all-uppercase).
- **No middle name?** Use an empty string: `''`.
- **Email must match** what they used to register.
        """.strip()
    )

    st.subheader("Badge Support")
    st.info(
        "Learners can email **developer-badges-DL@snowflake.com** if you want to inquire "
        "about a missing badge. Badges will be sent within 7 business days of the event. "
        "We can only support learners if inquired within 30 days of the event. "
        "After 30 days, we cannot guarantee support.",
        icon="📧",
    )

if not submitted:
    st.info("Fill out the form and click **Generate SQL**.", icon="ℹ️")
    st.stop()

email = normalize_space(email)

# Keep both raw + normalized variants:
# - raw is used for the "single character" check (so users can follow the instruction to add a trailing space)
# - normalized is used for SQL + other validation
first = normalize_space(first_raw)
middle = normalize_space(middle_raw)
last = normalize_space(last_raw)

# For SQL generation, preserve the user's original input (including trailing spaces),
# because some workshop badge workflows rely on that exact value.
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
if not last:
    errors.append("Last name is required.")

if errors:
    for e in errors:
        st.error(e)
    st.stop()

name_case_errors: list[str] = []
# Special case: a single lowercase initial (even with spaces in raw input, e.g. "k ")
# should report the "no all lowercase" error instead of the single-character message.
if len(first) == 1 and first.islower():
    name_case_errors.append("First name cannot be all lowercase or all uppercase.")
if middle_raw and len(middle) == 1 and middle.islower():
    name_case_errors.append("Middle name cannot be all lowercase or all uppercase.")
if len(last) == 1 and last.islower():
    name_case_errors.append("Last name cannot be all lowercase or all uppercase.")

if looks_like_bad_name_case(first):
    name_case_errors.append("First name cannot be all lowercase or all uppercase.")
if middle and looks_like_bad_name_case(middle):
    name_case_errors.append("Middle name cannot be all lowercase or all uppercase.")
if looks_like_bad_name_case(last):
    name_case_errors.append("Last name cannot be all lowercase or all uppercase.")

if name_case_errors:
    for e in name_case_errors:
        st.error(e)
    st.stop()

single_char_msg = "A single character is not allowed, please input a space after to proceed."
single_char_errors: list[str] = []
# Reject single-character names even if the user tries to add spaces (e.g. "a " -> "a").
if len(first) == 1 and not first.islower() and not is_allowed_single_initial(first_raw):
    single_char_errors.append(single_char_msg)
if middle_raw and len(middle) == 1 and not middle.islower() and not is_allowed_single_initial(middle_raw):
    single_char_errors.append(single_char_msg)
if len(last) == 1 and not last.islower() and not is_allowed_single_initial(last_raw):
    single_char_errors.append(single_char_msg)

if single_char_errors:
    # Show the message once (even if multiple fields triggered it).
    st.error(single_char_msg)
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
-- Format your name CORRECTLY (do not use all lower case)
-- If you do not have a middle name, use an empty string '' ; do not use "null" in place of any values
-- Double-check your email. You must use the same email for the greeting as you used to register
{greeting_call_sql}
""".strip() + "\n"

st.divider()
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
