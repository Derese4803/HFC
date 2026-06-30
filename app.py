import streamlit as st
import pandas as pd
import requests
import base64
import io
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="HFC Field-Data Correction System", layout="wide")

# --- GITHUB FETCHING FUNCTION (READ-ONLY) ---
def fetch_from_github(filename):
    # Retrieve credentials from .streamlit/secrets.toml
    token = st.secrets["github"]["token"]
    owner = "Derese4803"
    repo = "HFC"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = base64.b64decode(res.json()['content']).decode('utf-8')
        return pd.read_csv(io.StringIO(content))
    else:
        st.error(f"Could not fetch {filename}. Check your path or secrets.")
        return None

# --- INITIALIZATION ---
# (Keep your existing session_state initializations here)

# --- REPLACEMENT FOR UPLOADERS ---
st.markdown("### 📥 Loading Datasets from Secure Repository")
with st.spinner("Fetching data from GitHub..."):
    # Replace these filenames with your exact file names on GitHub
    constraints_df = fetch_from_github("Constriantt.csv")
    logic_df = fetch_from_github("Logicc.csv")

if constraints_df is None and logic_df is None:
    st.error("Failed to load data. Please check your GitHub repository.")
    st.stop()
