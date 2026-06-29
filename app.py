import streamlit as st
import pandas as pd
from datetime import datetime
import io
import re
import requests
import base64
from typing import Tuple, Optional, List, Dict

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="HFC Data Correction",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "HFC Data Correction System v2.0"
    }
)

# Constants
GITHUB_OWNER = "mohammed-seid"
GITHUB_REPO = "hfc-data-private"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
CACHE_TTL = 3600  # 1 hour

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
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 4px solid #4CAF50;
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
    
    /* Better mobile spacing */
    @media (max-width: 768px) {
        .stTextInput, .stNumberInput, .stTextArea {
            margin-bottom: 16px;
        }
        
        .stMetric {
            padding: 12px;
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
        
        if response.status_code != 200:
            return None
        
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        return pd.read_csv(io.StringIO(content))
        
    except requests.exceptions.Timeout:
        st.error(f"⏱️ Timeout loading {filename}. Please check your connection.")
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=CACHE_TTL)
def load_data_from_github() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Load constraints and logic data from GitHub with caching"""
    constraints_df = fetch_file_from_github("constraints.csv")
    logic_df = fetch_file_from_github("logic.csv")
    return constraints_df, logic_df

def load_existing_corrections() -> Optional[pd.DataFrame]:
    """Load existing corrections from GitHub"""
    try:
        headers = get_github_headers()
        corrections_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/corrections.csv"
        response = requests.get(corrections_url, headers=headers)
        
        if response.status_code == 200:
            corrections_content = base64.b64decode(response.json()['content']).decode('utf-8')
            return pd.read_csv(io.StringIO(corrections_content))
        else:
            return None
    except:
        return None

def save_corrections_to_github(corrections_df: pd.DataFrame) -> bool:
    """Save or append corrections to GitHub"""
    try:
        headers = get_github_headers()
        corrections_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/corrections.csv"
        
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
            "message": f"Add corrections - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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
            return False
        return True
    except:
        return False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_unique_id_column(df: pd.DataFrame) -> Optional[str]:
    """Find the unique ID column name in the dataframe"""
    if df is None or len(df) == 0:
        return None
    
    possible_names = [
        'unique_id', 'Unique_id', 'UNIQUE_ID', 'UniqueID', 'unique_ID',
        'id', 'ID', 'farmer_id', 'Farmer_ID', 'farmerid'
    ]
    
    for col_name in possible_names:
        if col_name in df.columns:
            return col_name
    
    for col in df.columns:
        if 'id' in col.lower():
            return col
    
    return None

# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

def extract_constraint_limits(constraint_text: str) -> Tuple[int, int]:
    """Extract min/max values from constraint text for display purposes only"""
    min_val, max_val = 0, 100000
    try:
        constraint_lower = str(constraint_text).lower()
        numbers = re.findall(r'\d+', constraint_text)
        if 'max' in constraint_lower and numbers:
            max_val = int(numbers[-1])
        if 'min' in constraint_lower and numbers:
            min_val = int(numbers[-1])
        if 'between' in constraint_lower and len(numbers) >= 2:
            min_val = int(numbers[0])
            max_val = int(numbers[1])
    except:
        pass
    return min_val, max_val

def get_corrected_error_keys(enumerator: str) -> set:
    """Get set of already corrected error keys for this enumerator"""
    existing_corrections = load_existing_corrections()
    if existing_corrections is None or len(existing_corrections) == 0:
        return set()
    
    enumerator_corrections = existing_corrections[existing_corrections['corrected_by'] == enumerator]
    corrected_keys = set()
    for _, row in enumerator_corrections.iterrows():
        unique_id = None
        if 'unique_id' in row:
            unique_id = row['unique_id']
        else:
            for col in row.index:
                if 'id' in col.lower() and col != 'error_type':
                    unique_id = row[col]
                    break
        if unique_id:
            error_key = f"{row['error_type']}_{unique_id}_{row['variable']}"
            corrected_keys.add(error_key)
    return corrected_keys

def filter_uncorrected_errors(df: pd.DataFrame, error_type: str, enumerator: str) -> pd.DataFrame:
    """Remove already corrected errors from dataframe"""
    if df is None or len(df) == 0:
        return pd.DataFrame()
    
    id_col = get_unique_id_column(df)
    if id_col is None:
        return pd.DataFrame()
    
    corrected_keys = get_corrected_error_keys(enumerator)
    all_corrected = corrected_keys.union(st.session_state.corrected_errors)
    
    return df[~df.apply(
        lambda x: f"{error_type}_{x[id_col]}_{x['variable']}" in all_corrected,
        axis=1
    )]

def get_enumerator_statistics(constraints_df: pd.DataFrame, logic_df: pd.DataFrame) -> pd.DataFrame:
    """Get detailed statistics for each enumerator"""
    stats = []
    all_enumerators = set()
    if constraints_df is not None and len(constraints_df) > 0:
        all_enumerators.update(constraints_df['username'].unique())
    if logic_df is not None and len(logic_df) > 0:
        all_enumerators.update(logic_df['username'].unique())
    
    existing_corrections = load_existing_corrections()
    
    for enumerator in sorted(all_enumerators):
        constraint_errors = len(constraints_df[constraints_df['username'] == enumerator]) if constraints_df is not None else 0
        logic_errors = len(logic_df[logic_df['username'] == enumerator]) if logic_df is not None else 0
        total_errors = constraint_errors + logic_errors
        
        solved = len(existing_corrections[existing_corrections['corrected_by'] == enumerator]) if existing_corrections is not None else 0
        remaining = total_errors - solved
        percentage = (solved / total_errors * 100) if total_errors > 0 else 0
        
        stats.append({
            'Username': enumerator,
            'Total Errors': total_errors,
            'Solved': solved,
            'Remaining': remaining,
            'Progress (%)': round(percentage, 1)
        })
    
    return pd.DataFrame(stats).sort_values('Remaining', ascending=False) if stats else pd.DataFrame()

# ============================================================================
# UI RENDERING & COMPONENT INJECTION
# ============================================================================

def render_farmer_header(farmer_name: str, phone_no: str, error_count: int, completed_count: int = 0):
    badge = f'<span class="success-badge">{completed_count} ready</span> <span class="error-badge">{error_count-completed_count} pending</span>' if completed_count > 0 else f'<span class="error-badge">{error_count} issues</span>'
    st.markdown(f"""
        <div class="farmer-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 18px; font-weight: 600;">👨‍🌾 {farmer_name}</div>
                    <div style="font-size: 14px; color: #666; margin-top: 4px;">📞 {phone_no}</div>
                </div>
                <div>{badge}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_constraint_error(error: pd.Series, error_key: str, id_col: str):
    st.markdown(f"### 🔒 {error['variable']}")
    min_val, max_val = extract_constraint_limits(error['constraint'])
    try: default_value = int(error['value'])
    except: default_value = 0
        
    col1, col2 = st.columns([3, 2])
    with col1:
        st.info(f"**Current Value:** {error['value']}")
        st.caption(f"**Rule:** {error['constraint']}")
    with col2:
        correct_value = st.number_input("Corrected Value", value=default_value, step=1, key=f"value_{error_key}")
        
    if correct_value < min_val or correct_value > max_val:
        st.warning(f"⚠️ Value outside expected range ({min_val}-{max_val}).")
        
    explanation = st.text_area("📝 Explanation (Required)", key=f"explain_{error_key}", height=100, 
                               placeholder="Why is this change necessary? What did the farmer clarify?")
    
    st.session_state.all_corrections_data[error_key] = {
        'error_type': 'constraint', 'error_data': error, 'correct_value': correct_value,
        'explanation': explanation, 'outside_range': correct_value < min_val or correct_value > max_val, 'id_column': id_col
    }

def render_logic_error(discrepancy: pd.Series, error_key: str, id_col: str):
    st.markdown(f"### 📊 {discrepancy['variable']}")
    try:
        farmer_value = int(discrepancy['value'])
        troster_value = int(discrepancy['Troster Value'])
    except:
        farmer_value, troster_value = 0, 0
        
    col1, col2, col3 = st.columns(3)
    col1.metric("Your Report", farmer_value)
    col2.metric("System Record", troster_value)
    col3.metric("Difference", farmer_value - troster_value)
    
    correct_value = st.number_input("Corrected Value", value=farmer_value, step=1, key=f"value_{error_key}")
    explanation = st.text_area("📝 Explanation (Required)", key=f"explain_{error_key}", height=100, 
                               placeholder="Why is there a conflict between your records and the system record?")
    
    st.session_state.all_corrections_data[error_key] = {
        'error_type': 'logic', 'error_data': discrepancy, 'correct_value': correct_value,
        'explanation': explanation, 'id_column': id_col
    }

# ============================================================================
# MAIN APPLICATION ROUTER
# ============================================================================

def main():
    st.title("🌾 HFC Structural Field-Data Correction System")
    
    constraints_df = None
    logic_df = None
    mode = "Cloud (GitHub)"

    # Check if GitHub configuration is active and working
    if check_token_validity():
        constraints_df, logic_df = load_data_from_github()
    
    # FALLBACK INPUT BUTTON: Triggered if GitHub variables are missing/failed
    if constraints_df is None or logic_df is None:
        mode = "Manual Local Upload"
        st.warning("⚠️ GitHub link offline or unconfigured. Switching to Local Upload mode.")
        
        col1, col2 = st.columns(2)
        with col1:
            c_file = st.file_uploader("Upload constraints.csv File", type=["csv"])
            if c_file:
                constraints_df = pd.read_csv(c_file)
        with col2:
            l_file = st.file_uploader("Upload logic.csv File", type=["csv"])
            if l_file:
                logic_df = pd.read_csv(l_file)
                
        if constraints_df is None and logic_df is None:
            st.info("💡 Drop your field data CSV logs above to begin auditing forms.")
            return

    st.sidebar.markdown(f"**Active Mode:** `{mode}`")

    # Admin Control Center Router
    st.sidebar.title("🔐 Authorization Check")
    if not st.session_state.is_admin:
        with st.sidebar.expander("Admin Login Dashboard"):
            user = st.text_input("Username")
            pas = st.text_input("Password", type="password")
            if st.button("Log In"):
                if user == ADMIN_USERNAME and pas == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.rerun()
                else: 
                    st.error("Invalid credentials.")
    else:
        st.sidebar.success("Logged in as System Administrator")
        if st.sidebar.button("Log Out"):
            st.session_state.is_admin = False
            st.rerun()

    # Route screen output to admin view panel if logged in
    if st.session_state.is_admin:
        st.subheader("📊 Executive System Metrics")
        stats_df = get_enumerator_statistics(constraints_df, logic_df)
        if not stats_df.empty:
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        else:
            st.info("No logs are currently pending submission across your active system networks.")
        return

    # Form Processor Layout for Field Agents
    all_users = []
    if constraints_df is not None and 'username' in constraints_df.columns:
        all_users.extend(constraints_df['username'].dropna().unique())
    if logic_df is not None and 'username' in logic_df.columns:
        all_users.extend(logic_df['username'].dropna().unique())
    all_users = sorted(list(set(all_users)))
    
    if not all_users:
        st.error("Could not parse 'username' column out of the uploaded datasets.")
        return

    selected_enum = st.selectbox("Select Your Enumerator Identifier Code:", ["-- Select ID --"] + all_users)
    if selected_enum == "-- Select ID --":
        st.info("Please select your assigned username identifier from the selector menu to pull up your pending dashboard.")
        return

    # Parse remaining tasks assigned specifically to this individual user
    c_user = constraints_df[constraints_df['username'] == selected_enum] if constraints_df is not None else pd.DataFrame()
    l_user = logic_df[logic_df['username'] == selected_enum] if logic_df is not None else pd.DataFrame()
    
    c_pending = filter_uncorrected_errors(c_user, "constraint", selected_enum) if not c_user.empty else pd.DataFrame()
    l_pending = filter_uncorrected_errors(l_user, "logic", selected_enum) if not l_user.empty else pd.DataFrame()

    if c_pending.empty and l_pending.empty:
        st.success("🎉 All clear! No pending corrections located for this profile.")
        return

    id_col = get_unique_id_column(constraints_df) or get_unique_id_column(logic_df) or 'unique_id'
    st.subheader("📋 Pending Data Verification Backlog")
    
    # Process Range Constraint Errors
    if not c_pending.empty and id_col in c_pending.columns:
        for idx, row in c_pending.iterrows():
            key = f"constraint_{row[id_col]}_{row['variable']}"
            with st.expander(f"❌ Range Constraint Error: ID {row[id_col]} ({row['variable']})"):
                render_farmer_header(row.get('farmer_name', 'N/A'), str(row.get('phone_number', 'N/A')), 1)
                render_constraint_error(row, key, id_col)
                
                if st.button("Commit Correction", key=f"btn_{key}"):
                    data = st.session_state.all_corrections_data.get(key)
                    if data and data['explanation'].strip():
                        new_row_df = pd.DataFrame([{
                            'error_type': 'constraint', 'unique_id': str(row[id_col]), 'variable': row['variable'],
                            'correct_value': data['correct_value'], 'explanation': data['explanation'].strip(),
                            'corrected_by': selected_enum, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }])
                        
                        if mode == "Cloud (GitHub)":
                            if save_corrections_to_github(new_row_df):
                                st.session_state.corrected_errors.add(key)
                                st.success("Correction pushed to GitHub!")
                                st.rerun()
                        else:
                            st.session_state.corrected_errors.add(key)
                            st.success("Correction logged locally! (Download final dataframe from admin profile panel)")
                            st.rerun()
                    else: 
                        st.error("Justification explanation comment is required.")

    # Process System Reconciliation Logic Mismatches
    if not l_pending.empty and id_col in l_pending.columns:
        for idx, row in l_pending.iterrows():
            key = f"logic_{row[id_col]}_{row['variable']}"
            with st.expander(f"⚠️ System Mismatch Discrepancy: ID {row[id_col]} ({row['variable']})"):
                render_farmer_header(row.get('farmer_name', 'N/A'), str(row.get('phone_number', 'N/A')), 1)
                render_logic_error(row, key, id_col)
                
                if st.button("Commit Correction", key=f"btn_{key}"):
                    data = st.session_state.all_corrections_data.get(key)
                    if data and data['explanation'].strip():
                        new_row_df = pd.DataFrame([{
                            'error_type': 'logic', 'unique_id': str(row[id_col]), 'variable': row['variable'],
                            'correct_value': data['correct_value'], 'explanation': data['explanation'].strip(),
                            'corrected_by': selected_enum, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }])
                        
                        if mode == "Cloud (GitHub)":
                            if save_corrections_to_github(new_row_df):
                                st.session_state.corrected_errors.add(key)
                                st.success("Correction pushed to GitHub!")
                                st.rerun()
                        else:
                            st.session_state.corrected_errors.add(key)
                            st.success("Correction logged locally!")
                            st.rerun()
                    else: 
                        st.error("Justification explanation comment is required.")

if __name__ == "__main__":
    main()
