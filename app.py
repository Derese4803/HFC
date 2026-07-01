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

# 🔄 INITIALIZE SHARED STATE
if "logged_in_as" not in st.session_state: st.session_state.logged_in_as = None
if "master_log" not in st.session_state: st.session_state.master_log = []

def main():
    st.title("🛠️ HFC Structural Field-Data Correction System")
    
    df_c = fetch_from_github("Constriantt.csv")
    df_l = fetch_from_github("Logicc.csv")
    
    if df_c is None: st.error("Data not loaded. Check GitHub token/secrets."); return

    # --- SIDEBAR: LOGIN ---
    with st.sidebar:
        if st.session_state.logged_in_as is None:
            st.subheader("👤 Enumerator Login")
            user = st.selectbox("Select Username", sorted(df_c['username'].dropna().unique()))
            if st.text_input("Password", type="password") == "1234":
                if st.button("Login"): st.session_state.logged_in_as = "enumerator"; st.session_state.user = user; st.rerun()
            st.markdown("---")
            st.subheader("👑 Admin Login")
            if st.text_input("Admin Passcode", type="password") == "admin123":
                if st.button("Access Admin"): st.session_state.logged_in_as = "admin"; st.rerun()
        else:
            if st.button("Logout / Reset"): st.session_state.logged_in_as = None; st.session_state.master_log = []; st.rerun()

    # --- SHARED DATA LOGIC ---
    fixed_df = pd.DataFrame(st.session_state.master_log) if st.session_state.master_log else pd.DataFrame(columns=['user', 'number', 'reason', 'fix'])
    combined = pd.concat([df_c, df_l])

    # --- ENUMERATOR VIEW ---
    if st.session_state.logged_in_as == "enumerator":
        st.header(f"👤 Enumerator: {st.session_state.user}")
        u_c = df_c[df_c['username'] == st.session_state.user]
        remaining = u_c[~u_c['number'].isin(fixed_df['number'].tolist())]
        
        st.metric("Total Errors Remaining", len(remaining))
        st.markdown("---")

        for idx, row in remaining.iterrows():
            with st.expander(f"Error ID: {row.get('number')} | Farmer: {row.get('farmer_name')}"):
                c1, c2 = st.columns(2)
                c1.write(f"**Name:** {row.get('farmer_name')}"); c1.write(f"**Phone:** {row.get('phone_number')}")
                c2.write(f"**Woreda:** {row.get('woreda')}"); c2.write(f"**Kebele:** {row.get('kebele')}")
                st.info(f"**Rule:** {row.get('constraint')}"); st.warning(f"**Value:** {row.get('value')}")
                
                reason = st.text_area("Reason for error", key=f"r_{idx}")
                fix = st.text_input("Enter correct value", key=f"f_{idx}")
                if st.button("Submit Fix", key=f"b_{idx}"):
                    st.session_state.master_log.append({'user': st.session_state.user, 'number': row.get('number'), 'reason': reason, 'fix': fix})
                    st.rerun()

    # --- ADMIN VIEW ---
    elif st.session_state.logged_in_as == "admin":
        st.subheader("📊 Admin Correction Dashboard")
        
        # Real-time metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Errors", len(combined))
        c2.metric("Corrected Errors", len(fixed_df))
        c3.metric("Remaining", len(combined) - len(fixed_df))
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 All Data", "✅ Corrected", "📈 Performance", "📊 Statistics"])
        
        with tab1: st.dataframe(combined, use_container_width=True)
        with tab2: 
            st.dataframe(fixed_df, use_container_width=True)
            if not fixed_df.empty: st.download_button("📥 Download Corrected Data", fixed_df.to_csv(index=False), "corrected_data.csv")
        with tab3: 
            if not fixed_df.empty: st.bar_chart(fixed_df['user'].value_counts())
            else: st.info("No corrections yet.")
        with tab4: 
            stats = pd.DataFrame({"Status": ["Fixed", "Remaining"], "Count": [len(fixed_df), len(combined)-len(fixed_df)]}).set_index("Status")
            st.bar_chart(stats)

if __name__ == "__main__":
    main()
