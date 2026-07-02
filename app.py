import streamlit as st
import pandas as pd
import requests
import base64
import io

# 🎨 PAGE CONFIGURATION
st.set_page_config(page_title="HFC Correction System", layout="wide")

# 🔐 GITHUB API FUNCTIONS
def fetch_from_github(filename):
    try:
        token = st.secrets["github"]["token"]
        url = f"https://api.github.com/repos/Derese4803/HFC/contents/{filename}?ref=main"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return pd.read_csv(io.StringIO(content)), res.json()['sha']
        return pd.DataFrame(), None
    except: return pd.DataFrame(), None

def save_to_github(filename, df, sha):
    token = st.secrets["github"]["token"]
    url = f"https://api.github.com/repos/Derese4803/HFC/contents/{filename}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    csv_content = df.to_csv(index=False)
    data = {
        "message": "Update corrections",
        "content": base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    requests.put(url, headers=headers, json=data)

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

def main():
    st.title("🛠️ HFC Structural Field-Data Correction System")
    
    # 1. Fetch data
    df_c, _ = fetch_from_github("Constriantt.csv")
    df_l, _ = fetch_from_github("Logicc.csv")
    fixed_df, sha = fetch_from_github("corrections.csv")
    
    if df_c.empty or df_l.empty: 
        st.error("Data not loaded. Check GitHub token/files."); return

    df_c['error_type'] = 'Consistency Error'
    df_l['error_type'] = 'Logic Error'
    combined = pd.concat([df_c, df_l])
    
    if fixed_df.empty:
        fixed_df = pd.DataFrame(columns=['user', 'number', 'type', 'reason', 'fix'])

    remaining = combined[~combined['number'].isin(fixed_df['number'].tolist())]

    # --- SIDEBAR ---
    if "logged_in_as" not in st.session_state: st.session_state.logged_in_as = None
    with st.sidebar:
        if st.session_state.logged_in_as is None:
            user = st.selectbox("Username", sorted(combined['username'].dropna().unique()))
            if st.button("Login"): st.session_state.update({"logged_in_as": "enumerator", "user": user})
            if st.text_input("Admin Passcode", type="password") == "admin123":
                if st.button("Access Admin"): st.session_state.logged_in_as = "admin"
        elif st.button("Logout"): st.session_state.logged_in_as = None

    # --- ENUMERATOR VIEW ---
    if st.session_state.logged_in_as == "enumerator":
        u_rem = remaining[remaining['username'] == st.session_state.user]
        st.metric("Errors Remaining", len(u_rem))
        for idx, row in u_rem.iterrows():
            with st.expander(f"{row['error_type']} (ID: {row['number']})"):
                reason = st.text_area("Reason", key=f"r_{idx}")
                fix = st.text_input("Correction", key=f"f_{idx}")
                if st.button("Submit Fix", key=f"b_{idx}"):
                    new_fix = pd.DataFrame([{'user': st.session_state.user, 'number': row['number'], 'type': row['error_type'], 'reason': reason, 'fix': fix}])
                    save_to_github("corrections.csv", pd.concat([fixed_df, new_fix], ignore_index=True), sha)
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
        
        st.markdown("---")
        st.write("### 👥 Performance by Enumerator")
        stats = combined.groupby('username')['number'].count().reset_index().rename(columns={'number': 'Assigned'})
        f_stats = fixed_df.groupby('user')['number'].count().reset_index().rename(columns={'number': 'Fixed'})
        final = pd.merge(stats, f_stats, left_on='username', right_on='user', how='left').fillna(0)
        st.dataframe(final, use_container_width=True)
        
        t1, t2, t3, t4 = st.tabs(["📋 All Data", "✅ Corrected", "📈 Performance", "📊 Statistics"])
        with t1: st.dataframe(combined, use_container_width=True)
        with t2: st.dataframe(fixed_df, use_container_width=True)
        with t3: st.bar_chart(fixed_df['user'].value_counts()) if not fixed_df.empty else None
        with t4: st.bar_chart(pd.DataFrame({"Status": ["Fixed", "Remaining"], "Count": [len(fixed_df), len(combined)-len(fixed_df)]}).set_index("Status"))

if __name__ == "__main__":
    main()
