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
            user = st.selectbox("Select Username", sorted(df_c['username'].dropna().unique()))
            if st.text_input("Password", type="password") == "1234":
                if st.button("Login"): st.session_state.logged_in_as = "enumerator"; st.session_state.user = user; st.rerun()
            if st.text_input("Admin Passcode", type="password") == "admin123":
                if st.button("Access Admin"): st.session_state.logged_in_as = "admin"; st.rerun()
        else:
            if st.button("Logout"): st.session_state.logged_in_as = None; st.rerun()

    if df_c is None: st.error("Data not loaded."); return

    fixed_df = pd.DataFrame(st.session_state.master_log) if st.session_state.master_log else pd.DataFrame(columns=['user', 'number', 'reason', 'fix'])

    if st.session_state.logged_in_as == "enumerator":
        u_c = df_c[df_c['username'] == st.session_state.user]
        remaining = u_c[~u_c['number'].isin(fixed_df['number'].tolist())]
        st.metric("Errors Remaining", len(remaining))
        for idx, row in remaining.iterrows():
            with st.expander(f"Error ID: {row.get('number')}"):
                if st.button("Submit Fix", key=f"b_{idx}"):
                    st.session_state.master_log.append({'user': st.session_state.user, 'number': row.get('number')})
                    st.rerun()

    elif st.session_state.logged_in_as == "admin":
        st.subheader("📊 Admin Correction Dashboard")
        total_c, total_l = len(df_c), len(df_l)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Errors", total_c + total_l)
        c2.metric("Consistency", total_c)
        c3.metric("Logic Errors", total_l)
        c4.metric("Remaining", (total_c + total_l) - len(fixed_df))
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 All", "✅ Corrected", "📈 Performance", "📊 Stats"])
        with tab1: st.dataframe(pd.concat([df_c, df_l]))
        with tab2: st.dataframe(fixed_df); st.download_button("Download", fixed_df.to_csv(), "data.csv") if not fixed_df.empty else None
        with tab3: st.bar_chart(fixed_df['user'].value_counts()) if not fixed_df.empty else None
        with tab4: st.bar_chart(pd.DataFrame({"Status": ["Fixed", "Remaining"], "Count": [len(fixed_df), (total_c+total_l)-len(fixed_df)]}).set_index("Status"))

if __name__ == "__main__": main()
