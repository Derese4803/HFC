import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="HFC Data Correction App", layout="wide")
GITHUB_REPO = "Derese4803/HFC"
SOURCE_FILE = "Constriantt.csv"
LOGIC_FILE = "logic.csv"
OUTPUT_FILE = "corrections_papaya.csv"
ENUMERATOR_PASSWORD = "1234"

# --- GITHUB HELPERS ---
def fetch_file_from_github(repo, filepath, token):
    url = f"https://api.github.com/repos/{repo}/contents/{filepath}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        return pd.read_csv(io.StringIO(content))
    return None

# --- INITIALIZATION ---
if 'constraints_df' not in st.session_state: st.session_state.constraints_df = None
if 'is_authenticated' not in st.session_state: st.session_state.is_authenticated = False

# --- UI: STEP 1 - CONNECT ---
if st.session_state.constraints_df is None:
    st.title("🛠️ HFC Data Correction App")
    token = st.text_input("Enter your GitHub Token (with 'repo' scope):", type="password")
    if st.button("Pull Data from GitHub"):
        df = fetch_file_from_github(GITHUB_REPO, SOURCE_FILE, token)
        if df is not None:
            st.session_state.constraints_df = df
            st.session_state.token = token
            st.success("Data Loaded!")
            st.rerun()
        else:
            st.error("Failed to fetch. Verify your token permissions and file name.")
    st.stop()

# --- UI: STEP 2 - DASHBOARD ---
if not st.session_state.is_authenticated:
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    pin = st.text_input("PIN", type="password")
    if st.button("Login"):
        if pin == ENUMERATOR_PASSWORD:
            st.session_state.is_authenticated = True
            st.session_state.user = username
            st.rerun()
else:
    st.write(f"Welcome, {st.session_state.user}!")
    st.dataframe(st.session_state.constraints_df)
    if st.button("Logout"):
        st.session_state.is_authenticated = False
        st.rerun()
