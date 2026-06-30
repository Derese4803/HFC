import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
import base64

# ============================================================================
# CONFIGURATION
# ============================================================================
st.set_page_config(page_title="HFC Data Correction App", layout="wide")

# UPDATED: Point to your correct repository
GITHUB_REPO = "Derese4803/HFC" 
SOURCE_FILE = "Constriantt.csv"  # Ensure this matches your file EXACTLY
LOGIC_FILE = "logic.csv"
OUTPUT_FILE = "corrections_papaya.csv"
ENUMERATOR_PASSWORD = "1234"

# ============================================================================
# GITHUB API HELPERS
# ============================================================================
def fetch_file_from_github(repo, filepath, token):
    url = f"https://api.github.com/repos/{repo}/contents/{filepath}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    
    # Debug helper: If 404, this will help you see what's actually there
    if response.status_code == 404:
        st.error(f"404 Not Found: {filepath} does not exist in {repo}.")
        # List files in root to help user debug
        root_url = f"https://api.github.com/repos/{repo}/contents/"
        root_resp = requests.get(root_url, headers=headers)
        if root_resp.status_code == 200:
            files = [f['name'] for f in root_resp.json()]
            st.write(f"Files found in repository: {files}")
        return None
        
    if response.status_code == 200:
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        return pd.read_csv(io.StringIO(content))
    return None

# ... [Keep your existing styling and session state code here] ...

# ============================================================================
# UI: STEP 1 - CONNECT
# ============================================================================
if 'active_token' not in st.session_state: st.session_state.active_token = ""

st.title("🛠️ HFC Data Correction App")

if st.session_state.constraints_df is None:
    st.subheader("📋 Step 1: Connect to GitHub")
    st.session_state.active_token = st.text_input("Enter your GitHub PAT (Personal Access Token):", type="password")
    
    if st.button("🚀 Pull Data"):
        if not st.session_state.active_token:
            st.error("Please provide a token.")
        else:
            with st.spinner("Fetching files..."):
                c_df = fetch_file_from_github(GITHUB_REPO, SOURCE_FILE, st.session_state.active_token)
                if c_df is not None:
                    st.session_state.constraints_df = c_df
                    # Fetch logic
                    l_df = fetch_file_from_github(GITHUB_REPO, LOGIC_FILE, st.session_state.active_token)
                    st.session_state.logic_df = l_df if l_df is not None else pd.DataFrame()
                    st.success("Successfully connected!")
                    st.rerun()

    # Fallback
    uploaded_file = st.file_uploader("Or upload local CSV if GitHub connection fails", type=["csv"])
    if uploaded_file:
        st.session_state.constraints_df = pd.read_csv(uploaded_file)
        st.rerun()
    st.stop()
