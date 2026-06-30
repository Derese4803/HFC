import streamlit as st
import pandas as pd
import requests
import base64
import io
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="HFC Correction System", layout="wide")

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

# --- STATE ---
if "auth" not in st.session_state: st.session_state.auth = False
if "admin" not in st.session_state: st.session_state.admin = False
if "master_log" not in st.session_state: st.session_state.master_log = []

def main():
    st.title("🛠️ HFC Structural Field-Data Correction System")

    # --- SIDEBAR: AUTH & INSTRUCTIONS ---
    with st.sidebar:
        st.subheader("👤 Enumerator Login")
        user = st.selectbox("Select Username", ["asfaw.m", "henok", "asfaw.f", "abreham", "tigist.p"])
        if st.text_input("Password", type="password") == "1234":
            if st.button("Login"): st.session_state.auth = True; st.session_state.user = user

        st.markdown("---")
        st.subheader("👑 Admin Login")
        adm_u = st.text_input("Admin Username")
        adm_p = st.text_input("Admin Password", type="password")
        if st.button("Access Admin"):
            if adm_u == "admin" and adm_p == "admin123": st.session_state.admin = True

        st.markdown("---")
        st.subheader("📋 Instructions")
        st.write("For Enumerator: Enter password: 1234")
        st.write("For Administrators: View progress and download reports.")

    # --- LOAD DATA ---
    df_c = fetch_from_github("Constriantt.csv")
    df_l = fetch_from_github("Logicc.csv")

    if df_c is None or df_l is None:
        st.error("Data files not found. Check repository naming.")
        return

    # --- DYNAMIC ID DETECTION ---
    def get_id_col(df):
        # Look for common ID names; if none found, use the first column
        for col in ['unique_id', 'id', 'ID', 'FarmerID', 'number']:
            if col in df.columns: return col
        return df.columns[0]

    id_c, id_l = get_id_col(df_c), get_id_col(df_l)

    # --- ENUMERATOR VIEW ---
    if st.session_state.get("auth"):
        st.success(f"Welcome, {st.session_state.user}")
        u_c = df_c[df_c['username'] == st.session_state.user]
        u_l = df_l[df_l['username'] == st.session_state.user]
        
        for idx, row in u_c.iterrows():
            with st.expander(f"Fix Constraint Error ID: {row.get(id_c, idx)}"):
                fix = st.text_input("Correction", key=f"c_{idx}")
                if st.button("Submit Fix", key=f"sb_{idx}"):
                    st.session_state.master_log.append({'user': st.session_state.user, 'id': row.get(id_c), 'fix': fix})
                    st.success("Logged!")

    # --- ADMIN VIEW ---
    if st.session_state.get("admin"):
        st.subheader("👑 High Frequency Check Summary")
        
        # Safe Metric Calculation
        total_errors = len(df_c) + len(df_l)
        unique_farmers = pd.concat([df_c[id_c], df_l[id_l]]).nunique()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Errors", total_errors)
        c2.metric("Unique Farmers", unique_farmers)
        c3.metric("Enumerators Active", pd.concat([df_c['username'], df_l['username']]).nunique())
        
        combined = pd.concat([df_c, df_l])
        st.write("### Error Rates by Enumerator")
        st.bar_chart(combined['username'].value_counts())
        
        if st.session_state.master_log:
            log_df = pd.DataFrame(st.session_state.master_log)
            st.dataframe(log_df)
            st.download_button("📥 Download Master Log", log_df.to_csv(index=False), "master_report.csv")

if __name__ == "__main__":
    main()
