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
        st.error(f"Failed to fetch {filepath} from GitHub. Error: {response.status_code
