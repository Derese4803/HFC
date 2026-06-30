import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# 🎨 PAGE CONFIGURATION
st.set_page_config(
    page_title="HFC Field-Data Correction System",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔄 INITIALIZE SESSION STATES FOR STORAGE
if "corrected_errors" not in st.session_state:
    st.session_state.corrected_errors = set()
if "master_log" not in st.session_state:
    st.session_state.master_log = []
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# 🔐 SIDEBAR: AUTHENTICATION & MANAGEMENT
with st.sidebar:
    st.title("⚙️ System Control Panel")
    st.markdown("---")
    
    # Administrative Login
    st.subheader("🔐 Authorization Check")
    if not st.session_state.admin_logged_in:
        admin_user = st.text_input("Admin Username", value="")
        admin_pass = st.text_input("Admin Password", type="password", value="")
        if st.button("Log In as Administrator"):
            if admin_user == "admin" and admin_pass == "admin123":
                st.session_state.admin_logged_in = True
                st.success("Authorized! Executive metrics unlocked.")
                st.rerun()
            else:
                st.error("Invalid credentials.")
    else:
        st.success("🔓 Logged in as Administrator")
        if st.button("Log Out"):
            st.session_state.admin_logged_in = False
            st.rerun()
            
    st.markdown("---")
    st.caption("HFC Field-Data Verification Utility • v2.1")


# 📑 MAIN INTERFACE LAYER
st.title("🛠️ HFC Structural Field-Data Correction System")
st.markdown("Reconcile invalid constraints and system mismatches directly from field reports.")

# Placeholders for dataframes
constraints_df = None
logic_df = None

# 📥 STEP 1: DYNAMIC FILE UPLOADERS (Accepts CSV & XLSX)
st.markdown("### 📥 Step 1: Upload Baseline System Datasets")
st.info("💡 You can upload Excel files (.xlsx) or CSV files (.csv). You may use both files, or just one depending on your audit focus.")

col1, col2 = st.columns(2)
with col1:
    c_file = st.file_uploader("Upload constraints File (Range/Data Types)", type=["csv", "xlsx"], key="local_c_upload")
    if c_file:
        try:
            if c_file.name.endswith('.xlsx'):
                constraints_df = pd.read_excel(c_file)
            else:
                constraints_df = pd.read_csv(c_file)
            st.success(f"Loaded {len(constraints_df)} rows from constraints file.")
        except Exception as e:
            st.error(f"Error parsing constraints file: {e}")

with col2:
    l_file = st.file_uploader("Upload logic File (System Mismatches)", type=["csv", "xlsx"], key="local_l_upload")
    if l_file:
        try:
            if l_file.name.endswith('.xlsx'):
                logic_df = pd.read_excel(l_file)
            else:
                logic_df = pd.read_csv(l_file)
            st.success(f"Loaded {len(logic_df)} rows from logic file.")
        except Exception as e:
            st.error(f"Error parsing logic file: {e}")

# Halt if absolutely no files are provided yet
if constraints_df is None and logic_df is None:
    st.warning("👋 Please upload at least one dataset file above to unlock the enumerator dashboards.")
    st.stop()


# 🗂️ AGGREGATE ENUMERATORS FROM ALL ACTIVE FILES
all_users = set()
if constraints_df is not None and 'username' in constraints_df.columns:
    all_users.update(constraints_df['username'].dropna().unique())
if logic_df is not None and 'username' in logic_df.columns:
    all_users.update(logic_df['username'].dropna().unique())

sorted_enumerators = sorted(list(all_users))


# 👥 STEP 2: ENUMERATOR SELECTION
st.markdown("---")
st.markdown("### 👥 Step 2: Select Your Enumerator Identifier Code")
selected_enum = st.selectbox("Select Your Identifier:", ["-- Select ID --"] + sorted_enumerators)

if selected_enum == "-- Select ID --":
    st.info("👈 Please select your enumerator username from the drop-down menu to view assignments.")
    st.stop()


# 🔍 FILTER THE DATA PATTERNS PER USER
user_constraints = pd.DataFrame()
user_logic = pd.DataFrame()

# Robust string cleaning (lowercasing & stripping trailing white spaces) to eliminate mismatch issues
if constraints_df is not None and 'username' in constraints_df.columns:
    user_constraints = constraints_df[constraints_df['username'].astype(str).str.lower().str.strip() == selected_enum.lower().strip()]

if logic_df is not None and 'username' in logic_df.columns:
    user_logic = logic_df[logic_df['username'].astype(str).str.lower().str.strip() == selected_enum.lower().strip()]

total_pending = len(user_constraints) + len(user_logic)

# Check for completed tasks within current runtime context
completed_count = 0
for idx, row in user_constraints.iterrows():
    if f"c_{idx}" in st.session_state.corrected_errors:
        completed_count += 1
for idx, row in user_logic.iterrows():
    if f"l_{idx}" in st.session_state.corrected_errors:
        completed_count += 1

remaining_tasks = total_pending - completed_count

# Welcome Banner
st.markdown(f"#### 📋 Profile Active Backlog for: `{selected_enum}`")
if remaining_tasks == 0:
    st.balloons()
    st.success("🎉 All clear! No pending verification tasks are currently assigned to this profile.")
else:
    st.warning(f"⏳ You have **{remaining_tasks}** records requiring active data corrections or justifications.")


# 🛠️ STEP 3 & 4: PROCESSING WORKFLOW LAYER
if remaining_tasks > 0:
    st.markdown("---")
    st.markdown("### 📝 Active Backlog Cards")
    
    # Loop through Range Constraints
    if not user_constraints.empty:
        for idx, row in user_constraints.iterrows():
            key = f"c_{idx}"
            if key in st.session_state.corrected_errors:
                continue
                
            # Set up dynamic naming fields based on what columns exist in file
            farmer_name = row.get('respondent_name', row.get('farmer_name', f"ID: {row.get('unique_id', idx)}"))
            var_name = row.get('variable', 'Unknown Field')
            current_val = row.get('value', 'N/A')
            rule_constraint = row.get('constraint', 'No rule logic stated')
            
            with st.expander(f"❌ Range Constraint Error — Farmer: {farmer_name} ({var_name})"):
                st.error(f"**Flagged System Rule Violation:** {rule_constraint}")
                
                col_m1, col_m2 = st.columns(2)
                col_m1.metric(label="Current Value Entered", value=str(current_val))
                col_m2.metric(label="Field Boundary Rule", value=str(rule_constraint))
                
                # Input Corrections Box
                corr_val = st.text_input(f"Enter Corrected Value for {farmer_name}", key=f"input_c_v_{idx}")
                justification = st.text_input(f"Explanation/Justification (Required)", key=f"input_c_j_{idx}")
                
                if st.button("Commit Correction", key=f"btn_c_{idx}"):
                    if not corr_val or not justification:
                        st.error("⚠️ You must fill in both the corrected value and an explicit structural explanation.")
                    else:
                        # Append changes directly into Memory Matrix State
                        new_row = {
                            'error_type': 'Range Constraint',
                            'username': selected_enum,
                            'unique_id': str(row.get('unique_id', row.get('number', idx))),
                            'farmer_name': farmer_name,
                            'variable': var_name,
                            'original_value': current_val,
                            'corrected_value': corr_val,
                            'explanation': justification.strip(),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.master_log.append(new_row)
                        st.session_state.corrected_errors.add(key)
                        
                        # Offline Local Hard-drive Auto-save Dump (Prevents data loss if window closes)
                        pd.DataFrame([new_row]).to_csv(
                            'saved_corrections.csv', 
                            mode='a', 
                            header=not os.path.exists('saved_corrections.csv'), 
                            index=False
                        )
                        st.success("💾 Correction logged and appended onto the hard drive file ('saved_corrections.csv')!")
                        st.rerun()

    # Loop through System Logic Mismatches
    if not user_logic.empty:
        for idx, row in user_logic.iterrows():
            key = f"l_{idx}"
            if key in st.session_state.corrected_errors:
                continue
                
            farmer_name = row.get('respondent_name', row.get('farmer_name', f"ID: {row.get('unique_id', idx)}"))
            var_name = row.get('variable', 'Unknown Mismatch')
            current_val = row.get('value', 0)
            troster_val = row.get('Troster Value', row.get('troster_value', 0))
            
            # Calculate mismatch delta automatically
            try:
                delta = float(current_val) - float(troster_val)
            except:
                delta = "N/A"
                
            with st.expander(f"⚠️ System Mismatch Discrepancy — Farmer: {farmer_name} ({var_name})"):
                st.warning(f"**Discrepancy Warning:** Field Report does not align with core backend Baseline Values.")
                
                col_l1, col_l2, col_l3 = st.columns(3)
                col_l1.metric(label="Your Field Report Value", value=str(current_val))
                col_l2.metric(label="System Record (Troster Value)", value=str(troster_val))
                col_l3.metric(label="Calculated Variance (Delta)", value=str(delta), delta=str(delta) if delta != "N/A" else None)
                
                corr_val = st.text_input(f"Enter Verified Core Value for {farmer_name}", key=f"input_l_v_{idx}")
                justification = st.text_input(f"Explanation/Justification (Required)", key=f"input_l_j_{idx}")
                
                if st.button("Commit Correction", key=f"btn_l_{idx}"):
                    if not corr_val or not justification:
                        st.error("⚠️ You must fill in both the resolved metrics and a verification explanation.")
                    else:
                        new_row = {
                            'error_type': 'System Mismatch (Logic)',
                            'username': selected_enum,
                            'unique_id': str(row.get('unique_id', row.get('number', idx))),
                            'farmer_name': farmer_name,
                            'variable': var_name,
                            'original_value': f"Reported: {current_val} | Troster: {troster_val}",
                            'corrected_value': corr_val,
                            'explanation': justification.strip(),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.master_log.append(new_row)
                        st.session_state.corrected_errors.add(key)
                        
                        # Offline Local Hard-drive Auto-save Dump 
                        pd.DataFrame([new_row]).to_csv(
                            'saved_corrections.csv', 
                            mode='a', 
                            header=not os.path.exists('saved_corrections.csv'), 
                            index=False
                        )
                        st.success("💾 Variance correction logged and written to hard drive ('saved_corrections.csv')!")
                        st.rerun()


# 👑 STEP 5: EXECUTIVE VIEW & DOWNLOAD PANELS (ADMIN SECURED)
st.markdown("---")
st.markdown("### 📥 Step 5: Export System Diagnostics")

if not st.session_state.admin_logged_in:
    st.info("🔒 Administrative View Locked. Authenticate using the **System Control Panel** on the left sidebar to download logs.")
else:
    st.subheader("📊 Session Audit Performance Monitor")
    
    # Merges current active memory state array alongside history items logged directly onto local CSV
    all_logged_corrections = []
    if os.path.exists('saved_corrections.csv'):
        try:
            all_logged_corrections = pd.read_csv('saved_corrections.csv')
        except:
            all_logged_corrections = pd.DataFrame(st.session_state.master_log)
    else:
        all_logged_corrections = pd.DataFrame(st.session_state.master_log)
        
    if len(all_logged_corrections) == 0:
        st.info("No logs found. Once agents start committing audited values, telemetry tables will display here.")
    else:
        st.metric(label="Total Completed Corrections (All-time Local)", value=len(all_logged_corrections))
        st.dataframe(all_logged_corrections, use_container_width=True)
        
        # Download Action Engine Block (Outputs clean CSV structure)
        csv_buffer = all_logged_corrections.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Master Corrections Log (CSV)",
            data=csv_buffer,
            file_name=f"HFC_Finalized_Data_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
