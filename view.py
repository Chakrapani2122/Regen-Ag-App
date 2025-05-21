import streamlit as st
import pandas as pd
import requests
from io import BytesIO, StringIO

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

def get_github_files(token, folder):
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{folder}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [item['name'] for item in response.json() if item['type'] == 'file']
    return []

def get_github_file_content(token, folder, file):
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{folder}/{file}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        import base64
        content = response.json()['content']
        return base64.b64decode(content)
    return None

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

    col1, col2, col3 = st.columns(3)
    with col1:
        folders = get_github_folders(token)
        folder_name = st.selectbox("Select a folder:", folders)
    if folder_name:
        with col2:
            files = get_github_files(token, folder_name)
            file_name = st.selectbox("Select a file:", files)
    else:
        file_name = None
    sheet_name = None
    df = None
    if file_name and file_name.endswith(("xls", "xlsx")):
        file_content = get_github_file_content(token, folder_name, file_name)
        if file_content:
            excel_data = pd.ExcelFile(BytesIO(file_content))
            with col3:
                sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names)
            if sheet_name:
                df = excel_data.parse(sheet_name)
    elif file_name and file_name.endswith("csv"):
        file_content = get_github_file_content(token, folder_name, file_name)
        if file_content:
            df = pd.read_csv(StringIO(file_content.decode("utf-8")))
    elif file_name:
        st.warning("Only Excel and CSV files are supported for preview.")

    if df is not None:
        with st.expander("File Display", expanded=True):
            st.dataframe(df, height=700)
        # Only show Data Types and Summary if sheet_name is not 'Metadata'
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
                st.write("**Descriptive statistics:**")
                st.write(df.describe(include='all'))

if __name__ == "__main__":
    main()