import streamlit as st
import pandas as pd
import requests
from io import BytesIO, StringIO
import docx
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
from urllib.parse import quote
import base64

warnings.filterwarnings("ignore")

ROOT_EXCLUDED_FOLDERS = {"Visualizations"}
GITHUB_REPO_API = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data"

def github_headers(token, accept=None):
    headers = {"Authorization": f"token {token}"}
    if accept:
        headers["Accept"] = accept
    return headers

def validate_github_token(token):
    response = requests.get(GITHUB_REPO_API, headers=github_headers(token), timeout=30)
    return response.status_code == 200

def get_github_folders(token):
    headers = {"Authorization": f"token {token}"}
    url = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [item['name'] for item in response.json() if item['type'] == 'dir' and item['name'] != 'Visualizations']
    return []

def get_folder_contents(token, path):
    encoded_path = quote(path, safe='/')
    url = f"{GITHUB_REPO_API}/contents/{encoded_path}"
    response = requests.get(url, headers=github_headers(token), timeout=30)
    if response.status_code == 200:
        items = response.json()
        subfolders = [item['name'] for item in items if item['type'] == 'dir']
        files = [item['name'] for item in items if item['type'] == 'file']
        return subfolders, files
    return [], []

def get_repo_contents(token, path=""):
    base_url = f"{GITHUB_REPO_API}/contents"
    encoded_path = quote(path, safe='/') if path else ""
    url = f"{base_url}/{encoded_path}" if encoded_path else base_url
    response = requests.get(url, headers=github_headers(token), timeout=30)
    if response.status_code != 200:
        return [], []

    items = response.json()
    folders = []
    files = []
    for item in items:
        if item['type'] == 'dir':
            if not path and item['name'] in ROOT_EXCLUDED_FOLDERS:
                continue
            folders.append(item['name'])
        elif item['type'] == 'file':
            files.append(item['name'])

    return sorted(folders), sorted(files)

def get_github_files(token, folder):
    encoded_folder = quote(folder, safe='/')
    url = f"{GITHUB_REPO_API}/contents/{encoded_folder}"
    response = requests.get(url, headers=github_headers(token), timeout=30)
    if response.status_code == 200:
        return [item['name'] for item in response.json() if item['type'] == 'file']
    return []

def get_github_file_metadata(token, path, file):
    file_path = f"{path}/{file}" if path else file
    encoded_file_path = quote(file_path, safe='/')
    url = f"{GITHUB_REPO_API}/contents/{encoded_file_path}"
    response = requests.get(url, headers=github_headers(token), timeout=30)
    if response.status_code != 200:
        return None
    try:
        return response.json()
    except ValueError:
        return None

def get_github_file_content(token, path, file):
    metadata = get_github_file_metadata(token, path, file)
    if not metadata:
        return None, "GitHub could not find the file metadata."

    if metadata.get("encoding") == "base64" and metadata.get("content"):
        try:
            return base64.b64decode(metadata["content"]), None
        except Exception as exc:
            return None, f"GitHub returned unreadable encoded content: {exc}"

    download_url = metadata.get("download_url")
    if download_url:
        response = requests.get(download_url, headers=github_headers(token), timeout=60)
        if response.status_code == 200:
            return response.content, None
        return None, f"GitHub download URL returned status {response.status_code}."

    file_path = metadata.get("path") or f"{path}/{file}" if path else file
    encoded_file_path = quote(file_path, safe='/')
    raw_url = f"{GITHUB_REPO_API}/contents/{encoded_file_path}"
    response = requests.get(
        raw_url,
        headers=github_headers(token, accept="application/vnd.github.raw"),
        timeout=60,
    )
    if response.status_code == 200:
        return response.content, None

    return None, f"GitHub raw content request returned status {response.status_code}."

def parse_csv_file(file_content):
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    parse_attempts = [
        {"sep": ",", "engine": "python"},
        {"sep": None, "engine": "python"},
    ]

    last_error = None
    for encoding in encodings:
        for parse_kwargs in parse_attempts:
            try:
                text = file_content.decode(encoding)
                return pd.read_csv(StringIO(text), **parse_kwargs), None
            except Exception as exc:
                last_error = exc

    return None, str(last_error) if last_error else "Unknown CSV parsing error."

def decode_text_file(file_content):
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    last_error = None
    for encoding in encodings:
        try:
            return file_content.decode(encoding), None
        except Exception as exc:
            last_error = exc
    return None, str(last_error) if last_error else "Unknown text decoding error."

def read_docx(content):
    """Reads content from a .docx file."""
    try:
        doc = docx.Document(BytesIO(content))
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        return f"Error reading .docx file: {e}"

def render_repository_navigation(token):
    # --- Pass 1: walk via session_state to collect every level's (label, options, key) ---
    levels = []
    current_path = ""
    breadcrumbs = []
    level = 0

    while True:
        folders, files = get_repo_contents(token, current_path)
        options = [""] + [f"[Folder] {folder}" for folder in folders] + [f"[File] {file}" for file in files]

        if len(options) == 1:
            break

        key = f"repo_nav_level_{level}"
        label = "Select a folder or file:" if level == 0 else f"Level {level + 1}:"

        # Invalidate stale stored value
        if key in st.session_state and st.session_state[key] not in options:
            st.session_state[key] = ""

        levels.append((label, options, key))

        # Read already-stored selection to decide whether to go deeper
        stored = st.session_state.get(key, "")
        if not stored:
            break

        item_type, item_name = stored.split("] ", 1)
        if item_type == "[Folder":
            breadcrumbs.append(item_name)
            current_path = "/".join(breadcrumbs)
            level += 1
        else:
            # File selected — no deeper levels needed
            break

    # --- Pass 2: render levels in a 3-column grid (new row every 3 levels) ---
    for row_start in range(0, len(levels), 3):
        row_levels = levels[row_start:row_start + 3]
        cols = st.columns(3)
        for col_idx, (label, options, key) in enumerate(row_levels):
            with cols[col_idx]:
                st.selectbox(
                    label, options, key=key,
                    format_func=lambda item: item or "Choose an item"
                )

    # --- Pass 3: re-walk session_state to derive final path and file ---
    breadcrumbs = []
    selected_file = None
    for _, _, key in levels:
        stored = st.session_state.get(key, "")
        if not stored:
            break
        item_type, item_name = stored.split("] ", 1)
        if item_type == "[Folder":
            breadcrumbs.append(item_name)
        else:
            selected_file = item_name
            break

    selected_path = "/".join(breadcrumbs)
    selected_file_path = f"{selected_path}/{selected_file}" if selected_path and selected_file else selected_file
    return selected_path, selected_file, selected_file_path

def main():
    st.title("View Data")
    st.write("*Access only to team members.*")

    # Use or ask for token: allow the user to provide it here (will be saved to session)
    token = st.session_state.get('gh_token', None)
    if not token:
        entered = st.text_input("Enter your security token:", type="password", key="view_token")
        if entered:
            if validate_github_token(entered):
                st.session_state['gh_token'] = entered
                st.success("Token validated and saved for this session.")
                token = entered
            else:
                st.error("Invalid token or access issue.")
                return
        else:
            st.warning("Please provide your security token to proceed.")
            return

    st.write("### Repository Browser")
    selected_path, file_name, selected_file_path = render_repository_navigation(token)
    if selected_file_path:
        st.caption(f"Current path: {selected_file_path}")
    elif selected_path:
        st.caption(f"Current path: {selected_path}/")

    sheet_name = None
    df = None
    
    if file_name:
        path = selected_path
        file_content, file_error = get_github_file_content(token, path, file_name)
        if file_content is None:
            st.error(f"Unable to load the selected file: {selected_file_path or file_name}")
            if file_error:
                st.caption(f"Details: {file_error}")
            return
        
        if file_name.endswith(("xls", "xlsx")):
            try:
                excel_data = pd.ExcelFile(BytesIO(file_content))
                sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names)
                if sheet_name:
                    df = excel_data.parse(sheet_name)
            except Exception as exc:
                st.error(f"Unable to read the Excel file: {exc}")
                return
        elif file_name.endswith("csv"):
            df, csv_error = parse_csv_file(file_content)
            if df is None:
                st.error(f"Unable to parse the CSV file: {csv_error}")
                return
        elif file_name.endswith("txt"):
            text_content, text_error = decode_text_file(file_content)
            if text_content is None:
                st.error(f"Unable to read the TXT file: {text_error}")
                return

            with st.expander("TXT Content", expanded=True):
                st.text_area("Content", text_content, height=700, disabled=True, label_visibility="hidden")
        elif file_name.endswith("docx"):
            st.info("Successfully fetched .docx file content.")
            st.write(f"File size: {len(file_content)} bytes")
            
            docx_text = read_docx(file_content)

            if "Error reading .docx file" in docx_text:
                st.error(docx_text)
            elif not docx_text.strip():
                st.warning("The .docx file appears to be empty or could not be read.")
            else:
                with st.expander("DOCX Content", expanded=True):
                    st.text_area("Content", docx_text, height=700, disabled=True, label_visibility="hidden")
        else:
            st.warning("Only Excel, CSV, TXT, and DOCX files are supported for preview.")

    if df is not None:
        with st.expander("File Display", expanded=True):
            # Add column filtering
            if len(df.columns) > 10:
                selected_cols = st.multiselect("Select columns to display:", df.columns.tolist(), default=df.columns.tolist()[:10])
                if selected_cols:
                    df_display = df[selected_cols]
                else:
                    df_display = df
            else:
                df_display = df
            st.dataframe(df_display, height=700)
        # Only show Data Types, Summary, and Descriptive Statistics if sheet_name is not 'Metadata'
        if not (sheet_name and sheet_name.strip().lower() == "metadata"):
            with st.expander("Data Types", expanded=False):
                col_data = [(col, str(df[col].dtype)) for col in df.columns]
                col1, col2, col3, col4 = st.columns(4)
                for i, (col_name, col_type) in enumerate(col_data):
                    if i % 4 == 0:
                        col1.write(f"{col_name} : \n{col_type}")
                    elif i % 4 == 1:
                        col2.write(f"{col_name} : \n{col_type}")
                    elif i % 4 == 2:
                        col3.write(f"{col_name} : \n{col_type}")
                    elif i % 4 == 3:
                        col4.write(f"{col_name} : \n{col_type}")
            with st.expander("Summary", expanded=False):
                st.write(f"**Shape:** Rows: {df.shape[0]}, Columns: {df.shape[1]}")
                st.write("**Missing values per column:**")
                missing_data = df.isnull().sum()
                col1, col2, col3, col4 = st.columns(4)
                for i, (col_name, missing) in enumerate(missing_data.items()):
                    if i % 4 == 0:
                        col1.write(f"**{col_name}**: {missing}")
                    elif i % 4 == 1:
                        col2.write(f"**{col_name}**: {missing}")
                    elif i % 4 == 2:
                        col3.write(f"**{col_name}**: {missing}")
                    elif i % 4 == 3:
                        col4.write(f"**{col_name}**: {missing}")
            with st.expander("Descriptive Statistics", expanded=False):
                st.write(df.describe(include='all'))

if __name__ == "__main__":
    main()