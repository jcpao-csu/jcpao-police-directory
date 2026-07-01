import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
import pandas as pd
import os
import time

load_dotenv("../jcpao-csu.env", override=True)  # points up to parent directory


# --- Local .env file ---
# from dotenv import load_dotenv
# import os
# load_dotenv(override=True)
# conn_string = os.getenv("DATABASE_URL")


# --- Initialize database connection pool ---

# SQLALCHEMY - Define get_engine()
@st.cache_resource
def get_engine(database_url):
    return create_engine(
        database_url,
        pool_size=10,
        max_overflow=5,
        pool_pre_ping=True,
        pool_timeout=60,
    )

# Establish NEON database connection (via sqlalchemy)
try:
    database_url = st.secrets["neonDB"]["database_url"]
except Exception:
    database_url = os.getenv("SQLALCHEMY_DATABASE_URL")

# Force the psycopg (v3) driver regardless of how the URL is stored
if database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

# Attempt connection
try:
    engine = get_engine(database_url)
except Exception as e:
    st.error(
        f"Network is blocking connection to the database server.\n"
        f"Please try again on a different network/internet connection, or reach out to admin at ujcho@jacksongov.org.\n{e}"
    )
    st.stop()

# --- Define helper functions ---

# Define parse_enum()
def parse_enum(array):
    """Return enum array dtypes in a workable format"""
    if pd.isna(array):
        return []
    array = array.strip('{}')
    return array.split(',') if array else []

def display_personal_name(row):
    if row['Preferred Name']:
        return f"{row['Preferred Name'].strip()} {row['Last Name'].strip()}"
    else:
        return f"{row['First Name'].strip()} {row['Last Name'].strip()}"

# Define ordinal()
def ordinal(n):
    if 10 <= n % 100 <= 20: # Covers unique cases, like 11th, 12th, 13th
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

# Define display_service()
def display_service(service_days, service_percentile):
    if service_days and service_percentile:
        st.write(f"**Fun fact:** You have been with the JCPAO for {service_days} days, and are in the ***:blue[{ordinal(service_percentile)} percentile]*** among all active JCPAO employees! Thank you for your service to the JCPAO!")

# Birthday Month (not enum)

# Filter by birthday month:
months_dict = {
    '1': 'Jan',
    '2': 'Feb',
    '3': 'Mar',
    '4': 'Apr',
    '5': 'May',
    '6': 'Jun',
    '7': 'Jul',
    '8': 'Aug',
    '9': 'Sep',
    '10': 'Oct',
    '11': 'Nov',
    '12': 'Dec'
}

def parse_month(type: str, value: str = None):
    month_list = list(months_dict.keys())

    if type == "options":
        return month_list
    elif type == "index":
        try:
            return month_list.index(value)
        except ValueError: # Value isn't in the list
            return None
    elif type == "format_func":
        return lambda x: months_dict[x]

# --- Define function to read tables from Neon DB ---

@st.cache_data(show_spinner="Loading data, please wait...")
def query_table(sql_query: str, _engine: Engine = engine) -> pd.DataFrame:
    if _engine is None:
        return pd.DataFrame()

    try:
        with _engine.connect() as conn:
            return pd.read_sql(text(sql_query), conn)
    except Exception as e:
        st.error(f"Database query failed: {e}")
        return pd.DataFrame()

# --- Query tables ---

# Get main STAFF_VIEW table
staff_view = query_table("SELECT * FROM employee_info_view")

if staff_view.empty:
    staff_view = pd.DataFrame()
else:
    staff_view["Assigned Unit"] = staff_view["Assigned Unit"].apply(parse_enum)
    staff_view["Race"] = staff_view["Race"].apply(parse_enum)

STAFF_VIEW = staff_view.copy()


# --- Log activity ---

def log_user(
    email_address: str,
    _engine: Engine = engine
):
    """
    Log user activity in the user_activity table.
    Possible values in user_activity_enum:
        'SIGN UP' / 'LOGIN' / 'UPDATE PROFILE' / 'REMOVE PROFILE' / 'ANNOUNCEMENT' / 'ADMIN-AUTHORIZE' / 'ADMIN-REMOVE PROFILE' / 'POST-TRIAL SURVEY' / 'RESET PASSWORD' / 'UPDATE PHOTO' / 'UPDATE NAME' / 'UPDATE JOB' / 'UPDATE OFFICE' / 'UPDATE DEMOGRAPHIC' / 'UPDATE INTERN'
    Logs user login (to track who is using the directory).
    SQLAlchemy's pool_pre_ping (set on the engine above) checks for stale/closed
    connections before handing them out, so no manual reconnect retry is needed here.
    """

    if _engine is None:
        return

    try:
        with _engine.connect() as conn:
            conn.execute(
                text("INSERT INTO police_log (user_email) VALUES (:email)"),
                {"email": email_address},
            )
            conn.commit()

    except Exception as e:
        error_msg = st.error(f"Error logging activity: {e}")
        time.sleep(2)
        error_msg.empty()


# Define refresh_app() function
def refresh_app():
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()
