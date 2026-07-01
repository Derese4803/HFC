import streamlit as st
import pandas as pd
import requests
import base64
import io

# 🎨 PAGE CONFIGURATION
st.set_page_config(page_title="HFC Correction System", layout="wide")

# 🔐 GITHUB DATA FETCHING
def fetch_from_github(filename):
    try:
        token = st.secrets["github"]["token"]
        url = f"https://api.github.com/repos/Derese4803/HFC/contents/{filename}?ref=main"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return pd.read_csv(io.StringIO(base64.b64decode(res.json()['content']).decode('utf-8')))
        return None
    except: return None

# 🔄 INITIALIZE STATE
if "logged_in_as" not in st.session_state: st.session_state.logged_in_as = None
if "master_log" not in st.session_state: st.session_state.master_log = []

def main():
    st.title("🛠️ HFC Structural Field-Data Correction System")

    df_c = fetch_from_github("Constriantt.csv")
    df_l = fetch_from_github("Logicc.csv")

    # --- SIDEBAR: LOGIN ---
    with st.sidebar:
        if st.session_state.logged_in_as is None:
            st.subheader("👤 Enumerator Login")
            all_users = sorted(df_c['username'].dropna().unique()) if df_c is not None else []
            user = st.selectbox("Select Username", all_users)
            if st.text_input("Password", type="password") == "1234":
                if st.button("Login"):
                    st.session_state.logged_in_as = "enumerator"
                    st.session_state.user = user
                    st.rerun()
            
            st.markdown("---")
            st.subheader("👑 Admin Login")
            adm_p = st.text_input("Admin Passcode", type="password")
            if st.button("Access Admin"):
                if adm_p == "admin123":
                    st.session_state.logged_in_as = "admin"
                    st.rerun()
        else:
            if st.button("Logout / Reset"): 
                st.session_state.logged_in_as = None
                st.session_state.master_log = []
                st.rerun()

    if df_c is None:
        st.error("Data not loaded. Check GitHub token/filename."); return

    # --- ENUMERATOR VIEW ---
    if st.session_state.logged_in_as == "enumerator":
        st.success(f"Welcome, {st.session_state.user}")
        
        fixed_ids = [entry.get('number') for entry in st.session_state.master_log if entry.get('number') is not None]
        u_c = df_c[df_c['username'] == st.session_state.user]
        u_c_filtered = u_c[~u_c['number'].isin(fixed_ids)]
        
        st.subheader(f"📋 You have {len(u_c_filtered)} errors remaining")
        
        for idx, row in u_c_filtered.iterrows():
            with st.expander(f"Error ID: {row.get('number')} | Variable: {row.get('variable')}"):
                st.markdown("### 🔍 Error Details")
                st.info(f"**Constraint Rule:** {row.get('constraint')}")
                st.warning(f"**Current Recorded Value:** {row.get('value')}")
                
                st.markdown("---")
                reason = st.text_area("Reason for error", placeholder="Please explain why this error happened...", key=f"reason_{idx}")
                fix = st.text_input(f"Enter correct value for {row.get('variable')}", key=f"fix_{idx}")
                
                if st.button("Submit Fix", key=f"btn_{idx}"):
                    st.session_state.master_log.append({
                        'user': st.session_state.user, 
                        'number': row.get('number'), 
                        'variable': row.get('variable'),
                        'reason': reason,
                        'fix': fix
                    })
                    st.rerun()

    # --- ADMIN VIEW ---
    elif st.session_state.logged_in_as == "admin":
        st.subheader("📊 Admin Correction Dashboard")
        combined = pd.concat([df_c, df_l])
        
        tab1, tab2, tab3 = st.tabs(["📋 All Data", "✅ Correction Data", "⚠️ Uncorrected Data"])
        
        with tab1:
            st.write("### Total Raw Error Data")
            st.dataframe(combined, use_container_width=True)
            
        with tab2:
            st.write("### Submitted Corrections")
            if st.session_state.master_log:
                log_df = pd.DataFrame(st.session_state.master_log)
                st.dataframe(log_df, use_container_width=True)
                st.download_button("📥 Download Corrected Data", log_df.to_csv(index=False), "corrected_data.csv")
            else:
                st.info("No corrections submitted yet.")
                
        with tab3:
            st.write("### Remaining Uncorrected Errors")
            fixed_ids = [entry.get('number') for entry in st.session_state.master_log]
            uncorrected = combined[~combined['number'].isin(fixed_ids)]
            st.dataframe(uncorrected, use_container_width=True)

if __name__ == "__main__":
    main()
