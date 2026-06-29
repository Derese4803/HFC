import base64
import io
import requests
import pandas as pd
import streamlit as st

OWNER = "mohammed-seid"
REPO = "hfc-data-private"


def github_headers():
    return {
        "Authorization": f"token {st.secrets['github']['token']}",
        "Accept": "application/vnd.github.v3+json",
    }


def load_csv(filename):
    ...
