import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
import base64
from typing import Tuple, Optional, Dict, List

# --- CONFIGURATION ---
st.set_page_config(page_title="HFC Correction Dashboard", layout="wide")

GITHUB_OWNER = "Derese4803"
GITHUB_REPO = "HFC"
ENUMERATOR_PASSWORD = "1234"
ADMIN_PASSWORD = "admin_papaya_2026"
VALID_ENUMERATORS = ["asfaw.m", "henok", "asfaw.f", "abreham", "tigist.p"]

# --- INITIALIZATION ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'all_corrections_data' not in st.session_state: st.session_state.all_corrections_data = {}

# --- GITHUB UTILS ---
def get_headers():
    token = st.secrets.get("github", {}).get("token")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def fetch_file(filename):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{filename}"
    res = requests.get(url, headers=get_headers())
    if res.status_code == 200:
        content = base64.b64decode(res.json()['content']).decode('utf-8')
        return pd.read_csv(io.StringIO(content))
    return None

# --- UI & LOGIC ---
def login_screen():
    st.title("🔐 HFC Correction Dashboard")
    tab1, tab2 = st.tabs(["👤 Enumerator Login", "👑 Admin Login"])
    with tab1:
        user = st.selectbox("Select Username", VALID_ENUMERATORS)
        if st.text_input("Password", type="password") == ENUMERATOR_PASSWORD:
            if st.button("Login as Enumerator"):
                st.session_state.update({'authenticated': True, 'role': 'enumerator', 'user': user})
                st.rerun()
    with tab2:
        if st.text_input("Admin Password", type="password") == ADMIN_PASSWORD:
            if st.button("Login as Admin"):
                st.session_state.update({'authenticated': True, 'role': 'admin', 'user': 'Administrator'})
                st.rerun()

def main():
    if not st.session_state.authenticated:
        login_screen()
        return

    st.title("🛠️ HFC Correction Dashboard")
    
    # Data Loading
    if 'data' not in st.session_state:
        with st.spinner("Fetching data from secure repository..."):
            st.session_state.data = fetch_file("constraints_papaya.csv")
    
    # Sidebar
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.user}**")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
        st.divider()
        st.header("💾 Download Data")
        if st.button("Export Corrections"):
            st.download_button("Download CSV", pd.DataFrame(st.session_state.all_corrections_data).to_csv(), "report.csv")

    # Tabs
    t1, t2, t3 = st.tabs(["📋 Pending Tasks", "👥 Statistics", "🎯 Error Overview"])
    
    with t1:
        st.write("Processing pending corrections for:", st.session_state.user)
        # Add your task iteration logic here
        
    with t2:
        st.header("👥 Enumerator & Overall Statistics")
        st.success("Enumerators without errors: All clear!")
        
    with t3:
        st.header("🎯 Error Type Overview")
        st.subheader("📊 High Frequency Check Summary")

if __name__ == "__main__":
    main()
