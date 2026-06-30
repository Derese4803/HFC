import streamlit as st
import pandas as pd
import requests
import base64
import io
from datetime import datetime

# 🎨 PAGE CONFIGURATION
st.set_page_config(page_title="HFC Correction System", layout="wide")

# 🔐 GITHUB DATA FETCHING (READ-ONLY)
def fetch_from_github(filename):
    try:
        token = st.secrets["github"]["token"]
        url = f"https://api.github.com/repos/Derese4803/HFC/contents/{filename}?ref=main"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return pd.read_csv(io.StringIO(base64.b64decode(res.json()['content']).decode('utf-8')))
        return None
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return None

# 🛠️ HELPER: DYNAMIC ID DETECTION
def get_id_col(df):
    for col in ['unique_id', 'id', 'ID', 'number', 'farmer_id']:
        if col in df.columns: return col
    return df.columns[0]

# 🔄 STATE INITIALIZATION
if "logged_in_as" not in st.session_state: st.session_state.logged_in_as = None
if "user" not in st.session_state: st.session_state.user = None
if "master_log" not in st.session_state: st.session_state.master_log = []

def main():
    st.title("🛠️ HFC Structural Field-Data Correction System")

    # --- SIDEBAR: LOGIN & INSTRUCTIONS ---
    with st.sidebar:
        if st.session_state.logged_in_as is None:
            st.subheader("👤 Enumerator Login")
            # Automatically fetch users from CSV
            df_temp = fetch_from_github("Constriantt.csv")
            users = sorted(df_temp['username'].dropna().unique()) if df_temp is not None else []
            user = st.selectbox("Select Username", users)
            if st.text_input("Password", type="password") == "1234":
                if st.button("Login"):
                    st.session_state.logged_in_as = "enumerator"
                    st.session_state.user = user
                    st.rerun()

            st.markdown("---")
            st.subheader("👑 Admin Login")
            adm_u = st.text_input("Admin Username")
            adm_p = st.text_input("Admin Password", type="password")
            if st.button("Access Admin"):
                if adm_u == "admin" and adm_p == "admin123":
                    st.session_state.logged_in_as = "admin"
                    st.rerun()
        else:
            if st.button("Logout"):
                st.session_state.logged_in_as = None
                st.rerun()

    # --- LOAD DATA ---
    df_c = fetch_from_github("Constriantt.csv")
    df_l = fetch_from_github("Logicc.csv")

    if df_c is None or df_l is None:
        st.warning("Data loading... please check GitHub repository connectivity.")
        return

    # --- ENUMERATOR VIEW ---
    if st.session_state.logged_in_as == "enumerator":
        st.success(f"Welcome, {st.session_state.user}")
        u_c = df_c[df_c['username'] == st.session_state.user]
        id_c = get_id_col(df_c)
        
        st.subheader(f"📋 You have {len(u_c)} errors to fix")
        for idx, row in u_c.iterrows():
            with st.expander(f"Error in {row.get('variable', 'Unknown')} (ID: {row.get(id_c, idx)})"):
                st.write(f"**Issue:** {row.get('constraint', 'N/A')}")
                fix = st.text_input("Enter Correction", key=f"fix_{idx}")
                if st.button("Submit Fix", key=f"btn_{idx}"):
                    st.session_state.master_log.append({'user': st.session_state.user, 'id': row.get(id_c), 'fix': fix})
                    st.success("Correction saved to local session!")

    # --- ADMIN VIEW ---
    elif st.session_state.logged_in_as == "admin":
        st.subheader("👑 High Frequency Check Summary")
        id_c, id_l = get_id_col(df_c), get_id_col(df_l)
        
        combined = pd.concat([df_c, df_l])
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Errors", len(combined))
        c2.metric("Unique Farmers", combined[id_c].nunique())
        c3.metric("Enumerators Active", combined['username'].nunique())
        
        st.write("### Error Rates by Enumerator")
        st.bar_chart(combined['username'].value_counts())
        
        if st.session_state.master_log:
            log_df = pd.DataFrame(st.session_state.master_log)
            st.dataframe(log_df)
            st.download_button("📥 Download Master Report", log_df.to_csv(index=False), "master_report.csv")

if __name__ == "__main__":
    main()
