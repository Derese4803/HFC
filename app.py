import streamlit as st
import pandas as pd
import requests
import base64
import io

st.set_page_config(page_title="HFC Admin Dashboard", layout="wide")

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

if "logged_in_as" not in st.session_state: st.session_state.logged_in_as = None
if "master_log" not in st.session_state: st.session_state.master_log = []

def main():
    st.title("🛠️ HFC Structural Field-Data Correction System")
    df_c = fetch_from_github("Constriantt.csv")
    df_l = fetch_from_github("Logicc.csv")

    with st.sidebar:
        if st.session_state.logged_in_as is None:
            st.subheader("👤 Enumerator Login")
            all_users = sorted(df_c['username'].dropna().unique()) if df_c is not None else []
            user = st.selectbox("Select Username", all_users)
            if st.text_input("Password", type="password") == "1234":
                if st.button("Login"): st.session_state.logged_in_as = "enumerator"; st.session_state.user = user; st.rerun()
            st.markdown("---")
            st.subheader("👑 Admin Login")
            adm_p = st.text_input("Admin Passcode", type="password")
            if st.button("Access Admin"):
                if adm_p == "admin123": st.session_state.logged_in_as = "admin"; st.rerun()
        else:
            if st.button("Logout / Reset"): st.session_state.logged_in_as = None; st.session_state.master_log = []; st.rerun()

    if df_c is None: st.error("Data not loaded."); return

    if st.session_state.logged_in_as == "enumerator":
        fixed_ids = [entry.get('number') for entry in st.session_state.master_log if entry.get('number') is not None]
        u_c = df_c[df_c['username'] == st.session_state.user]
        u_c_filtered = u_c[~u_c['number'].isin(fixed_ids)]
        for idx, row in u_c_filtered.iterrows():
            with st.expander(f"Error ID: {row.get('number')}"):
                st.info(f"Rule: {row.get('constraint')}"); st.warning(f"Value: {row.get('value')}")
                reason = st.text_area("Reason", key=f"r_{idx}"); fix = st.text_input("Correction", key=f"f_{idx}")
                if st.button("Submit", key=f"b_{idx}"):
                    st.session_state.master_log.append({'user': st.session_state.user, 'number': row.get('number'), 'reason': reason, 'fix': fix})
                    st.rerun()

    elif st.session_state.logged_in_as == "admin":
        combined = pd.concat([df_c, df_l])
        fixed_df = pd.DataFrame(st.session_state.master_log) if st.session_state.master_log else pd.DataFrame(columns=['user', 'number', 'reason', 'fix'])
        
        st.subheader("📊 Admin Correction Dashboard")
        
        # DOWNLOAD BUTTON
        if not fixed_df.empty:
            st.download_button("📥 Download All Corrected Data", fixed_df.to_csv(index=False), "corrected_data.csv")
        
        summary = pd.DataFrame({'Assigned': combined.groupby('username')['number'].count(), 
                                'Fixed': fixed_df.groupby('user')['number'].count() if not fixed_df.empty else 0}).fillna(0)
        summary['Remaining'] = summary['Assigned'] - summary['Fixed']
        st.dataframe(summary, use_container_width=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 All", "✅ Corrected", "⚠️ Uncorrected", "📈 Performance"])
        with tab1: st.dataframe(combined)
        with tab2: st.dataframe(fixed_df)
        with tab3: st.dataframe(combined[~combined['number'].isin(fixed_df['number'].tolist() if not fixed_df.empty else [])])
        with tab4: 
            if not fixed_df.empty: st.bar_chart(fixed_df['user'].value_counts())

if __name__ == "__main__": main()
