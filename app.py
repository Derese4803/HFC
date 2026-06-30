import streamlit as st
import pandas as pd
import requests
import base64
import io
import os
from datetime import datetime

# 🎨 CONFIGURATION
st.set_page_config(page_title="HFC Correction System", layout="wide")

# 🔐 GITHUB FETCHING
def fetch_from_github(filename):
    try:
        token = st.secrets["github"]["token"]
        url = f"https://api.github.com/repos/Derese4803/HFC/contents/{filename}?ref=main"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return pd.read_csv(io.StringIO(content))
        return None
    except: return None

# 🔄 STATE
if "corrected_errors" not in st.session_state: st.session_state.corrected_errors = set()
if "master_log" not in st.session_state: st.session_state.master_log = []
if "admin_logged_in" not in st.session_state: st.session_state.admin_logged_in = False

# 📥 DATA LOADING
constraints_df = fetch_from_github("Constriantt.csv")
logic_df = fetch_from_github("Logicc.csv")

# ⚙️ SIDEBAR
with st.sidebar:
    st.title("⚙️ Control Panel")
    if not st.session_state.admin_logged_in:
        if st.text_input("Admin Password", type="password") == "admin123":
            if st.button("Log In"): st.session_state.admin_logged_in = True; st.rerun()
    else:
        st.success("🔓 Admin Mode Active")
        if st.button("Log Out"): st.session_state.admin_logged_in = False; st.rerun()

# 📑 MAIN INTERFACE
st.title("🛠️ HFC Structural Field-Data Correction System")

if constraints_df is None or logic_df is None:
    st.error("Data missing. Ensure Constriantt.csv and Logicc.csv are in the repo.")
    st.stop()

# 👥 ENUMERATOR SELECTION
all_users = sorted(list(set(constraints_df['username'].dropna().unique()) | set(logic_df['username'].dropna().unique())))
selected_enum = st.selectbox("Select Your Identifier:", ["-- Select ID --"] + all_users)

if selected_enum != "-- Select ID --":
    # 🔍 FILTER
    u_c = constraints_df[constraints_df['username'] == selected_enum]
    u_l = logic_df[logic_df['username'] == selected_enum]
    
    tab1, tab2 = st.tabs(["📋 My Tasks", "👑 Admin Summary"])
    
    with tab1:
        st.subheader(f"Backlog for {selected_enum}")
        for idx, row in u_c.iterrows():
            with st.expander(f"Constraint Error: {row.get('unique_id', idx)}"):
                val = st.text_input(f"Correction", key=f"c_{idx}")
                just = st.text_input(f"Justification", key=f"j_{idx}")
                if st.button("Submit", key=f"b_c_{idx}"):
                    st.session_state.master_log.append({'username': selected_enum, 'id': row.get('unique_id'), 'fix': val, 'time': datetime.now().strftime('%H:%M:%S')})
                    st.rerun()

    with tab2:
        if st.session_state.admin_logged_in:
            st.subheader("👑 High Frequency Check Summary")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Errors", len(constraints_df) + len(logic_df))
            c2.metric("Constraint", len(constraints_df))
            c3.metric("Logic", len(logic_df))
            c4.metric("Farmers", len(set(constraints_df['unique_id'].tolist() + logic_df['unique_id'].tolist())))
            
            combined = pd.concat([constraints_df, logic_df])
            st.write("### 📊 Error Rate by Enumerator")
            st.bar_chart(combined['username'].value_counts())
            
            st.write("### 📉 Overall Statistics")
            st.dataframe(combined.groupby('username').size().reset_index(name='Total Errors'))
            
            if st.session_state.master_log:
                log_df = pd.DataFrame(st.session_state.master_log)
                st.download_button("📥 Download Master Log", log_df.to_csv(index=False), "final_log.csv")
        else:
            st.warning("🔒 Please login as admin in the sidebar to view metrics.")

if __name__ == "__main__":
    main()
