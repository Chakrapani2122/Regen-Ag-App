import streamlit as st
import pandas as pd
import os
import requests
import base64
from io import StringIO, BytesIO

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
    headers = {"Authorization": f"token {token}"}
    url = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data"
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def main():
    st.title("Upload the Data")
    st.write("*Access only to team members.*")
    
    # Upload progress tracking
    if 'upload_history' not in st.session_state:
        st.session_state.upload_history = []
    
    if st.session_state.upload_history:
        with st.expander("📋 Recent Uploads"):
            for upload in st.session_state.upload_history[-5:]:
                st.write(f"✅ {upload['file']} → {upload['folder']} ({upload['time']})")

    # Step 1: Ask for GitHub security token
    token = st.text_input("Enter your security token:", type="password")
    if not token:
        st.warning("Please provide your security token to proceed.")
        return

    if validate_github_token(token):
        st.success("Token validated successfully!")
    else:
        st.error("Invalid token or access issue.")
        return

    # Step 3: File upload
    uploaded_files = st.file_uploader("Select files to upload (xls, xlsx, csv, dat, txt):", 
                                      type=["xls", "xlsx", "csv", "dat", "txt"], 
                                      accept_multiple_files=True)

    if uploaded_files:
        # Data validation summary
        st.write("### 🔍 Data Validation Summary")
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
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                folders = get_github_folders(token)
                folder_name = st.selectbox("Select a folder to upload the files:", folders)
            
            subfolder_name = None
            
            if folder_name:
                subfolders, _ = get_folder_contents(token, folder_name)
                
                if subfolders:
                    with col2:
                        subfolder_name = st.selectbox("Select a subfolder (optional):", [""] + subfolders)
                        
        except Exception as e:
            st.error(f"Error fetching folders: {e}")
            return

        # Step 6: Upload files to GitHub repository
        if st.button("Upload Files"):
            try:
                for file in uploaded_files:
                    # Construct file path based on folder and subfolder selection
                    if subfolder_name:
                        file_path = f"{folder_name}/{subfolder_name}/{file.name}"
                    else:
                        file_path = f"{folder_name}/{file.name}"
                    try:
                        # Check if file already exists
                        url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{file_path}"
                        response = requests.get(url, headers={"Authorization": f"token {token}"})
                        response.raise_for_status()
                        st.warning(f"File '{file.name}' already exists at '{folder_name}'.")
                    except requests.exceptions.HTTPError as err:
                        if err.response.status_code == 404:
                            # File does not exist, proceed with upload
                            content = file.getvalue()
                            url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{file_path}"
                            response = requests.put(url, headers={"Authorization": f"token {token}"}, json={
                                "message": f"Add {file.name}",
                                "content": base64.b64encode(content).decode("utf-8"),
                                "path": file_path
                            })
                            response.raise_for_status()
                            st.success(f"File '{file.name}' uploaded successfully.")
                            # Add to upload history
                            from datetime import datetime
                            st.session_state.upload_history.append({
                                'file': file.name,
                                'folder': folder_name,
                                'time': datetime.now().strftime('%Y-%m-%d %H:%M')
                            })
                        else:
                            st.error(f"Error checking file existence: {err}")
            except Exception as e:
                st.error(f"Error uploading files: {e}")