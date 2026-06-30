import streamlit as st
import pandas as pd
from database import fetch_file, commit_file

st.set_page_config(page_title="HFC Correction App", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .farmer-card { background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 10px; }
    .progress-bar { height: 12px; background: #eee; border-radius: 6px; overflow: hidden; margin: 15px 0; }
    .progress-fill { height: 100%; background: #4CAF50; transition: width 0.5s; }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_column(df, options):
    for col in df.columns:
        if col.lower() in [o.lower() for o in options]:
            return col
    return df.columns[0]

# --- INITIALIZATION ---
if 'corrections' not in st.session_state: st.session_state.corrections = []

st.title("🛠️ HFC Data Correction Dashboard")

# --- DATA LOAD ---
token = st.sidebar.text_input("GitHub Token", type="password")
if st.session_state.get('data') is None and token:
    if st.sidebar.button("Fetch Data"):
        try:
            st.session_state.data = fetch_file("Constriantt.csv", token)
            st.rerun()
        except Exception as e:
            st.error(f"Error fetching file: {e}")

if st.session_state.get('data') is not None:
    df = st.session_state.data
    user_col = get_column(df, ['enumerator', 'username', 'user', 'enumerator_name'])
    id_col = get_column(df, ['unique_id', 'id', 'farmer_id'])
    
    # --- ENUMERATOR SELECTION ---
    user = st.sidebar.selectbox("Select Your Username", df[user_col].unique())
    
    # --- METRICS & PROGRESS ---
    user_data = df[df[user_col] == user]
    corrected = [c for c in st.session_state.corrections if c['corrected_by'] == user]
    pct = (len(corrected) / len(user_data) * 100) if len(user_data) > 0 else 0
    
    st.markdown(f"**Progress for {user}:**")
    st.markdown(f'<div class="progress-bar"><div class="progress-fill" style="width: {pct}%"></div></div>', unsafe_allow_html=True)
    
    # --- PENDING TASKS ---
    st.subheader("📋 Pending Tasks")
    # Identify items not yet in corrections
    pending = user_data[~user_data[id_col].astype(str).isin([str(c['unique_id']) for c in st.session_state.corrections])]
    pending = pending.reset_index(drop=True)
    
    for idx, row in pending.iterrows():
        with st.container():
            st.markdown(f'<div class="farmer-card"><b>ID: {row[id_col]}</b> - Issue: {row.get("constraint", "N/A")}</div>', unsafe_allow_html=True)
            # UNIQUE KEY FIX: Used idx to ensure button is distinct
            if st.button(f"Fix ID {row[id_col]}", key=f"btn_{row[id_col]}_{idx}"):
                st.session_state.target = row[id_col]
                st.rerun()
    
    # --- CORRECTION ENTRY FORM ---
    if 'target' in st.session_state:
        st.divider()
        st.write(f"### ✏️ Correcting Record: {st.session_state.target}")
        
        with st.form(key="correction_form"):
            val = st.text_input("Enter Corrected Value")
            submit = st.form_submit_button("Save Correction")
            
            if submit:
                st.session_state.corrections.append({
                    'unique_id': st.session_state.target, 
                    'corrected_value': val, 
                    'corrected_by': user
                })
                del st.session_state.target
                st.rerun()
