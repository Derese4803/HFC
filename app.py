import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
import base64

# ============================================================================
# CONFIGURATION & BRANDING
# ============================================================================

st.set_page_config(
    page_title="HFC Data Correction App",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "HFC Data Correction App v2.0"
    }
)

ENUMERATOR_PASSWORD = "1234"

# GitHub Configuration Details
GITHUB_REPO = "mohammed-seid/hfc-data-private"
SOURCE_FILE = "Constriantt.csv"
OUTPUT_FILE = "corrections_papaya.csv"

# Fetch token safely from Streamlit Secrets or environment variables
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")

# ============================================================================
# STYLING - Mobile-First Design
# ============================================================================

st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 50px;
        font-size: 16px;
        font-weight: 600;
    }
    
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .farmer-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 4px solid #4CAF50;
    }
    
    .farmer-info-row {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-top: 8px;
    }
    
    .farmer-info-item {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 13px;
        color: #555;
    }
    
    .location-badge {
        background: #e3f2fd;
        color: #1565c0;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .error-badge {
        background: #ff6b6b;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .success-badge {
        background: #51cf66;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .login-box {
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    @media (max-width: 768px) {
        .stTextInput, .stNumberInput, .stTextArea {
            margin-bottom: 16px;
        }
        .farmer-info-row {
            flex-direction: column;
            gap: 8px;
        }
    }
    
    .progress-bar {
        height: 8px;
        background: #e0e0e0;
        border-radius: 4px;
        overflow: hidden;
        margin: 16px 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #4CAF50, #8BC34A);
        transition: width 0.3s ease;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'constraints_df' not in st.session_state:
    st.session_state.constraints_df = None
if 'logic_df' not in st.session_state:
    st.session_state.logic_df = None
if 'corrections_list' not in st.session_state:
    st.session_state.corrections_list = []
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False
if 'selected_enumerator' not in st.session_state:
    st.session_state.selected_enumerator = None

# ============================================================================
# GITHUB API INTEGRATION HELPERS
# ============================================================================

def fetch_file_from_github(repo, filepath, token):
    url = f"https://api.github.com/repos/{repo}/contents/{filepath}"
    headers = {"Authorization": f"token {token}"} if token else {}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        return pd.read_csv(io.StringIO(content))
    else:
        st.error(f"Failed to fetch {filepath} from GitHub. Error: {response.status_code}")
        return None

def commit_file_to_github(repo, filepath, token, df, commit_message="Update corrections"):
    url = f"https://api.github.com/repos/{repo}/contents/{filepath}"
    headers = {"Authorization": f"token {token}"}
    
    get_resp = requests.get(url, headers=headers)
    sha = get_resp.json().get('sha') if get_resp.status_code == 200 else None
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    content_encoded = base64.b64encode(csv_buffer.getvalue().encode('utf-8')).decode('utf-8')
    
    data = {
        "message": commit_message,
        "content": content_encoded
    }
    if sha:
        data["sha"] = sha
        
    put_resp = requests.put(url, headers=headers, json=data)
    return put_resp.status_code in [200, 201]

# ============================================================================
# COLUMN DETECTION HELPERS
# ============================================================================

def get_column_by_alternatives(df: pd.DataFrame, alternatives: list, default: str) -> str:
    for col in df.columns:
        if any(alt in col.lower() for alt in alternatives):
            return col
    return default

def find_user_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        if col.lower().strip() in ['username', 'user', 'enumerator', 'enum', 'enumerator_name']:
            return col
    return None

# ============================================================================
# STEP 1: GITHUB CONNECTION / FILE LOADING
# ============================================================================

st.title("🛠️ HFC Data Correction App")

if st.session_state.constraints_df is None:
    st.subheader("📋 Step 1: Connect & Fetch Source Files")
    
    if not GITHUB_TOKEN:
        st.warning("⚠️ GitHub Access Token is missing. Provide it below or save it in Streamlit Secrets.")
        input_token = st.text_input("Enter GitHub Personal Access Token (PAT):", type="password")
        if input_token:
            GITHUB_TOKEN = input_token

    if st.button("🚀 Pull Source Files From GitHub"):
        if not GITHUB_TOKEN:
            st.error("Cannot fetch repository files without a valid GitHub Access Token.")
        else:
            with st.spinner("Fetching dynamic dataset configurations..."):
                fetched_df = fetch_file_from_github(GITHUB_REPO, SOURCE_FILE, GITHUB_TOKEN)
                if fetched_df is not None:
                    st.session_state.constraints_df = fetched_df
                    st.session_state.logic_df = pd.DataFrame()
                    st.success(f"Successfully pulled fresh data structure from {SOURCE_FILE}!")
                    st.rerun()

    st.write("---")
    st.info("💡 Alternatively, you can drop a temporary local file below to override style:")
    c_file = st.file_uploader("Upload Backup Constraints CSV (Local Mirror)", type=["csv"])
    if c_file:
        st.session_state.constraints_df = pd.read_csv(c_file)
        st.session_state.logic_df = pd.DataFrame()
        st.rerun()
        
    st.stop()

# ============================================================================
# DYNAMIC USERNAME AGGREGATION & GATEWAY LOGIN
# ============================================================================

all_users = set()

if st.session_state.constraints_df is not None:
    user_col_c = find_user_column(st.session_state.constraints_df)
    if user_col_c:
        all_users.update(st.session_state.constraints_df[user_col_c].dropna().astype(str).str.strip().unique())

VALID_ENUMERATORS = sorted(list(all_users))

if not st.session_state.is_authenticated:
    st.subheader("🔐 Profile Verification Gate")
    
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        if not VALID_ENUMERATORS:
            st.warning("⚠️ No username column automatically identified. Please type your username manually.")
            user_input = st.text_input("Username").strip()
        else:
            user_input = st.selectbox("Select Your Enumerator Username", [""] + VALID_ENUMERATORS)
            
        pass_input = st.text_input("Security PIN (Default: 1234)", type="password")
        
        if st.button("Access Dashboard"):
            if user_input != "" and pass_input == ENUMERATOR_PASSWORD:
                st.session_state.is_authenticated = True
                st.session_state.selected_enumerator = user_input
                st.rerun()
            else:
                st.error("Invalid Username or Security PIN selection.")
                
        st.markdown('</div>', unsafe_allow_html=True)
        
    if st.button("🗑️ Reset Application / Upload New Files"):
        st.session_state.constraints_df = None
        st.session_state.logic_df = None
        st.rerun()
    st.stop()

# ============================================================================
# ENUMERATOR WORKFLOW PANEL
# ============================================================================

enum_id = st.session_state.selected_enumerator
st.subheader(f"👋 Active Session: `{enum_id}`")

if st.sidebar.button("🚪 Logout Session"):
    st.session_state.is_authenticated = False
    st.session_state.selected_enumerator = None
    st.rerun()

if st.sidebar.button("🔄 Clear Uploads & Start Over"):
    st.session_state.clear()
    st.rerun()

c_df = st.session_state.constraints_df
l_df = st.session_state.logic_df

user_col_c = find_user_column(c_df) or 'username'
c_user = c_df[c_df[user_col_c].astype(str).str.lower().str.strip() == str(enum_id).lower().strip()].copy() if user_col_c in c_df.columns else c_df.copy()

if l_df is not None and not l_df.empty:
    user_col_l = find_user_column(l_df) or 'username'
    l_user = l_df[l_df[user_col_l].astype(str).str.lower().str.strip() == str(enum_id).lower().strip()].copy() if user_col_l in l_df.columns else l_df.copy()
else:
    l_user = pd.DataFrame()

id_col = get_column_by_alternatives(c_user, ['unique_id', 'id', 'farmer_id', 'number'], 'number')
name_col = get_column_by_alternatives(c_user, ['name', 'respondent', 'farmer'], 'respondent_name')
phone_col = get_column_by_alternatives(c_user, ['phone', 'mobile', 'telephone'], 'phone_no')
reason_col = get_column_by_alternatives(c_user, ['constraint', 'reason', 'rule', 'error_message'], 'constraint')

woreda_col = get_column_by_alternatives(c_user, ['woreda', 'district'], 'woreda')
kebele_col = get_column_by_alternatives(c_user, ['kebele'], 'kebele_name')
village_col = get_column_by_alternatives(c_user, ['village', 'gote'], 'village_name')

combined_farmers_index = {}

for idx, row in c_user.iterrows():
    f_id = str(row.get(id_col, idx))
    error_key = f"constraint_{f_id}_{row.get('variable', 'var')}"
    if any(item['key'] == error_key for item in st.session_state.corrections_list):
        continue
    if f_id not in combined_farmers_index:
        combined_farmers_index[f_id] = {'meta': row, 'issues': []}
    combined_farmers_index[f_id]['issues'].append({'type': 'Constraint', 'row': row, 'key': error_key})

for idx, row in l_user.iterrows():
    f_id = str(row.get(id_col, idx))
    error_key = f"logic_{f_id}_{row.get('variable', 'var')}"
    if any(item['key'] == error_key for item in st.session_state.corrections_list):
        continue
    if f_id not in combined_farmers_index:
        combined_farmers_index[f_id] = {'meta': row, 'issues': []}
    combined_farmers_index[f_id]['issues'].append({'type': 'Logic Variance', 'row': row, 'key': error_key})

total_backlog = len(combined_farmers_index)
completed_count = len({item['unique_id'] for item in st.session_state.corrections_list})

total_tasks = total_backlog + completed_count
percentage = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
st.markdown(f"""
    <div class="progress-bar"><div class="progress-fill" style="width: {percentage}%"></div></div>
    <p style="text-align: center; color: #666; font-weight: 600;">{completed_count} Farmers Solved | {total_backlog} Remaining Folders</p>
""", unsafe_allow_html=True)

if total_backlog == 0:
    st.balloons()
    st.success("🎉 Outstanding job! All of your assigned survey issues are corrected.")
else:
    for f_id, context in combined_farmers_index.items():
        meta = context['meta']
        issues = context['issues']
        
        f_name = str(meta.get(name_col, 'Unknown Respondent'))
        p_num = str(meta.get(phone_col, 'N/A'))
        woreda = str(meta.get(woreda_col, 'N/A'))
        kebele = str(meta.get(kebele_col, 'N/A'))
        village = str(meta.get(village_col, 'N/A'))
        
        st.markdown(f"""
            <div class="farmer-card">
                <div style="font-size: 18px; font-weight: 600; color: #2C3E50;">👨‍🌾 {f_name} (ID: {f_id})</div>
                <div class="farmer-info-row">
                    <div class="farmer-info-item">📞 {p_num}</div>
                    <span class="location-badge">📍 {woreda} • {kebele} • {village}</span>
                    <span class="error-badge">{len(issues)} Discrepancies</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        for iss in issues:
            row_data = iss['row']
            var_name = row_data.get('variable', 'N/A')
            bad_val = row_data.get('value', 'N/A')
            reason = row_data.get(reason_col, 'Value out of range constraint')
            
            with st.expander(f"⚠️ Flagged Target Column: {var_name}"):
                st.markdown(f"**Error Reason:** `{reason}`")
                st.markdown(f"**Collected Value:** `{bad_val}`")
                
                corrected_val = st.text_input("Enter Corrected Value", key=f"input_{iss['key']}")
                justification = st.text_area("Justification Notes/Explanation", key=f"notes_{iss['key']}", placeholder="Why is this change being made?")
                
                if st.button("Save Entry Correction", key=f"btn_{iss['key']}"):
                    if not corrected_val or not justification:
                        st.error("Please fill out both fields before saving.")
                    else:
                        st.session_state.corrections_list.append({
                            'key': iss['key'],
                            'error_type': iss['type'],
                            'unique_id': f_id,
                            'farmer_name': f_name,
                            'variable': var_name,
                            'original_value': bad_val,
                            'corrected_value': corrected_val,
                            'explanation': justification,
                            'corrected_by': enum_id,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        st.success("Correction saved locally!")
                        st.rerun()

# ============================================================================
# EXPORT DATA COMPILING LAYER WITH GITHUB SYNC
# ============================================================================
st.write("---")
st.subheader("📥 Sync Cleaned Dataset Logs")

if st.session_state.corrections_list:
    export_df = pd.DataFrame(st.session_state.corrections_list)
    st.dataframe(export_df, use_container_width=True)
    
    if st.button("☁️ Commit Corrections Directly to GitHub"):
        if not GITHUB_TOKEN:
            st.error("Missing personal token. Setup access permission variables first.")
        else:
            with st.spinner(f"Pushing changes securely back to {OUTPUT_FILE}..."):
                success = commit_file_to_github(
                    repo=GITHUB_REPO,
                    filepath=OUTPUT_FILE,
                    token=GITHUB_TOKEN,
                    df=export_df,
                    commit_message=f"Automated log adjustments by {enum_id} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                if success:
                    st.success(f"🎉 Securely synced and saved data matrix to GitHub: `{OUTPUT_FILE}`!")
                else:
                    st.error("Git target branch verification failed. Confirm write authorization scopes.")

    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download Corrections CSV File (Local Backup)",
        data=csv_buffer.getvalue(),
        file_name=f"corrections_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
else:
    st.info("No corrections have been submitted in this browser session yet.")
