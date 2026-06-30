import streamlit as st
import pandas as pd
from datetime import datetime
import io
import re
import requests
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="ET Papaya HFC System", layout="wide")

# --- DATA LOAD & UTILS ---
# (Include your helper functions: get_unique_id_column, get_farmer_name_column, etc. here)
# ... [Insert your helper functions from previous step] ...

def main():
    # --- AUTHENTICATION ---
    if not st.session_state.get('is_authenticated'):
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if user in VALID_ENUMERATORS and password == ENUMERATOR_PASSWORD:
                st.session_state.is_authenticated = True
                st.session_state.selected_enumerator = user
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # --- MAIN APP UI ---
    st.title("🌾 ET Papaya Data Correction")
    
    # Load Data (with caching)
    constraints_df, logic_df = load_data_from_github()
    
    # --- STATS DASHBOARD ---
    stats_df = get_enumerator_statistics(constraints_df, logic_df)
    current_enum_stats = stats_df[stats_df['Username'] == st.session_state.selected_enumerator]
    
    # Visual Progress Indicator
    if not current_enum_stats.empty:
        total = current_enum_stats['Total Errors'].iloc[0]
        solved = current_enum_stats['Solved'].iloc[0]
        render_progress_bar(solved, total)

    # --- PENDING WORKSPACE ---
    tab1, tab2 = st.tabs(["📝 Pending Tasks", "📊 My History"])
    
    with tab1:
        # Filter logic to show only user's assigned errors
        user_constraints = constraints_df[constraints_df['username'] == st.session_state.selected_enumerator]
        
        for idx, row in user_constraints.iterrows():
            unique_id = row[get_unique_id_column(constraints_df)]
            error_key = f"constraint_{unique_id}_{row['variable']}"
            
            # Use expander for mobile-friendly interface
            with st.expander(f"Task: {unique_id} - {row['variable']}"):
                render_farmer_header(
                    row.get('farmer_name', 'Unknown'), 
                    row.get('phone_no', 'N/A'),
                    row.get('woreda', 'N/A'), row.get('kebele', 'N/A'), row.get('village', 'N/A'),
                    error_count=1
                )
                render_constraint_error(row, error_key, get_unique_id_column(constraints_df))

        if st.button("Submit All Corrections"):
            is_valid, missing, comp, tot = validate_corrections()
            if is_valid:
                # Prepare and Save
                corr_df = pd.DataFrame([v for v in st.session_state.all_corrections_data.values()])
                if save_corrections_to_github(corr_df):
                    st.success("Successfully pushed to GitHub!")
            else:
                st.error(f"Missing explanations for: {', '.join(missing)}")

    with tab2:
        st.subheader("Your Corrections")
        # Display history from session state
        if st.session_state.all_corrections_data:
            st.write(pd.DataFrame([v for v in st.session_state.all_corrections_data.values()]))

if __name__ == "__main__":
    main()
