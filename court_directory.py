"""
File: court_directory.py
Function: Streamlit page for JCPAO directory (EXTERNAL view for COURTS)
Author: Joseph Cho, ujcho@jacksongov.org
Date: April 30, 2025
"""

import streamlit as st
from pathlib import Path 
import pandas as pd

from connect_data import STAFF_VIEW
from photo import load_photo


# --- Configure Streamlit page settings --- 
jcpao_logo = Path("assets/logo/jcpao_logo_500x500.png")

# # --- JCPAO Streamlit page logo --- 
# st.logo(jcpao_logo, size="large", link="https://www.jacksoncountyprosecutor.com")

# --- Load data --- 

apa_data = STAFF_VIEW.copy()
apa_data = apa_data.loc[apa_data["Position"].isin(['Exec', 'CTA', 'TTL', 'APA'])]
apa_data.sort_values(by=["Last Name", "First Name"], ascending=[True, True], inplace=True, ignore_index=True)


# --- Initialize session state --- 

if "courtview_selected_position" not in st.session_state:
    st.session_state["courtview_selected_position"] = "All"

if "courtview_selected_unit" not in st.session_state:
    st.session_state["courtview_selected_unit"] = "All"

if "courtview_selected_location" not in st.session_state:
    st.session_state["courtview_selected_location"] = "All"

if "courtview_searched_text" not in st.session_state: 
    st.session_state["courtview_searched_text"] = ""

if "courtview_view" not in st.session_state:
    st.session_state["courtview_view"] = "Main Directory"


# --- Define callback functions --- 

# Define update_df() function
def update_df():

    filtered_df = apa_data.copy()

    if st.session_state["courtview_selected_position"] != 'All':
        filtered_df = filtered_df[filtered_df['Position']==st.session_state["courtview_selected_position"]].reset_index(drop=True)
    if st.session_state["courtview_selected_unit"] != 'All':
        filtered_df = filtered_df[filtered_df['Assigned Unit'].apply(lambda x: st.session_state["courtview_selected_unit"] in x)].reset_index(drop=True)
    if st.session_state["courtview_selected_location"] != 'All': 
        filtered_df = filtered_df[filtered_df['Office Location']==st.session_state["courtview_selected_location"]].reset_index(drop=True)
    if st.session_state["courtview_searched_text"]: # Added searched_text to main clickback action 
        searched_text = st.session_state["courtview_searched_text"].strip().lower()
        words = list({w for w in searched_text.split() if w}) # split search text into unique words
        search_cols = ["Full Name", "First Name", "Middle Name", "Last Name", "Suffix", "Preferred Name"]
        combined = filtered_df[search_cols].astype(str).agg(" ".join, axis=1).str.lower() # combine searchable columns into a single lowercase string per row
        mask = combined.apply(lambda text: any(word in text for word in words)) # match if ANY word appears in the combined text

        filtered_df = filtered_df[mask].reset_index(drop=True)

    st.session_state["courtview_filtered_df"] = filtered_df.reset_index(drop=True)

# Reset filters button
def reset_filters():
    st.session_state["courtview_selected_position"] = "All"
    st.session_state["courtview_selected_unit"] = "All"
    st.session_state["courtview_selected_location"] = "All"
    st.session_state["courtview_searched_text"] = ""
    # filtered_df = apa_data.copy()
    # st.session_state["courtview_filtered_df"] = filtered_df
    st.session_state["courtview_filtered_df"] = apa_data

# --- Sidebar Filter functions --- 

with st.sidebar:
    # Select options: position / unit / location / birthday month 
    st.title("Law Enforcement Agencies of Jackson County, Missouri")
    st.write("***JCPAO Police Directory 🚔***")
    st.divider()
    st.markdown(
        "This directory provides information on all active attorneys and Executive Staff in the Jackson County Prosecuting Attorney's Office. "
        "Please reach out to [Joseph Cho](mailto:ujcho@jacksongov.org) with any questions or suggestions on how to improve the police directory!"
    )
    st.divider()
    st.selectbox(
            "**Select the directory to view:**",
            options=['Main Directory','Contact Directory'],
            key="courtview_view"
        )
    st.divider()
    # Filter by job position: 
    positions_dict = {
        'All': 'All Job Positions', 
        'Exec': 'Executive Staff', 
        'CTA': 'Chief Trial Attorneys', 
        'TTL': 'Team Trial Leaders', 
        'APA': 'APAs',
        # 'I': 'Investigators',
        # 'VA': 'Victim Advocates',
        # 'LA': 'Legal Assistants',
        # 'SS': 'Support Staff',
        # 'INTERN': 'Intern'
    }
    position_options = st.selectbox(
        label= "**Filter by Position:**", 
        options=positions_dict.keys(), # ('All', 'Exec', 'CTA', 'TTL', 'APA', 'I', 'VA', 'LA', 'SS')
        index=0, # All
        format_func=lambda x: positions_dict[x],
        key='courtview_selected_position',
        placeholder="Select job position",
        on_change=update_df,
    )

    # Filter by unit_enum[]: 
    units_dict = {
        'All': 'All Units',
        'Exec': 'Executive Staff',
        'GCU': 'GCU, General Crimes',
        'SVU': 'SVU, Special Victims',
        'VCU': 'VCU, Violent Crimes',
        'CSU': 'CSU, Crime Strategies',
        # 'COMBAT': 'COMBAT',
        'Drug': 'Drug Court',
        'FSD': 'Family Support',
        'WARRANT': 'Warrant Desk'
    }
    unit_options = st.selectbox(
        label="**Filter by Assigned Unit:**",
        options=units_dict.keys(), # ('Exec', 'GCU', 'SVU', 'VCU', 'CSU', 'COMBAT', 'Drug', 'FSD')
        index=0, # All
        format_func=lambda x: units_dict[x],
        key='courtview_selected_unit',
        placeholder="Select unit",
        on_change=update_df,
    )

    # Filter by location: 
    locations_dict = {
        'All': 'All Office Locations',
        'Dt-11': 'Downtown, 11th',
        'Dt-10': 'Downtown, 10th',
        # 'Dt-9': 'Downtown Courthouse, 9th floor (COMBAT)',
        'Dt-7M': 'Downtown, 7M',
        'Indy': 'East Jack, Independence',
        'FSD': 'Family Support'
    }
    location_options = st.selectbox(
        label="**Filter by Office Location:**",
        options=locations_dict.keys(), # ('Dt-11', 'Dt-10', 'Dt-9', 'Dt-7M', 'Indy', 'FSD')
        index=0, # All
        format_func=lambda x: locations_dict[x],
        key='courtview_selected_location',
        placeholder="Select office location",
        on_change=update_df,
    )

    # Reset filters 
    refresh = st.button(
        label="Reset Filters",
        key="courtview_filter_reset",
        on_click=reset_filters,
        type="secondary",
        icon="🔄",
    )

    st.write("To securely exit portal, logout or just exit page:")

    # Logout 

    logout = st.button(
        label="Logout",
        key="logout",
        on_click=lambda: st.session_state.clear(), # Clear session state
        type="secondary",
        icon=":material/logout:"
    )

    st.divider()

    st.markdown(
        """
        ***Color Legend:***  
          
        :red-badge[**Executive Staff**]  
        :orange-badge[**Chief Trial Attorneys**]  
        :green-badge[**Trial Team Leaders**]  
        :blue-badge[**Assistant Prosecuting Attorneys**]
        """
    )


# --- Internal Directory HELPER funcs --- 

def configure_badge(row):

    # Only possible st.badge colors: blue, green, orange, red, violet, gray/grey, or primary
    
    # 'Assigned Unit' - 'Exec' / 'GCU' / 'SVU' / 'VCU' / 'CSU' / 'COMBAT' / 'Drug' / 'FSD'
    if row['Assigned Unit']:
        unit = ' / '.join(row['Assigned Unit'])
    else:
        unit = ':red[???]' # N/A 
    
    # Drug Court 
    if 'Drug' in unit:
        unit = unit.replace("Drug", "Drug Court")
    
    # 'Position' - 'Exec' / 'CTA' / 'TTL' / 'APA'
    if row['Position'] == 'Exec':
        if row['Position'] == unit:
            position_badge = f":red-badge[**Executive Staff**]"
        else:
            position_badge = f":red-badge[**Executive Staff - {unit}**]"
    elif row['Position'] == 'CTA':
        position_badge = f":orange-badge[**Chief Trial Attorney - {unit}**]"
    elif row['Position'] == 'TTL':
        position_badge = f":green-badge[**Trial Team Leader - {unit}**]"
    elif row['Position'] == 'APA':
        position_badge = f":blue-badge[**Assistant Prosecuting Attorney - {unit}**]"
    
    return position_badge

def reformat_location(row):

    # 'Office Location' - 'Dt-11' / 'Dt-10' / 'Dt-9' / 'Dt-7M' / 'Indy' / 'FSD'
    if row['Office Location'] == 'Dt-11':
        office_location = "Downtown Courthouse, 11th floor"
    elif row['Office Location'] == 'Dt-10':
        office_location = "Downtown Courthouse, 10th floor"
    elif row['Office Location'] == 'Dt-9':
        office_location = "Downtown Courthouse, 9th floor (COMBAT)"
    elif row['Office Location'] == 'Dt-7M':
        office_location = "Downtown Courthouse, 7M"
    elif row['Office Location'] == 'Indy':
        office_location = "Eastern Jackson Courthouse, Independence"
    elif row['Office Location'] == 'FSD':
        office_location = "Family Support Division"

    return office_location

def reformat_phone_num(phone_num):
    # Handle NaN values or non-string types 
    if not isinstance(phone_num, str) or pd.isna(phone_num):
        return phone_num
    
    # Check length is 10-digits, then reformat 
    if len(phone_num) == 10:
        return f"{phone_num[:3]}-{phone_num[3:6]}-{phone_num[6:]}"
    else:
        return phone_num

def display_attorney(row):

    with st.container():

        col1, col2 = st.columns([1,1.25], gap="small", vertical_alignment="center")

        with col1:
            
            # Headshot Photo (if None, JCPAO logo)
            if row['PhotoID'] is None: 
                st.image(jcpao_logo, width=400)
            else:
                # headshot_path = "JCPAO_headshots/"+row['PhotoID']
                headshot_path = "JCPAO_headshots/" + (str(row['PhotoID']) if pd.notna(row['PhotoID']) else "")
                attorney_headshot = load_photo(headshot_path)
                st.image(attorney_headshot, width=400)

        with col2:

            # Employee Name
            st.header(f"{row['Full Name']}")

            # Job Title
            st.subheader(f"{row['Job Title']}")

            # Position
            position_badge = configure_badge(row)
            st.markdown(position_badge)
            
            # Office Location
            office_location = reformat_location(row)
            st.write(f"**Office Location:** {office_location}")

            # Work Email Address
            st.write(f"**Email Address:** {row['Work Email Address']}")

            # Work Phone Number 
            work_phone = reformat_phone_num(row['Work Phone #'])
            if str(row['Work Phone #']).startswith("816881"):
                st.write(f"**Work Phone:** {work_phone} (ext. {str(row['Work Phone #'])[-4:]})")
            else:
                st.write(f"**Work Phone:** {work_phone}")
            
        st.divider()


# --- Display INTERNAL Directory ---
st.markdown("<h1 style='text-align: center; color: black;'>JCPAO Police Directory</h1>", unsafe_allow_html=True)
st.divider()

def main_directory():

    df = st.session_state.get("courtview_filtered_df", apa_data)

    # Text search
    searched_text = st.text_input(
        "Search attorney name:",
        key="courtview_searched_text",
        # on_change=update_df,
    )

    text_search = st.button(
        "Search",
        icon="🔎",
        on_click=update_df,
        key="courtview_text_search",
    )

    st.divider()

    if df.empty:
        st.info("No attorneys found matching the search criteria.", icon="⚠️")
    else:
        for i, row in df.iterrows():
            display_attorney(row)


def contact_directory():

    # NO Text Search -- ignore 'searched_text' 
    st.session_state["searched_text"] = ""

    df = st.session_state.get("courtview_filtered_df", apa_data)

    # Reformat df
    df = df.sort_values(by=['Last Name'])
    attorney_contacts = df[['Full Name','Work Email Address', 'Work Phone #']].copy()
    attorney_contacts['Work Phone #'] = attorney_contacts['Work Phone #'].apply(reformat_phone_num)
    attorney_contacts.rename(columns={
        'Full Name': 'Attorney Name',
        'Work Email Address': 'Email Address',
        'Work Phone #': 'Phone Number'
    })
    st.dataframe(attorney_contacts, hide_index=True, height=int(35.2 * (len(df) + 1)))

# --- Display directories --- 
if st.session_state['courtview_view'] == 'Main Directory':
    main_directory()
elif st.session_state['courtview_view'] == 'Contact Directory':
    contact_directory()

