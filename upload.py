import streamlit as st
import pandas as pd
import os
import requests
import base64
from io import StringIO, BytesIO
import warnings
from urllib.parse import quote
from github_client import get_github_client

warnings.filterwarnings("ignore")

GITHUB_REPO_API_UPLOAD = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data"
_UPLOAD_HERE = "Select Folder"


@st.cache_data(show_spinner=False, ttl=120)
def get_upload_folders_cached(token, path=""):
    client = get_github_client(token)
    items, error, auth_error = client.list_contents(path)
    if items is None:
        return [], error, auth_error

    folders = sorted([
        item['name'] for item in items
        if item['type'] == 'dir'
    ])
    return folders, None, False


def nav_option_value(item_type, name):
    return f"{item_type}|{name}"


def parse_nav_option(option):
    if not option or "|" not in option:
        return None, None
    item_type, item_name = option.split("|", 1)
    return item_type, item_name


def format_upload_nav_option(option):
    if not option or option == _UPLOAD_HERE:
        return _UPLOAD_HERE
    item_type, item_name = parse_nav_option(option)
    if item_type == "folder":
        return f"📁 {item_name}"
    return option


def render_folder_navigation(token):
    """Navigate repository folders for selecting an upload destination.
    Returns the selected destination path as a string."""
    levels = []
    current_path = ""
    breadcrumbs = []
    level = 0

    while True:
        folders, error, auth_error = get_upload_folders_cached(token, current_path)
        if auth_error:
            st.session_state['gh_token'] = None
            st.session_state['gh_token_validated'] = False
            st.error("Authentication failed. Please re-enter your security token.")
            break
        if error:
            st.warning(error)
            break

        folders = [f for f in folders if not (level == 0 and f == 'Visualizations')]
        if not folders:
            break

        options = [_UPLOAD_HERE] + [nav_option_value("folder", f) for f in folders]
        key = f"upload_dest_level_{level}"
        label = "Select destination folder:" if level == 0 else f"Subfolder (Level {level + 1}):"

        if key in st.session_state and st.session_state[key] not in options:
            st.session_state[key] = _UPLOAD_HERE

        levels.append((label, options, key))

        stored = st.session_state.get(key, _UPLOAD_HERE)
        if not stored or stored == _UPLOAD_HERE:
            break

        _, folder_name = parse_nav_option(stored)
        breadcrumbs.append(folder_name)
        current_path = "/".join(breadcrumbs)
        level += 1

    # Render in 3-column grid
    for row_start in range(0, len(levels), 3):
        row_levels = levels[row_start:row_start + 3]
        cols = st.columns(3)
        for col_idx, (lbl, opts, k) in enumerate(row_levels):
            with cols[col_idx]:
                st.selectbox(lbl, opts, key=k, format_func=format_upload_nav_option)

    # Re-walk session_state to derive final destination path
    dest_path = ""
    for _, _, k in levels:
        stored = st.session_state.get(k, _UPLOAD_HERE)
        if not stored or stored == _UPLOAD_HERE:
            break
        _, folder_name = parse_nav_option(stored)
        dest_path = f"{dest_path}/{folder_name}" if dest_path else folder_name

    return dest_path


def get_github_folders(token):
    headers = {"Authorization": f"token {token}"}
    url = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [item['name'] for item in response.json() if item['type'] == 'dir' and item['name'] != 'Visualizations']
    return []

def get_folder_contents(token, path):
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{path}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        items = response.json()
        subfolders = [item['name'] for item in items if item['type'] == 'dir']
        files = [item['name'] for item in items if item['type'] == 'file']
        return subfolders, files
    return [], []

def validate_github_token(token):
    client = get_github_client(token)
    return client.validate_token()

def main():
    st.title("Upload Data")
    
    # Use or ask for token: allow the user to provide it here (will be saved to session)
    token = st.session_state.get('gh_token', None)
    if not token:
        entered = st.text_input("Enter your security token:", type="password", key="upload_token")
        if entered:
            if validate_github_token(entered):
                st.session_state['gh_token'] = entered
                st.session_state['gh_token_validated'] = True
                st.success("Token validated and saved for this session.")
                token = entered
            else:
                st.error("Invalid token or access issue.")
                return
        else:
            st.warning("Please provide your security token to proceed.")
            return

    # Upload progress tracking
    if 'upload_history' not in st.session_state:
        st.session_state.upload_history = []
    
    if st.session_state.upload_history:
        with st.expander("Recent Uploads"):
            for upload in st.session_state.upload_history[-5:]:
                st.write(f"{upload['file']} → {upload['folder']} ({upload['time']})")

    # Step 3: File upload
    uploaded_files = st.file_uploader("Select files to upload (xls, xlsx, csv, dat, txt):",
                                      type=["xls", "xlsx", "csv", "dat", "txt"],
                                      accept_multiple_files=True,
                                      key="upload_files_widget")

    if uploaded_files:
        client = get_github_client(token)

        # Data validation summary
        st.write("### Data Validation Summary")
        validation_col1, validation_col2, validation_col3 = st.columns(3)
        
        total_files = len(uploaded_files)
        valid_files = sum(1 for f in uploaded_files if f.name.endswith(('xls', 'xlsx', 'csv', 'dat', 'txt')))
        total_size = sum(f.size for f in uploaded_files) / (1024*1024)  # MB
        
        with validation_col1:
            st.metric("Total Files", total_files)
        with validation_col2:
            st.metric("Valid Files", valid_files, f"{valid_files-total_files}" if valid_files != total_files else None)
        with validation_col3:
            st.metric("Total Size", f"{total_size:.1f} MB")
        
        # Step 4: File selection and sheet selection
        selected_file = st.selectbox("Select a file to view:", uploaded_files, format_func=lambda x: x.name, key="file_select")
        sheet_name = None
        if selected_file and selected_file.name.endswith(("xls", "xlsx")):
            excel_data = pd.ExcelFile(selected_file)
            sheet_name = st.selectbox("Select a sheet to view:", excel_data.sheet_names, key="sheet_select")

        # Step 4.1: File navigation and display
        with st.expander("File Display"):
            if selected_file:
                if selected_file.name.endswith(("xls", "xlsx")) and sheet_name:
                    df = excel_data.parse(sheet_name)
                    st.write(df)
                elif selected_file.name.endswith("csv"):
                    df = pd.read_csv(selected_file)
                    st.write(df)
                else:
                    content = StringIO(selected_file.getvalue().decode("utf-8"))
                    df = pd.read_csv(content, delimiter="\t")
                    st.write(df)

        # Step 4.2: Display column names and data types in a table
        with st.expander("Data Types"):
            if selected_file:
                if selected_file.name.endswith(("xls", "xlsx")) and sheet_name:
                    df = excel_data.parse(sheet_name)
                elif selected_file.name.endswith("csv"):
                    df = pd.read_csv(selected_file)
                else:
                    content = StringIO(selected_file.getvalue().decode("utf-8"))
                    df = pd.read_csv(content, delimiter="\t")

                if not df.empty:
                    col_data = []
                    for col in df.columns:
                        col_data.append((col, str(df[col].dtype)))

                    # Organize data into a table with 4 columns
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

        # Step 5: Navigate folder structure for upload destination
        st.write("### Select Upload Destination")
        dest_path = render_folder_navigation(token)
        if dest_path:
            st.caption(f"Upload destination: **{dest_path}**")
        else:
            st.info("Select a destination folder above.")

        # Step 6: Upload files to GitHub repository
        if st.button("Upload Files"):
            if not dest_path:
                st.warning("Please select a destination folder before uploading.")
                return
            try:
                for file in uploaded_files:
                    file_path = f"{dest_path}/{file.name}"
                    metadata, metadata_error, metadata_auth_error = client.get_file_metadata(file_path)
                    if metadata_auth_error:
                        st.session_state['gh_token'] = None
                        st.session_state['gh_token_validated'] = False
                        st.error("Authentication failed. Please re-enter your security token.")
                        return

                    if metadata:
                        st.warning(f"File '{file.name}' already exists at '{dest_path}'.")
                        continue

                    if metadata_error and "status 404" not in metadata_error:
                        st.error(f"Error checking file existence: {metadata_error}")
                        continue

                    content = file.getvalue()
                    _, upload_error, upload_auth_error = client.put_file(
                        file_path=file_path,
                        message=f"Add {file.name}",
                        content_b64=base64.b64encode(content).decode("utf-8"),
                    )
                    if upload_auth_error:
                        st.session_state['gh_token'] = None
                        st.session_state['gh_token_validated'] = False
                        st.error("Authentication failed. Please re-enter your security token.")
                        return
                    if upload_error:
                        st.error(f"Error uploading '{file.name}': {upload_error}")
                        continue

                    st.success(f"File '{file.name}' uploaded successfully.")
                    from datetime import datetime
                    st.session_state.upload_history.append({
                        'file': file.name,
                        'folder': dest_path,
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
                    })
            except Exception as e:
                st.error(f"Error uploading files: {e}")