import streamlit as st
import pandas as pd
from database import fetch_file, commit_file

# --- CONFIG & STYLING ---
st.set_page_config(page_title="HFC Professional Dashboard", layout="wide", page_icon="📊")

# --- DATA VALIDATION LOGIC ---
def is_valid_input(val):
    return val and len(str(val).strip()) > 0

# --- APP START ---
if 'corrections' not in st.session_state: st.session_state.corrections = []

st.title("📊 HFC Professional Data Suite")

# --- LOAD DATA ---
token = st.sidebar.text_input("GitHub Token", type="password")
if st.session_state.get('data') is None and token:
    with st.spinner("Syncing with GitHub..."):
        st.session_state.data = fetch_file("Constriantt.csv", token)
        st.rerun()

if st.session_state.get('data') is not None:
    df = st.session_state.data
    # Use your smart column detection logic here...
    user = st.sidebar.selectbox("Active Enumerator", df['enumerator'].unique())
    
    # --- METRICS AREA ---
    user_data = df[df['enumerator'] == user]
    corrected = [c for c in st.session_state.corrections if c['corrected_by'] == user]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Assigned", len(user_data))
    c2.metric("Fixed", len(corrected))
    c3.metric("Remaining", len(user_data) - len(corrected))

    # --- PENDING TASKS (The reliable way) ---
    st.subheader("📝 Pending Tasks")
    pending = user_data[~user_data['unique_id'].astype(str).isin([str(c['unique_id']) for c in st.session_state.corrections])]
    
    for idx, row in pending.iterrows():
        # Unique keys combined with index ensures no collisions
        with st.expander(f"Task: {row['unique_id']} | {row.get('constraint', 'Check Data')}"):
            st.write(f"**Original Value:** {row.get('value', 'N/A')}")
            
            # Input with validation check
            new_val = st.text_input("Corrected Value:", key=f"inp_{row['unique_id']}_{idx}")
            
            if st.button("Confirm Fix", key=f"btn_{row['unique_id']}_{idx}"):
                if is_valid_input(new_val):
                    st.session_state.corrections.append({
                        'unique_id': row['unique_id'], 
                        'corrected_value': new_val, 
                        'corrected_by': user
                    })
                    st.success("Correction logged!")
                    st.rerun()
                else:
                    st.error("Please enter a valid value before confirming.")

    # --- ADMIN EXPORT AREA ---
    if st.sidebar.checkbox("Admin Controls"):
        if st.session_state.corrections:
            corr_df = pd.DataFrame(st.session_state.corrections)
            st.sidebar.download_button("Download All Records", corr_df.to_csv(index=False), "audit_log.csv")
