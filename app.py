import streamlit as st
import pandas as pd
import requests
import base64
import io
import os
from datetime import datetime

# 🎨 PAGE CONFIGURATION
st.set_page_config(page_title="HFC Field-Data Correction System", page_icon="🛠️", layout="wide")

# 🔐 GITHUB FETCHING (READ-ONLY)
def fetch_from_github(filename):
    try:
        token = st.secrets["github"]["token"]
        owner = "Derese4803"
        repo = "HFC"
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}?ref=main"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return pd.read_csv(io.StringIO(content))
        else:
            st.warning(f"Could not load {filename} (Status: {res.status_code})")
            return None
    except Exception as e:
        st.error(f"Error connecting to GitHub: {e}")
        return None

# 🔄 INITIALIZE SESSION STATES
if "corrected_errors" not in st.session_state: st.session_state.corrected_errors = set()
if "master_log" not in st.session_state: st.session_state.master_log = []
if "admin_logged_in" not in st.session_state: st.session_state.admin_logged_in = False

# 📥 DATA LOADING
constraints_df = fetch_from_github("Constriantt.csv")
logic_df = fetch_from_github("Logicc.csv")

# ⚙️ SIDEBAR
with st.sidebar:
    st.title("⚙️ System Control Panel")
    if not st.session_state.admin_logged_in:
        if st.text_input("Admin Password", type="password") == "admin123":
            if st.button("Log In"):
                st.session_state.admin_logged_in = True
                st.rerun()
    else:
        st.success("🔓 Admin Mode Active")
        if st.button("Log Out"): st.session_state.admin_logged_in = False; st.rerun()

# 📑 MAIN INTERFACE
st.title("🛠️ HFC Structural Field-Data Correction System")

if constraints_df is None and logic_df is None:
    st.error("Datasets could not be loaded. Please check repository file names and GitHub secrets.")
    st.stop()

# 👥 ENUMERATOR SELECTION
all_users = sorted(list(set(constraints_df['username'].dropna().unique()) | set(logic_df['username'].dropna().unique())))
selected_enum = st.selectbox("Select Your Identifier:", ["-- Select ID --"] + all_users)

if selected_enum == "-- Select ID --": st.stop()

# 🔍 FILTER DATA
user_constraints = constraints_df[constraints_df['username'].astype(str) == selected_enum]
user_logic = logic_df[logic_df['username'].astype(str) == selected_enum]

# 🛠️ PROCESSING WORKFLOW
for idx, row in user_constraints.iterrows():
    key = f"c_{idx}"
    if key in st.session_state.corrected_errors: continue
    with st.expander(f"❌ Error ID: {row.get('unique_id', idx)}"):
        corr_val = st.text_input(f"Correction", key=f"inp_c_{idx}")
        justification = st.text_input(f"Justification", key=f"inp_j_{idx}")
        if st.button("Commit", key=f"btn_c_{idx}"):
            new_row = {'error_type': 'Range', 'username': selected_enum, 'unique_id': row.get('unique_id'), 'corrected_value': corr_val, 'explanation': justification, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            st.session_state.master_log.append(new_row)
            st.session_state.corrected_errors.add(key)
            st.rerun()

# 👑 ADMIN EXPORT
if st.session_state.admin_logged_in:
    if st.session_state.master_log:
        df_log = pd.DataFrame(st.session_state.master_log)
        st.dataframe(df_log)
        st.download_button("📥 Download Master Log", df_log.to_csv(index=False), "log.csv")
