import streamlit as st
from psycopg_pool import ConnectionPool
import psycopg
import pandas as pd
import time

# --- Local .env file ---
# from dotenv import load_dotenv
# import os
# load_dotenv(override=True)
# conn_string = os.getenv("DATABASE_URL")


# --- Initialize database connection pool ---

# Define get_database_session() 
@st.cache_resource
def get_database_session(database_url: str):
    try: 
        # Create a database session object that points to the URL.
        pool = ConnectionPool(
            conninfo=database_url, 
            min_size=1, 
            max_size=10,
            max_lifetime=300, # recycle connections every 300 seconds
            max_idle=60, # close idle connections after 60 seconds
            timeout=10 # wait 10 seconds to connect
        ) # Initialize connection pool
        return pool
    except psycopg.OperationalError as e:
        st.error(
            f"Network is blocking connection to the database server.\n"
            f"Please try again on a different network/internet connection, or reach out to admin at ujcho@jacksongov.org.\n{e}"
        )
        return None

# Establish NEON database connection (via psycopg3)
database_url = st.secrets["neonDB"]["database_url"]
# database_url2 = st.secrets["neonDB"]["DATABASE_URL"]

# Attempt connection
db_connection = get_database_session(database_url)
# db_connection2 = get_database_session(database_url2)

# --- Define helper functions ---

# Define parse_enum()
def parse_enum(array):
    """Return enum array dtypes in a workable format"""
    if pd.isna(array):
        return []
    array = array.strip('{}')
    return array.split(',') if array else []

# Define display_personal_name()
# def display_personal_name(pref_name, first_name):
#     if not pref_name:
#         return first_name
#     else:
#         return pref_name

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

@st.cache_data
def query_table(sql_query: str, _connection: ConnectionPool = db_connection) -> pd.DataFrame:
    if _connection is None:
        return pd.DataFrame()
    
    try:
        if isinstance(_connection, ConnectionPool):
            with _connection.connection() as conn:
                df = pd.read_sql(sql_query, conn)

        else:
            df = pd.read_sql(sql_query, _connection)

        return df
    
    except psycopg.OperationalError as e:
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
    _connection: ConnectionPool = db_connection
):
    """
    Log user activity in the user_activity table.
    Possible values in user_activity_enum:
        'SIGN UP' / 'LOGIN' / 'UPDATE PROFILE' / 'REMOVE PROFILE' / 'ANNOUNCEMENT' / 'ADMIN-AUTHORIZE' / 'ADMIN-REMOVE PROFILE' / 'POST-TRIAL SURVEY' / 'RESET PASSWORD' / 'UPDATE PHOTO' / 'UPDATE NAME' / 'UPDATE JOB' / 'UPDATE OFFICE' / 'UPDATE DEMOGRAPHIC' / 'UPDATE INTERN'
    Logs user login (to track who is using the directory).
    See technical notes: https://www.psycopg.org/psycopg3/docs/basic/params.html
    """

    try:
        # Always grab a fresh connection from the pool
        with _connection.connection() as conn:
            if conn.closed:
                # Replace with a fresh connection if the previous one was bad or stale
                conn = _connection.connection()

            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO police_log (user_email) VALUES (%s)",
                    (email_address, ),
                )
                conn.commit()

    except psycopg.OperationalError as e:
        # This catches stale/SSL-closed connections and reattempts once
        try:
            # st.warning("Reconnecting to database...")
            with _connection.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO police_log (user_email) VALUES (%s)",
                        (email_address),
                    )
                    conn.commit()
        except Exception as e2:
            error_msg1 = st.error(f"Database reconnect failed: {e2}")
            time.sleep(2)
            error_msg1.empty()

    except Exception as e:
        error_msg2 = st.error(f"Error logging activity: {e}")
        time.sleep(2)
        error_msg2.empty()


# Define refresh_app() function
def refresh_app():
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()