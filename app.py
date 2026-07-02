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
        
        for idx, row in remaining.iterrows():
            error_label = "Consistency Error" if row.get('number') in df_c['number'].values else "Logic Error"
            with st.expander(f"{error_label} (ID: {row.get('number')})"):
                name = row.get('respondent_name') or row.get('farmer_name') or "N/A"
                c1, c2 = st.columns(2)
                c1.write(f"**Name:** {name}")
                c2.write(f"**Rule:** {row.get('constraint')}")
                
                reason = st.text_area("Reason", key=f"r_{idx}")
                fix = st.text_input("Correction", key=f"f_{idx}")
                if st.button("Submit Fix", key=f"b_{idx}"):
                    st.session_state.master_log.append({'user': st.session_state.user, 'number': row.get('number'), 'type': error_label, 'reason': reason, 'fix': fix})
                    st.rerun()

    # --- ADMIN VIEW ---
    elif st.session_state.logged_in_as == "admin":
        st.subheader("📊 Admin Correction Dashboard")
        
        total_errors = len(combined)
        total_corrected = len(fixed_df)
        total_consistency = len(df_c)
        total_logic = len(df_l)
        remaining = total_errors - total_corrected
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: styled_metric("Total Errors", total_errors, "#6c757d")
        with c2: styled_metric("Corrected", total_corrected, "#28a745")
        with c3: styled_metric("Consistency", total_consistency, "#007bff")
        with c4: styled_metric("Logic", total_logic, "#fd7e14")
        with c5: styled_metric("Remaining", remaining, "#dc3545")
        
        st.markdown("---")
        st.dataframe(combined, use_container_width=True)

if __name__ == "__main__":
    main()
