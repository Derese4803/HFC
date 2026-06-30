import requests
import base64
import io
import pandas as pd

GITHUB_REPO = "Derese4803/HFC"

def fetch_file(filepath, token):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filepath}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        return pd.read_csv(io.StringIO(content))
    return None

def commit_file(filepath, token, df, message):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filepath}"
    headers = {"Authorization": f"token {token}"}
    get_resp = requests.get(url, headers=headers)
    sha = get_resp.json().get('sha') if get_resp.status_code == 200 else None
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    content = base64.b64encode(csv_buffer.getvalue().encode('utf-8')).decode('utf-8')
    
    data = {"message": message, "content": content}
    if sha: data["sha"] = sha
    return requests.put(url, headers=headers, json=data).status_code in [200, 201]
