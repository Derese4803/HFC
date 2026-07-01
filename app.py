import streamlit as st
import pandas as pd
import requests
import base64
import io

st.set_page_config(page_title="HFC Admin Dashboard", layout="wide")

# (Keep your existing fetch_from_github function here)

def main():
    st.title("🛠️ HFC Structural Field-Data Correction System")
    df_c = fetch_from_github("Constriantt.csv")
    df_l = fetch_from_github("Logicc.csv")

    # ... (Sidebar login code remains the same)

    if st.session_state.logged_in_as == "enumerator":
        # ... (Filter logic remains the same)
        for idx, row in u_c_filtered.iterrows():
            with st.expander(f"Error ID: {row.get('number')} | Farmer: {row.get('farmer_name')}"):
                # Farmer Profile
                st.markdown("### 👤 Farmer Information")
                c1, c2 = st.columns(2)
                c1.write(f"**Name:** {row.get('farmer_name')}"); c1.write(f"**Phone:** {row.get('phone_number')}")
                c2.write(f"**Woreda:** {row.get('woreda')}"); c2.write(f"**Kebele:** {row.get('kebele')}")
                st.markdown("---")
                
                # Error Details
                st.markdown("### 🔍 Error Details")
                st.info(f"**Constraint:** {row.get('constraint')}"); st.warning(f"**Value:** {row.get('value')}")
                
                # Action
                reason = st.text_area("Reason for error", key=f"r_{idx}")
                fix = st.text_input("Correct value", key=f"f_{idx}")
                if st.button("Submit", key=f"b_{idx}"):
                    st.session_state.master_log.append({'user': st.session_state.user, 'number': row.get('number'), 'reason': reason, 'fix': fix})
                    st.rerun()

    # ... (Keep existing Admin logic)

if __name__ == "__main__": main()
