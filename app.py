import streamlit as st
import pandas as pd
import requests
import base64
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="HFC Correction Dashboard", layout="wide")

GITHUB_OWNER = "Derese4803"
GITHUB_REPO = "HFC"
# Ensure your token is in .streamlit/secrets.toml
GITHUB_TOKEN = st.secrets["github"]["token"]

# --- GITHUB UTILS ---
def get_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def fetch_file(filename):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{filename}"
    res = requests.get(url, headers=get_headers())
    if res.status_code == 200:
        content = base64.b64decode(res.json()['content']).decode('utf-8')
        return pd.read_csv(io.StringIO(content))
    else:
        st.error(f"Error {res.status_code}: Could not fetch {filename}")
        return None

# --- INITIALIZATION ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False

# --- AUTHENTICATION ---
def login():
    st.title("🔐 HFC Correction Dashboard")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if pw == "1234": # Add your logic here
            st.session_state.authenticated = True
            st.session_state.user = user
            st.rerun()

# --- MAIN APP ---
def main():
    if not st.session_state.authenticated:
        login()
        return

    st.title("🛠️ HFC Correction Dashboard")
    
    # Load Data
    if 'data_constraints' not in st.session_state:
        with st.spinner("Fetching data..."):
            st.session_state.data_constraints = fetch_file("Constraintt.csv")
            st.session_state.data_logic = fetch_file("Logicc.csv")

    # App Logic
    tab1, tab2 = st.tabs(["📋 Tasks", "📊 Statistics"])
    
    with tab1:
        if st.session_state.data_constraints is not None:
            st.write("Pending Constraints:")
            st.dataframe(st.session_state.data_constraints)
        
    with tab2:
        if st.session_state.data_logic is not None:
            st.write("System Logic Report:")
            st.dataframe(st.session_state.data_logic)

if __name__ == "__main__":
    main()
