import streamlit as st
import pandas as pd
import requests
import base64
import io
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="HFC System", layout="wide")

# --- GITHUB DATA FETCHING ---
def fetch_from_github(filename):
    try:
        token = st.secrets["github"]["token"]
        url = f"https://api.github.com/repos/Derese4803/HFC/contents/{filename}?ref=main"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return pd.read_csv(io.StringIO(base64.b64decode(res.json()['content']).decode('utf-8')))
        return None
    except: return None

# --- SESSION STATE ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "admin_logged_in" not in st.session_state: st.session_state.admin_logged_in = False
if "master_log" not in st.session_state: st.session_state.master_log = []

def main():
    st.title("🛠️ HFC Field-Data Correction System")
    
    # --- SIDEBAR AUTHENTICATION ---
    with st.sidebar:
        st.subheader("👤 Enumerator Login")
        user = st.selectbox("Select Username", ["-- Select --", "asfaw.m", "henok", "asfaw.f", "abreham", "tigist.p"])
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == "1234":
                st.session_state.authenticated = True
                st.session_state.username = user
            else: st.error("Invalid Password")

        st.markdown("---")
        st.subheader("👑 Admin Login")
        adm_u = st.text_input("Username", key="adm_u")
        adm_p = st.text_input("Password", type="password", key="adm_p")
        if st.button("Access Admin"):
            if adm_u == "admin" and adm_p == "admin123":
                st.session_state.admin_logged_in = True
            else: st.error("Invalid Admin Credentials")

        st.markdown("---")
        st.subheader("📋 Instructions")
        st.write("**For Enumerators:** Select username, enter '1234' to start.")
        st.write("**For Admins:** Use credentials to view full system diagnostics.")

    # --- MAIN VIEW ---
    if st.session_state.authenticated:
        st.write(f"Welcome, {st.session_state.username}")
        # Add your Task loading logic here...
    
    if st.session_state.admin_logged_in:
        st.subheader("👑 High Frequency Check Summary")
        # Load Data
        df_c = fetch_from_github("Constriantt.csv")
        df_l = fetch_from_github("Logicc.csv")
        
        if df_c is not None and df_l is not None:
            combined = pd.concat([df_c, df_l])
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Errors", len(combined))
            col2.metric("Constraint Errors", len(df_c))
            col3.metric("Logic Errors", len(df_l))
            st.bar_chart(combined['username'].value_counts())
            st.dataframe(combined.groupby('username').size().reset_index(name='Errors'))

if __name__ == "__main__":
    main()
