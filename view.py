import streamlit as st
import pandas as pd
import requests
from io import BytesIO, StringIO
import docx
import seaborn as sns
import matplotlib.pyplot as plt

def validate_github_token(token):
    headers = {"Authorization": f"token {token}"}
    url = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data"
    response = requests.get(url, headers=headers)
    return response.status_code == 200

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

def get_github_files(token, folder):
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{folder}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [item['name'] for item in response.json() if item['type'] == 'file']
    return []

def get_github_file_content(token, path, file):
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{path}/{file}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        import base64
        content = response.json()['content']
        return base64.b64decode(content)
    return None

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

def main():
    st.title("View Data")
    st.write("*Access only to team members.*")

    token = st.text_input("Enter your security token:", type="password")
    if not token:
        st.warning("Please provide your security token to proceed.")
        return

    if not validate_github_token(token):
        st.error("Invalid token or access issue.")
        return
    st.success("Token validated successfully!")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        folders = get_github_folders(token)
        folder_name = st.selectbox("Select a folder:", folders)

    subfolder_name = None
    file_name = None
    
    if folder_name:
        subfolders, files_in_folder = get_folder_contents(token, folder_name)
        
        if subfolders:
            with col2:
                subfolder_name = st.selectbox("Select a subfolder:", [""] + subfolders)
            
            if subfolder_name:
                _, files_in_subfolder = get_folder_contents(token, f"{folder_name}/{subfolder_name}")
                with col3:
                    file_name = st.selectbox("Select a file:", files_in_subfolder)
        else:
            with col2:
                file_name = st.selectbox("Select a file:", files_in_folder)

    sheet_name = None
    df = None
    
    if file_name:
        path = f"{folder_name}/{subfolder_name}" if subfolder_name else folder_name
        file_content = get_github_file_content(token, path, file_name)
        
        if file_name.endswith(("xls", "xlsx")):
            if file_content:
                excel_data = pd.ExcelFile(BytesIO(file_content))
                with col4:
                    sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names)
                if sheet_name:
                    df = excel_data.parse(sheet_name)
        elif file_name.endswith("csv"):
            if file_content:
                df = pd.read_csv(StringIO(file_content.decode("utf-8")))
        elif file_name.endswith("docx"):
            if file_content:
                st.info("Successfully fetched .docx file content.")
                st.write(f"File size: {len(file_content)} bytes")
                
                docx_text = read_docx(file_content)

                if "Error reading .docx file" in docx_text:
                    st.error(docx_text)
                elif not docx_text.strip():
                    st.warning("The .docx file appears to be empty or could not be read.")
                else:
                    st.info("Successfully parsed .docx content.")
                    with st.expander("DOCX Content", expanded=True):
                        st.text_area("Content", docx_text, height=700, label_visibility="hidden")
            else:
                st.warning("Failed to fetch .docx file content.")
        else:
            st.warning("Only Excel, CSV, and DOCX files are supported for preview.")

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