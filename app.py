import streamlit as st
import pandas as pd

# --- CONFIG & STATE ---
st.set_page_config(page_title="ET Papaya HFC System", layout="wide")
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'role' not in st.session_state: st.session_state.role = None
if 'corrections' not in st.session_state: st.session_state.corrections = []

def login_ui():
    st.title("🔐 ET Papaya HFC System")
    with st.expander("📋 Instructions for Enumerators"):
        st.write("1. Select your username.\n2. Enter your 4-digit PIN.\n3. Complete your pending tasks.")
    
    tab1, tab2 = st.tabs(["👤 Enumerator Login", "👑 Admin Login"])
    with tab1:
        user = st.selectbox("Select Username", ["asfaw.m", "henok", "asfaw.f", "abreham", "tigist.p"])
        pw = st.text_input("Password", type="password", key="p1")
        if st.button("Login as Enumerator"):
            if pw == "1234":
                st.session_state.update({'authenticated': True, 'role': 'enumerator', 'user': user})
                st.rerun()
    with tab2:
        admin_pw = st.text_input("Admin Password", type="password", key="p2")
        if st.button("Login as Admin"):
            if admin_pw == "admin_papaya_2026":
                st.session_state.update({'authenticated': True, 'role': 'admin', 'user': 'Admin'})
                st.rerun()

def main():
    if not st.session_state.authenticated:
        login_ui()
        return

    # --- HEADER & LOGOUT ---
    col1, col2 = st.columns([6, 1])
    col1.title(f"🛠️ HFC Suite | {st.session_state.role.capitalize()}")
    if col2.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    # --- DASHBOARD LOGIC ---
    if st.session_state.role == "admin":
        tab_tasks, tab_stats, tab_errors = st.tabs(["📋 Pending Tasks", "👥 Enumerator Statistics", "🎯 Error Type Overview"])
    else:
        tab_tasks, tab_stats, tab_errors = st.tabs(["📋 My Tasks", "👥 My Stats", "🎯 Error Analysis"])

    with tab_tasks:
        st.subheader("Pending Data Corrections")
        # [Insert Data Fetch & Loop Logic Here]

    with tab_stats:
        st.header("👥 Enumerator & Overall Statistics")
        # 💾 DOWNLOAD DATA
        st.sidebar.header("💾 Download Data")
        if st.session_state.corrections:
            corr_df = pd.DataFrame(st.session_state.corrections)
            st.sidebar.download_button("Export Corrections", corr_df.to_csv(index=False), "log.csv")
        
        # Statistics logic
        st.success("Enumerators without errors: All clear!")

    with tab_errors:
        st.header("🎯 Error Type Overview")
        st.subheader("📊 High Frequency Check Summary")
        # [Insert Error Analysis Visualization Here]

if __name__ == "__main__":
    main()
