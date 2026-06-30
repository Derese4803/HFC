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

# --- AUTO-DETECT COLUMN HELPER ---
def get_column(df, options):
    for col in df.columns:
        if col.lower() in [o.lower() for o in options]:
            return col
    return df.columns[0] # Fallback

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
    
    # Smart detection for columns
    user_col = get_column(df, ['enumerator', 'username', 'user', 'enumerator_name'])
    id_col = get_column(df, ['unique_id', 'id', 'farmer_id'])
    
    user = st.sidebar.selectbox("Select Your Username", df[user_col].unique())
    
    # --- METRICS & PROGRESS ---
    user_data = df[df[user_col] == user]
    corrected = [c for c in st.session_state.corrections if c['corrected_by'] == user]
    pct = (len(corrected) / len(user_data) * 100) if len(user_data) > 0 else 0
    
    st.markdown(f"**Progress for {user}:**")
    st.markdown(f'<div class="progress-bar"><div class="progress-fill" style="width: {pct}%"></div></div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Errors", len(user_data))
    c2.metric("Fixed", len(corrected))
    c3.metric("Remaining", len(user_data) - len(corrected))

    # --- PENDING CARDS ---
    st.subheader("📋 Pending Tasks")
    pending = user_data[~user_data[id_col].astype(str).isin([str(c['unique_id']) for c in corrected])]
    
    for _, row in pending.iterrows():
        with st.container():
            st.markdown(f'<div class="farmer-card"><b>ID: {row[id_col]}</b> - Issue: {row.get("constraint", "N/A")}</div>', unsafe_allow_html=True)
            if st.button(f"Fix {row[id_col]}", key=str(row[id_col])):
                st.session_state.target = row[id_col]
    
    # --- ADMIN EXPORT ---
    if st.sidebar.checkbox("Admin Access"):
        if st.sidebar.button("Sync All to GitHub"):
            commit_file("corrections.csv", token, pd.DataFrame(st.session_state.corrections), "Audit update")
