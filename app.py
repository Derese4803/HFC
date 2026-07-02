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
    
    if df_c is None or df_l is None: 
        st.error("Data not loaded. Check GitHub token/files."); return

    # --- SIDEBAR: LOGIN ---
    with st.sidebar:
        if st.session_state.logged_in_as is None:
            st.subheader("👤 Enumerator Login")
            user = st.selectbox("Select Username", sorted(df_c['username'].dropna().unique()))
            if st.text_input("Password", type="password") == "1234":
                if st.button("Login"): 
                    st.session_state.logged_in_as = "enumerator"
                    st.session_state.user = user
                    st.rerun()
            st.markdown("---")
            st.subheader("👑 Admin Login")
            if st.text_input("Admin Passcode", type="password") == "admin123":
                if st.button("Access Admin"): 
                    st.session_state.logged_in_as = "admin"
                    st.rerun()
        else:
            if st.button("Logout / Reset"): 
                st.session_state.logged_in_as = None
                st.session_state.master_log = []
                st.rerun()

    # --- SHARED DATA LOGIC ---
    fixed_df = pd.DataFrame(st.session_state.master_log) if st.session_state.master_log else pd.DataFrame(columns=['user', 'number', 'type', 'reason', 'fix'])
    combined = pd.concat([df_c, df_l])

    # --- ENUMERATOR VIEW ---
    if st.session_state.logged_in_as == "enumerator":
        st.header(f"👤 Enumerator: {st.session_state.user}")
        u_c = combined[combined['username'] == st.session_state.user]
        remaining = u_c[~u_c['number'].isin(fixed_df['number'].tolist())]
        
        st.metric("Total Errors Remaining", len(remaining))
        st.markdown("---")

        for idx, row in remaining.iterrows():
            error_label = "Consistency Error" if row.get('number') in df_c['number'].values else "Logic Error"
            with st.expander(f"{error_label} (ID: {row.get('number')})"):
                st.markdown("### 👤 Respondent Profile")
                name_to_show = row.get('respondent_name') or row.get('farmer_name') or "N/A"
                phone_to_show = row.get('phone_no') or row.get('phone_number') or "N/A"
                kebele_to_show = row.get('kebele_name') or row.get('kebele') or "N/A"
                
                c1, c2 = st.columns(2)
                c1.write(f"**Name:** {name_to_show}")
                c1.write(f"**Phone:** {phone_to_show}")
                c2.write(f"**Kebele:** {kebele_to_show}")
                
                st.markdown("---")
                st.markdown("### 🔍 Error Details")
                st.info(f"**Rule:** {row.get('constraint')}")
                st.warning(f"**Current Value:** {row.get('value')}")
                
                reason = st.text_area("Reason for error", key=f"r_{idx}")
                fix = st.text_input("Corrected Value", key=f"f_{idx}")
                if st.button("Submit Fix", key=f"b_{idx}"):
                    st.session_state.master_log.append({'user': st.session_state.user, 'number': row.get('number'), 'type': error_label, 'reason': reason, 'fix': fix})
                    st.rerun()

    # --- ADMIN VIEW ---
    elif st.session_state.logged_in_as == "admin":
        st.subheader("📊 Admin Correction Dashboard")
        
        # Metrics
        total_errors = len(combined)
        total_corrected = len(fixed_df)
        total_consistency = len(df_c)
        total_logic = len(df_l)
        remaining = total_errors - total_corrected
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Errors", total_errors)
        c2.metric("Total Corrected", total_corrected, delta=f"{total_corrected} Fixed")
        c3.metric("Consistency", total_consistency)
        c4.metric("Logic", total_logic)
        c5.metric("Remaining", remaining, delta_color="inverse")
        
        st.markdown("---")
        st.write("### 👥 Performance by Enumerator")
        stats = combined.groupby('username')['number'].count().reset_index()
        stats.columns = ['Enumerator', 'Assigned']
        f_stats = fixed_df.groupby('user')['number'].count().reset_index()
        f_stats.columns = ['Enumerator', 'Fixed']
        final = pd.merge(stats, f_stats, on='Enumerator', how='left').fillna(0)
        final['Remaining'] = final['Assigned'] - final['Fixed']
        st.dataframe(final, use_container_width=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 All Data", "✅ Corrected", "📈 Performance", "📊 Statistics"])
        with tab1: st.dataframe(combined, use_container_width=True)
        with tab2: 
            st.dataframe(fixed_df, use_container_width=True)
            if not fixed_df.empty: st.download_button("📥 Download Corrected Data", fixed_df.to_csv(index=False), "corrected_data.csv")
        with tab3: st.bar_chart(fixed_df['user'].value_counts()) if not fixed_df.empty else None
        with tab4: st.bar_chart(pd.DataFrame({"Status": ["Fixed", "Remaining"], "Count": [len(fixed_df), len(combined)-len(fixed_df)]}).set_index("Status"))

if __name__ == "__main__":
    main()
