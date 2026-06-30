import streamlit as st
import pandas as pd
from database import fetch_file, commit_file
from models import Correction

# --- SETUP ---
st.set_page_config(layout="wide")
if 'corrections' not in st.session_state: st.session_state.corrections = []

# --- AUTH & ADMIN ---
st.sidebar.title("Login / Admin")
user = st.sidebar.text_input("Enumerator Username")
admin_toggle = st.sidebar.checkbox("Admin Mode")
if admin_toggle and st.sidebar.text_input("PIN", type="password") != "9999":
    st.error("Invalid Admin PIN")
    admin_toggle = False

# --- LOAD DATA ---
if st.session_state.get('data') is None:
    token = st.text_input("GitHub Token", type="password")
    if st.button("Connect"):
        st.session_state.data = fetch_file("Constriantt.csv", token)
        st.rerun()
    st.stop()

# --- DASHBOARD LOGIC ---
df = st.session_state.data
corr_df = pd.DataFrame(st.session_state.corrections)

# Split views
pending = df[~df['unique_id'].isin(corr_df['unique_id'] if not corr_df.empty else [])]

tab1, tab2, tab3 = st.tabs(["Pending Corrections", "History", "Performance Stats"])

with tab1:
    st.write(f"Hello {user}, you have {len(pending)} pending tasks.")
    # Implementation of your correction entry form goes here...

with tab3:
    st.subheader("Enumerator Performance Tracker")
    if not corr_df.empty:
        stats = corr_df.groupby('corrected_by').size() / df.groupby('enumerator').size()
        st.bar_chart(stats * 100)
    else:
        st.info("No data to display yet.")

if admin_toggle:
    st.sidebar.markdown("---")
    if st.sidebar.button("Sync to GitHub"):
        commit_file("corrections.csv", "YOUR_TOKEN", corr_df, "Audit update")
