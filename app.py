import streamlit as st
import pandas as pd
from database import fetch_file, commit_file

st.set_page_config(page_title="HFC Correction App", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    .farmer-card { background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 10px; }
    .progress-bar { height: 12px; background: #eee; border-radius: 6px; overflow: hidden; margin: 15px 0; }
    .progress-fill { height: 100%; background: #4CAF50; transition: width 0.5s; }
    </style>
""", unsafe_allow_html=True)

if 'corrections' not in st.session_state: st.session_state.corrections = []

st.title("🛠️ HFC Data Correction Dashboard")

# --- DATA LOAD ---
token = st.sidebar.text_input("GitHub Token", type="password")
if st.session_state.get('data') is None and token:
    if st.sidebar.button("Fetch Data"):
        st.session_state.data = fetch_file("Constriantt.csv", token)
        st.rerun()

if st.session_state.get('data') is not None:
    df = st.session_state.data
    user = st.sidebar.selectbox("Select Your Username", df['enumerator'].unique())
    
    # --- METRICS & PROGRESS ---
    user_data = df[df['enumerator'] == user]
    corrected = [c for c in st.session_state.corrections if c['corrected_by'] == user]
    pct = (len(corrected) / len(user_data) * 100) if len(user_data) > 0 else 0
    
    st.markdown(f"**Completion Progress for {user}:**")
    st.markdown(f'<div class="progress-bar"><div class="progress-fill" style="width: {pct}%"></div></div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Errors", len(user_data))
    c2.metric("Fixed", len(corrected))
    c3.metric("Remaining", len(user_data) - len(corrected))

    # --- PENDING CARDS ---
    st.subheader("📋 Pending Tasks")
    pending = user_data[~user_data['unique_id'].isin([c['unique_id'] for c in corrected])]
    
    for _, row in pending.iterrows():
        with st.container():
            st.markdown(f'<div class="farmer-card"><b>ID: {row["unique_id"]}</b> - Issue: {row["constraint"]}</div>', unsafe_allow_html=True)
            if st.button(f"Fix {row['unique_id']}", key=row['unique_id']):
                # Correction form appears here
                st.session_state.target = row['unique_id']
    
    # --- ADMIN EXPORT ---
    if st.sidebar.checkbox("Admin Access"):
        if st.sidebar.button("Sync All to GitHub"):
            commit_file("corrections.csv", token, pd.DataFrame(st.session_state.corrections), "Audit update")
