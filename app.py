import streamlit as st
import pandas as pd
import requests
import base64
import io

# 🎨 PAGE CONFIGURATION
st.set_page_config(page_title="HFC Admin Dashboard", layout="wide")

# 🔐 GITHUB DATA FETCHING
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

# 🔄 STATE INITIALIZATION
if "logged_in_as" not in st.session_state: st.session_state.logged_in_as = None
if "master_log" not in st.session_state: st.session_state.master_log = []

def main():
    st.title("🛠️ HFC Structural Field-Data Correction System")

    df_c = fetch_from_github("Constriantt.csv")
    df_l = fetch_from_github("Logicc.csv")

    # --- SIDEBAR: LOGIN ---
    with st.sidebar:
        if st.session_state.logged_in_as is None:
            st.subheader("👤 Enumerator Login")
            all_users = sorted(df_c['username'].dropna().unique()) if df_c is not None else []
            user = st.selectbox("Select Username", all_users)
            if st.text_input("Password", type="password") == "1234":
                if st.button("Login"):
                    st.session_state.logged_in_as = "enumerator"
                    st.session_state.user = user
                    st.rerun()

            st.markdown("---")
            st.subheader("👑 Admin Login")
            adm_p = st.text_input("Admin Passcode", type="password")
            if st.button("Enter Admin Dashboard"):
                if adm_p == "admin123": # SET YOUR ADMIN PASSCODE HERE
                    st.session_state.logged_in_as = "admin"
                    st.rerun()
        else:
            if st.button("Logout"): st.session_state.logged_in_as = None; st.rerun()

    # --- ADMIN DASHBOARD ---
    if st.session_state.logged_in_as == "admin":
        st.subheader("📊 Admin Correction Dashboard")
        combined = pd.concat([df_c, df_l])
        
        # 1. ERROR SUMMARY BY ENUMERATOR
        st.write("### 📉 Errors per Enumerator")
        error_counts = combined.groupby('username')['number'].count().reset_index()
        error_counts.columns = ['Enumerator', 'Total Errors']
        st.bar_chart(error_counts.set_index('Enumerator'))
        
        # 2. FULL CORRECTION DATA
        st.write("### 📝 Submitted Corrections")
        if st.session_state.master_log:
            log_df = pd.DataFrame(st.session_state.master_log)
            st.dataframe(log_df, use_container_width=True)
            st.download_button("📥 Download Report", log_df.to_csv(index=False), "corrections.csv")
        else:
            st.info("No corrections submitted yet.")

    # --- ENUMERATOR VIEW ---
    elif st.session_state.logged_in_as == "enumerator":
        # ... (Enumerator logic as previously defined)
        st.write(f"Welcome, {st.session_state.user}. Use your dashboard to fix assigned errors.")

if __name__ == "__main__":
    main()
