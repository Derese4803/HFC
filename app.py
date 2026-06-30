import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="ET Papaya HFC", layout="wide")

# --- AUTH CONFIG ---
USER_DB = {"asfaw.m": "1234", "henok": "1234", "asfaw.f": "1234", "abreham": "1234", "tigist.p": "1234"}
ADMIN_PW = "admin_papaya_2026"

# --- STATE INITIALIZATION ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user' not in st.session_state: st.session_state.user = None
if 'role' not in st.session_state: st.session_state.role = None

def login_screen():
    st.title("🔐 ET Papaya HFC System")
    
    with st.expander("📋 Instructions for Enumerators"):
        st.write("1. Select your username from the dropdown.\n2. Enter your 4-digit PIN.\n3. Click 'Login' to view your assigned data tasks.")

    tab1, tab2 = st.tabs(["👤 Enumerator Login", "👑 Admin Login"])

    with tab1:
        user = st.selectbox("Select Username", list(USER_DB.keys()))
        pw = st.text_input("Password", type="password", key="p1")
        if st.button("Login as Enumerator"):
            if pw == USER_DB.get(user):
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.role = "enumerator"
                st.rerun()
            else: st.error("Incorrect PIN")

    with tab2:
        pw_admin = st.text_input("Admin Password", type="password", key="p2")
        if st.button("Login as Admin"):
            if pw_admin == ADMIN_PW:
                st.session_state.authenticated = True
                st.session_state.user = "Administrator"
                st.session_state.role = "admin"
                st.rerun()
            else: st.error("Invalid Admin Credentials")

def main():
    if not st.session_state.authenticated:
        login_screen()
        return

    # Sidebar Logout
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.user}**")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    # --- MAIN CONTENT ---
    if st.session_state.role == "admin":
        st.header("👑 Admin Dashboard")
        st.write("Monitor overall progress and download reports here.")
        # [Insert Admin Logic/Charts Here]
        
    else:
        st.header(f"Welcome, {st.session_state.user}")
        st.write("Below are your pending data corrections.")
        # [Insert Enumerator Data Loop Here]

if __name__ == "__main__":
    main()
