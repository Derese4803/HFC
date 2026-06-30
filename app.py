import streamlit as st
import pandas as pd
import requests
import base64
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="HFC Correction Dashboard", layout="wide")
GITHUB_OWNER = "Derese4803"
GITHUB_REPO = "HFC"
GITHUB_TOKEN = st.secrets["github"]["token"]

# --- GITHUB UTILS ---
def get_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def fetch_file(filename):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{filename}?ref=main"
    res = requests.get(url, headers=get_headers())
    if res.status_code == 200:
        content = base64.b64decode(res.json()['content']).decode('utf-8')
        return pd.read_csv(io.StringIO(content))
    return None

# --- HELPER: AUTO-DETECT ID COLUMN ---
def get_id_column(df):
    possible_names = ['unique_id', 'id', 'farmer_id', 'ID', 'UUID', 'FarmerID']
    for name in possible_names:
        if name in df.columns:
            return name
    return df.columns[0] # Default to first column

# --- STATE ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'corrections' not in st.session_state: st.session_state.corrections = []

# --- MAIN APP ---
def main():
    if not st.session_state.authenticated:
        st.title("🔐 HFC Login")
        user = st.selectbox("Select Username", ["asfaw.m", "henok", "asfaw.f", "abreham", "tigist.p"])
        if st.text_input("Password", type="password") == "1234":
            if st.button("Login"):
                st.session_state.update({'authenticated': True, 'user': user})
                st.rerun()
        return

    # Load Data
    if 'data' not in st.session_state:
        st.session_state.data = fetch_file("Constriantt.csv")
    
    st.title("🛠️ HFC Correction Dashboard")
    st.sidebar.write(f"User: **{st.session_state.user}**")
    
    df = st.session_state.data
    id_col = get_id_column(df)
    user_tasks = df[df['username'] == st.session_state.user]
    
    tab1, tab2 = st.tabs(["📋 My Tasks", "💾 Download & Progress"])
    
    with tab1:
        st.subheader(f"You have {len(user_tasks)} errors to fix")
        for idx, row in user_tasks.iterrows():
            row_id = row[id_col]
            with st.expander(f"Task ID: {row_id}"):
                st.write(f"**Issue:** {row.get('constraint', 'N/A')}")
                val = st.text_input(f"Correction for {row_id}", key=f"inp_{idx}")
                if st.button("Submit Fix", key=f"btn_{idx}"):
                    st.session_state.corrections.append({'id': row_id, 'fix': val})
                    st.success("Correction logged!")

    with tab2:
        st.header("💾 Download Data")
        if st.session_state.corrections:
            corr_df = pd.DataFrame(st.session_state.corrections)
            st.download_button("Download My Fixes (CSV)", corr_df.to_csv(index=False), "my_corrections.csv")
        st.write(f"Total fixes submitted: {len(st.session_state.corrections)}")

if __name__ == "__main__":
    main()
