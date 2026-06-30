import streamlit as st
import pandas as pd
from datetime import datetime
import io
import re
import requests
import base64
import os
from typing import Tuple, Optional, List, Dict

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="ET Papaya HFC Data Correction",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "ET Papaya HFC Data Correction System v2.0"
    }
)

# Constants
GITHUB_OWNER = "mohammed-seid"
GITHUB_REPO = "hfc-data-private"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ENUMERATOR_PASSWORD = "1234"
CACHE_TTL = 3600  # 1 hour

# ========== FILE NAMES ==========
CONSTRAINTS_FILE = "constraints_papaya.csv"
LOGIC_FILE = "logic_papaya.csv"
CORRECTIONS_FILE = "corrections_papaya.csv"

# ============================================================================
# STYLING - Mobile-First Design
# ============================================================================

st.markdown("""
    <style>
    /* Mobile-optimized styles */
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
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .enumerator-stats {
        background: #f8f9fa;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        border-left: 4px solid #667eea;
    }
    
    .login-box {
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    /* Better mobile spacing */
    @media (max-width: 768px) {
        .stTextInput, .stNumberInput, .stTextArea {
            margin-bottom: 16px;
        }
        
        .stMetric {
            padding: 12px;
        }
        
        .farmer-info-row {
            flex-direction: column;
            gap: 8px;
        }
    }
    
    /* Progress indicator */
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

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'corrected_errors': set(),
        'all_corrections_data': {},
        'is_admin': False,
        'is_authenticated': False,
        'selected_enumerator': None,
        'show_completed': False,
        'filter_error_type': 'All'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ============================================================================
# GITHUB API FUNCTIONS
# ============================================================================

def get_github_headers() -> Dict[str, str]:
    """Get GitHub API headers with authentication"""
    token = st.secrets.get("github", {}).get("token")
    if not token:
        raise ValueError("GitHub token not configured in secrets")
    
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

def fetch_file_from_github(filename: str) -> Optional[pd.DataFrame]:
    """Fetch and parse CSV file from GitHub"""
    try:
        headers = get_github_headers()
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{filename}"
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            # Return blank DataFrame if corrections file doesn't exist yet
            if filename == CORRECTIONS_FILE:
                return pd.DataFrame()
            return None
        elif response.status_code != 200:
            st.error(f"Failed to load {filename}: {response.status_code}")
            return None
        
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        df = pd.read_csv(io.StringIO(content))
        return df
        
    except requests.exceptions.Timeout:
        st.error(f"⏱️ Timeout loading {filename}. Please check your connection.")
        return None
    except Exception as e:
        st.error(f"Error loading {filename}: {str(e)}")
        return None

@st.cache_data(ttl=CACHE_TTL)
def load_data_from_github() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Load constraints and logic data from GitHub with caching"""
    constraints_df = fetch_file_from_github(CONSTRAINTS_FILE)
    logic_df = fetch_file_from_github(LOGIC_FILE)
    
    if constraints_df is not None or logic_df is not None:
        st.success("✅ Data assets loaded from secure repository")
    
    return constraints_df, logic_df

def load_existing_corrections() -> Optional[pd.DataFrame]:
    """Load existing corrections from GitHub"""
    return fetch_file_from_github(CORRECTIONS_FILE)

def save_corrections_to_github(corrections_df: pd.DataFrame) -> bool:
    """Save or append corrections to GitHub"""
    try:
        headers = get_github_headers()
        corrections_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{CORRECTIONS_FILE}"
        
        response = requests.get(corrections_url, headers=headers)
        sha = None
        
        if response.status_code == 200:
            sha = response.json()['sha']
            existing_content = base64.b64decode(response.json()['content']).decode('utf-8')
            existing_df = pd.read_csv(io.StringIO(existing_content))
            corrections_df = pd.concat([existing_df, corrections_df], ignore_index=True)
        
        csv_data = corrections_df.to_csv(index=False)
        encoded_data = base64.b64encode(csv_data.encode()).decode()
        
        payload = {
            "message": f"Add papaya corrections - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": encoded_data,
            "branch": "main"
        }
        
        if sha:
            payload["sha"] = sha
            
        response = requests.put(corrections_url, headers=headers, json=payload, timeout=10)
        return response.status_code in [200, 201]
        
    except Exception as e:
        st.error(f"Error saving to GitHub: {str(e)}")
        return False

def check_token_validity() -> bool:
    """Verify GitHub token is valid"""
    try:
        headers = get_github_headers()
        response = requests.get("https://api.github.com/user", headers=headers, timeout=5)
        if response.status_code == 401:
            st.error("🔐 Access token expired. Please contact administrator.")
            return False
        return True
    except:
        return False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_unique_id_column(df: pd.DataFrame) -> str:
    """Find the unique ID column name in the dataframe"""
    if df is None or len(df) == 0:
        return 'unique_id'
    
    possible_names = ['unique_id', 'Unique_id', 'number', 'id', 'ID', 'farmer_id']
    for col_name in possible_names:
        if col_name in df.columns:
            return col_name
    return df.columns[0]

def get_farmer_name_column(df: pd.DataFrame) -> Optional[str]:
    """Find the farmer name column in the dataframe"""
    if df is None or len(df) == 0:
        return None
    possible_names = ['respondent_name', 'farmer_name', 'resp_name', 'name']
    for col_name in possible_names:
        if col_name in df.columns:
            return col_name
    return None

def get_phone_column(df: pd.DataFrame) -> Optional[str]:
    """Find the phone number column in the dataframe"""
    if df is None or len(df) == 0:
        return None
    possible_names = ['phone_no', 'phone', 'telephone', 'mobile']
    for col_name in possible_names:
        if col_name in df.columns:
            return col_name
    return None

def get_reason_column(df: pd.DataFrame) -> Optional[str]:
    """Find the reason/constraint column in the dataframe"""
    if df is None or len(df) == 0:
        return None
    possible_names = ['constraint', 'reason', 'rule', 'error_message']
    for col_name in possible_names:
        if col_name in df.columns:
            return col_name
    return None

def get_location_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Find location columns (woreda, kebele, village) in the dataframe"""
    location_cols = {'woreda': None, 'kebele': None, 'village': None}
    if df is None or len(df) == 0:
        return location_cols
    
    for col in df.columns:
        if 'woreda' in col.lower() or 'district' in col.lower():
            location_cols['woreda'] = col
        elif 'kebele' in col.lower():
            location_cols['kebele'] = col
        elif 'village' in col.lower() or 'gote' in col.lower():
            location_cols['village'] = col
            
    return location_cols

def format_display_value(value) -> str:
    """Format a value for display, handling None, NaN, and special values"""
    if value is None or pd.isna(value):
        return 'N/A'
    str_val = str(value).strip()
    if str_val in ['-99', '-999', 'nan', 'None', '']:
        return 'N/A'
    return str_val

# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

def extract_constraint_limits(constraint_text: str) -> Tuple[int, int]:
    """Extract min/max values from constraint text for display purposes only"""
    min_val, max_val = 0, 100000
    try:
        constraint_lower = str(constraint_text).lower()
        numbers = [int(s) for s in re.findall(r'\d+', constraint_text)]
        if 'max' in constraint_lower and numbers:
            max_val = numbers[-1]
        if 'min' in constraint_lower and numbers:
            min_val = numbers[-1]
        if 'between' in constraint_lower and len(numbers) >= 2:
            min_val = numbers[0]
            max_val = numbers[1]
    except:
        pass
    return min_val, max_val

def get_corrected_error_keys(enumerator: str) -> set:
    """Get set of already corrected error keys for this enumerator"""
    existing_corrections = load_existing_corrections()
    if existing_corrections is None or len(existing_corrections) == 0:
        return set()
    
    enumerator_corrections = existing_corrections[
        existing_corrections['corrected_by'].astype(str).str.lower().str.strip() == enumerator.lower().strip()
    ]
    
    corrected_keys = set()
    for _, row in enumerator_corrections.iterrows():
        if 'unique_id' in row and 'variable' in row and 'error_type' in row:
            error_key = f"{row['error_type']}_{row['unique_id']}_{row['variable']}"
            corrected_keys.add(error_key)
            
    return corrected_keys

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_progress_bar(current: int, total: int):
    """Render a visual progress bar"""
    percentage = (current / total * 100) if total > 0 else 0
    st.markdown(f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {percentage}%"></div>
        </div>
        <p style="text-align: center; color: #666;">
            {current} of {total} completed ({percentage:.0f}%)
        </p>
    """, unsafe_allow_html=True)

def render_metric_card(label: str, value: str, icon: str = "📊"):
    """Render an attractive metric card"""
    st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 32px; margin-bottom: 8px;">{icon}</div>
            <div style="font-size: 28px; font-weight: 700;">{value}</div>
            <div style="font-size: 14px; opacity: 0.9;">{label}</div>
        </div>
    """, unsafe_allow_html=True)

def render_farmer_header(farmer_name: str, phone_no: str, woreda: str, kebele: str, village: str, error_count: int, completed_count: int = 0):
    """Render farmer information header with location details"""
    if completed_count > 0:
        badge = f'<span class="success-badge">{completed_count} ready</span> <span class="error-badge">{error_count - completed_count} pending</span>'
    else:
        badge = f'<span class="error-badge">{error_count} issues</span>'
    
    phone_display = format_display_value(phone_no)
    woreda_display = format_display_value(woreda)
    kebele_display = format_display_value(kebele)
    village_display = format_display_value(village)
    
    st.markdown(f"""
        <div class="farmer-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                <div style="flex: 1;">
                    <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">👨‍🌾 {farmer_name}</div>
                    <div class="farmer-info-row">
                        <div class="farmer-info-item">
                            📞 <a href="tel:{phone_display}" style="color: #667eea; text-decoration: none;">{phone_display}</a>
                        </div>
                    </div>
                    <div class="farmer-info-row" style="margin-top: 10px;">
                        <div class="farmer-info-item">
                            <span class="location-badge">📍 Woreda: {woreda_display}</span>
                        </div>
                        <div class="farmer-info-item">
                            <span class="location-badge">🏘️ Kebele: {kebele_display}</span>
                        </div>
                        <div class="farmer-info-item">
                            <span class="location-badge">🏡 Village: {village_display}</span>
                        </div>
                    </div>
                </div>
                <div style="margin-top: 5px;">{badge}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MAIN APP ROUTER LOGIC
# ============================================================================

# Fetch core configuration datasets
constraints_df, logic_df = load_data_from_github()

# Collect actual unique users inside your asset spreadsheets
all_users = set()
if constraints_df is not None and 'username' in constraints_df.columns:
    all_users.update(constraints_df['username'].dropna().unique())
if logic_df is not None and 'username' in logic_df.columns:
    all_users.update(logic_df['username'].dropna().unique())
VALID_ENUMERATORS = sorted(list(all_users)) if all_users else VALID_ENUMERATORS

# LOGIN INTERFACE
if not st.session_state.is_authenticated:
    st.title("🔐 ET Papaya Verification Entry Gate")
    
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        login_role = st.radio("Select Operational Role", ["Enumerator Profile", "Central Administrator"])
        
        user_input = st.text_input("Username / ID Token")
        pass_input = st.text_input("Security Access PIN", type="password")
        
        if st.button("Authorize Connection"):
            if login_role == "Central Administrator":
                if user_input == ADMIN_USERNAME and pass_input == ADMIN_PASSWORD:
                    st.session_state.is_authenticated = True
                    st.session_state.is_admin = True
                    st.success("Welcome Back Admin!")
                    st.rerun()
                else:
                    st.error("Invalid Administrative Access Pin.")
            else:
                if user_input.lower().strip() in [u.lower().strip() for u in VALID_ENUMERATORS] and pass_input == ENUMERATOR_PASSWORD:
                    st.session_state.is_authenticated = True
                    st.session_state.is_admin = False
                    # Preserve standard string matching alignment
                    matched_enum = [u for u in VALID_ENUMERATORS if u.lower().strip() == user_input.lower().strip()][0]
                    st.session_state.selected_enumerator = matched_enum
                    st.success(f"Profile `{matched_enum}` Authenticated.")
                    st.rerun()
                else:
                    st.error("Invalid Enumerator Profile Username or pin.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================================
# ADMIN ARCHITECTURE VIEW
# ============================================================================
if st.session_state.is_admin:
    st.title("📊 Control Room Dashboard")
    
    if st.button("🔄 Clear App Cache & Sync"):
        st.cache_data.clear()
        st.rerun()
        
    if st.button("🚪 Logout Admin"):
        st.session_state.is_authenticated = False
        st.session_state.is_admin = False
        st.rerun()
        
    # Read global history trace log
    master_trace_df = load_existing_corrections()
    
    col1, col2 = st.columns(2)
    with col1:
        render_metric_card("Total Logs Fixed Across Network", str(len(master_trace_df) if master_trace_df is not None else 0), "🎯")
    with col2:
        rem_count = (len(constraints_df) if constraints_df is not None else 0) + (len(logic_df) if logic_df is not None else 0)
        solved_total = len(master_trace_df) if master_trace_df is not None else 0
        render_metric_card("Remaining Field System Discrepancies", str(max(0, rem_count - solved_total)), "⏳")
        
    if master_trace_df is not None and len(master_trace_df) > 0:
        st.markdown("### 📥 Download Session Diagnostic Logs")
        st.dataframe(master_trace_df, use_container_width=True)
        st.download_button(
            label="Download Master Corrections spreadsheet (CSV)",
            data=master_trace_df.to_csv(index=False).encode('utf-8'),
            file_name=f"Master_Papaya_Corrections_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No logs have been pushed to the repository yet.")
    st.stop()

# ============================================================================
# ENUMERATOR ARCHITECTURE WORKFLOW
# ============================================================================
enum_id = st.session_state.selected_enumerator
st.title(f"🛠️ HFC Core Tasklist: `{enum_id}`")

if st.button("🚪 Logout Account"):
    st.session_state.is_authenticated = False
    st.session_state.selected_enumerator = None
    st.session_state.all_corrections_data = {}
    st.session_state.corrected_errors = set()
    st.rerun()

# Filter active user records from global matrices
c_user = constraints_df[constraints_df['username'].astype(str).str.lower().str.strip() == enum_id.lower().strip()].copy() if constraints_df is not None else pd.DataFrame()
l_user = logic_df[logic_df['username'].astype(str).str.lower().str.strip() == enum_id.lower().strip()].copy() if logic_df is not None else pd.DataFrame()

id_c_col = get_unique_id_column(c_user)
id_l_col = get_unique_id_column(l_user)

# Identify downstream targets that have been fixed on the remote server
preexisting_completed_keys = get_corrected_error_keys(enum_id)

# Render User Forms UI Loops
combined_farmers_index = {}

# Process Constraints
for idx, row in c_user.iterrows():
    f_id = str(row[id_c_col])
    ekey = f"constraint_{f_id}_{row['variable']}"
    if ekey in preexisting_completed_keys:
        continue
    if f_id not in combined_farmers_index:
        combined_farmers_index[f_id] = {'meta': row, 'issues': []}
    combined_farmers_index[f_id]['issues'].append({'type': 'constraint', 'data': row, 'key': ekey, 'id_col': id_c_col})

# Process Logic Mismatches
for idx, row in l_user.iterrows():
    f_id = str(row[id_l_col])
    ekey = f"logic_{f_id}_{row['variable']}"
    if ekey in preexisting_completed_keys:
        continue
    if f_id not in combined_farmers_index:
        combined_farmers_index[f_id] = {'meta': row, 'issues': []}
    combined_farmers_index[f_id]['issues'].append({'type': 'logic', 'data': row, 'key': ekey, 'id_col': id_l_col})

total_backlog_items = len(combined_farmers_index)

if total_backlog_items == 0:
    st.balloons()
    st.success("🎉 Outstanding job! All data issues associated with your profile are completely resolved.")
    st.stop()

# Progress Dashboard Status Tracker
active_done = len(st.session_state.corrected_errors)
render_progress_bar(active_done, total_backlog_items)

# Display Farmer Issues Grouped by Cards
for f_id, context in combined_farmers_index.items():
    meta = context['meta']
    issues = context['issues']
    
    # Skip if this whole card was verified during the session run
    if all(iss['key'] in st.session_state.corrected_errors for iss in issues):
        continue
        
    f_name = format_display_value(meta.get(get_farmer_name_column(pd.DataFrame([meta])), 'Unknown Farmer'))
    p_num = meta.get(get_phone_column(pd.DataFrame([meta])), 'N/A')
    locs = get_location_columns(pd.DataFrame([meta]))
    
    woreda = meta.get(locs['woreda'], 'N/A')
    kebele = meta.get(locs['kebele'], 'N/A')
    village = meta.get(locs['village'], 'N/A')
    
    render_farmer_header(f_name, p_num, woreda, kebele, village, len(issues))
    
    for iss in issues:
        if iss['key'] in st.session_state.corrected_errors:
            continue
            
        row_data = iss['data']
        var = row_data['variable']
        val = row_data['value']
        
        with st.expander(f"⚠️ Flagged Variable Column: {var}"):
            if iss['type'] == 'constraint':
                rule = row_data.get(get_reason_column(pd.DataFrame([row_data])), 'Value outside valid bounds')
                st.error(f"**Constraint Rule Violated:** {rule} (Value provided: `{val}`)")
            else:
                rule = row_data.get(get_reason_column(pd.DataFrame([row_data])), 'Internal survey conflict mismatch')
                st.warning(f"**Logic Variance Conflict:** {rule}")
                
            c_val = st.text_input("Input Corrected Value", key=f"v_{iss['key']}")
            exp_text = st.text_area("Justification / Explanation Notes", key=f"e_{iss['key']}", placeholder="Please enter validation feedback detailed explanation...")
            
            if st.button("Commit This Correction File", key=f"b_{iss['key']}"):
                if not c_val or not exp_text:
                    st.error("Please ensure all value inputs and explanation fields are filled before submitting.")
                else:
                    new_log_row = {
                        'error_type': iss['type'],
                        'unique_id': str(f_id),
                        'variable': str(var),
                        'original_value': str(val),
                        'corrected_value': str(c_val),
                        'explanation': str(exp_text).strip(),
                        'corrected_by': str(enum_id),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Package and commit straight to GitHub Cloud Server
                    save_success = save_corrections_to_github(pd.DataFrame([new_log_row]))
                    if save_success:
                        st.session_state.corrected_errors.add(iss['key'])
                        st.success("💾 Correction pushed to GitHub secure database successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Link connection failure. Unable to push data to GitHub repository.")
