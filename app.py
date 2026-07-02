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

# 🟦 METRIC BOX FUNCTION
def styled_metric(label, value, bg_color):
    st.markdown(
        f"""
        <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; text-align: center; color: white; border: 1px solid #ddd;">
            <h4 style="margin: 0; color: white; font-size: 14px;">{label}</h4>
            <h2 style="margin: 0; color: white;">{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

# 🔄 INITIALIZE SHARED STATE
if "logged_in_as" not in st.session_state: st.session_state.logged_in_as = None
if "master_log" not in st.session_state: st.session_state.master_log = []

def main():
    st.title("🛠️ HFC Structural Field-Data Correction System")
    
    df_c = fetch_from_github("Constriantt.csv")
    df_l = fetch_from_github("Logicc.csv")
    
    if df_c is None or df_l is None: 
        st.error("Data not loaded. Check GitHub token/files."); return

    # --- PERMANENTLY LABEL DATA TYPES ---
    df_c['error_type'] = 'Consistency Error'
    df_l['error_type'] = 'Logic Error'
    combined = pd.concat([df_c, df_l])

    # --- SIDEBAR: LOGIN ---
    with st.sidebar:
        if st.session_state.logged_in_as is None:
            st.subheader("👤 Login")
            user = st.selectbox("Username", sorted(combined['username'].dropna().unique()))
            if st.text_input("Password", type="password") == "1234":
                if st.button("Login"): 
                    st.session_state.logged_in_as = "enumerator"
                    st.session_state.user = user
                    st.rerun()
            st.markdown("---")
            if st.text_input("Admin Passcode", type="password") == "admin123":
                if st.button("Access Admin"): 
                    st.session_state.logged_in_as = "admin"
                    st.rerun()
        else:
            if st.button("Logout"): 
                st.session_state.logged_in_as = None
                st.rerun()

    # --- SHARED DATA LOGIC ---
    fixed_df = pd.DataFrame(st.session_state.master_log)
    remaining = combined[~combined['number'].isin(fixed_df['number'].tolist())]

    # --- ENUMERATOR VIEW ---
    if st.session_state.logged_in_as == "enumerator":
        st.header(f"👤 Enumerator: {st.session_state.user}")
        u_rem = remaining[remaining['username'] == st.session_state.user]
        st.metric("Errors Remaining", len(u_rem))
        
        for idx, row in u_rem.iterrows():
            with st.expander(f"{row['error_type']} (ID: {row['number']})"):
                name = row.get('respondent_name') or row.get('farmer_name') or "N/A"
                st.write(f"**Name:** {name}")
                st.info(f"**Rule:** {row['constraint']}")
                reason = st.text_area("Reason", key=f"r_{idx}")
                fix = st.text_input("Correction", key=f"f_{idx}")
                if st.button("Submit Fix", key=f"b_{idx}"):
                    st.session_state.master_log.append({'user': st.session_state.user, 'number': row['number'], 'type': row['error_type'], 'reason': reason, 'fix': fix})
                    st.rerun()

    # --- ADMIN VIEW ---
    elif st.session_state.logged_in_as == "admin":
        st.subheader("📊 Admin Correction Dashboard")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: styled_metric("Total", len(combined), "#6c757d")
        with c2: styled_metric("Fixed", len(fixed_df), "#28a745")
        with c3: styled_metric("Consistency", len(df_c), "#007bff")
        with c4: styled_metric("Logic", len(df_l), "#fd7e14")
        with c5: styled_metric("Remaining", len(remaining), "#dc3545")
        st.dataframe(combined, use_container_width=True)

if __name__ == "__main__":
    main()
