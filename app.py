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
        st.error(f"Error loading {filename}: {str(e)}")
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
            st.error("🔐 Access token expired. Please contact administrator.")
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

def safe_get_unique_ids(df: pd.DataFrame) -> set:
    """Safely get unique IDs from dataframe"""
    if df is None or len(df) == 0:
        return set()
    id_col = get_unique_id_column(df)
    if id_col is None:
        return set()
    return set(df[id_col].unique())

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

def render_progress_bar(current: int, total: int):
    percentage = (current / total * 100) if total > 0 else 0
    st.markdown(f"""
        <div class="progress-bar"><div class="progress-fill" style="width: {percentage}%"></div></div>
        <p style="text-align: center; color: #666;">{current} of {total} completed ({percentage:.0f}%)</p>
    """, unsafe_allow_html=True)

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
        st.info(f"**Current Value:** {
