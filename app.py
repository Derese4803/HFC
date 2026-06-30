import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
import base64
from typing import Tuple, Optional, Dict

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

# ========== DEFAULT ENUMERATORS ==========
DEFAULT_ENUMERATORS = ["semayat.s", "amarech.d", "eyuel.u", "kiya.l"]

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
        border-radius: 1
