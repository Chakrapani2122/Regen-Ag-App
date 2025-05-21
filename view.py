import streamlit as st
import pandas as pd
from github import Github
from io import BytesIO, StringIO
import requests

def validate_github_token(token):
    headers = {"Authorization": f"token {token}"}
    url = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data"
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def main():
    st.title("View Data from GitHub Repository")
    st.write("*Access only to team members.*")

    # Step 1: Ask for GitHub security token
    token = st.text_input("Enter your GitHub security token:", type="password")
    if not token:
        st.warning("Please provide your GitHub security token to proceed.")
        return

    if validate_github_token(token):
        st.success("Token validated successfully!")
    else:
        st.error("Invalid token or repository access issue.")
        return

    # Step 3: List folders (excluding 'Visualizations') and select folder in a table layout
    try:
        g = Github(token)
        repo = g.get_repo("Chakrapani2122/Regen-Ag-Data")
        contents = repo.get_contents("")
        folders = [content.path for content in contents if content.type == "dir" and content.path != "Visualizations"]
        col1, col2, col3 = st.columns(3)
        with col1:
            folder_name = st.selectbox("Select a folder:", folders)
    except Exception as e:
        st.error(f"Error fetching folders: {e}")
        return

    # Step 4: List files in the selected folder and select file in the table layout
    if folder_name:
        try:
            folder_contents = repo.get_contents(folder_name)
            folder_files = [content.path for content in folder_contents if content.type == "file"]
            with col2:
                file_name = st.selectbox("Select a file:", folder_files)
        except Exception as e:
            st.error(f"Error fetching files: {e}")
            return
    else:
        file_name = None

    # Step 5: If file is Excel, select sheet in the table layout
    sheet_name = None
    df = None
    if file_name and file_name.endswith(("xls", "xlsx")):
        try:
            file_content = repo.get_contents(file_name).decoded_content
            excel_data = pd.ExcelFile(BytesIO(file_content))
            with col3:
                sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names)
            if sheet_name:
                df = excel_data.parse(sheet_name)
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
    elif file_name and file_name.endswith("csv"):
        try:
            file_content = repo.get_contents(file_name).decoded_content.decode("utf-8")
            df = pd.read_csv(StringIO(file_content))
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
    elif file_name:
        st.warning("Only Excel and CSV files are supported for preview.")

    # Step 6: Display file and sheet in an expander
    if df is not None:
        with st.expander("File Display", expanded=True):
            st.dataframe(df, height=700)
        with st.expander("Data Types", expanded=False):
            col_data = [(col, str(df[col].dtype)) for col in df.columns]
            col1, col2, col3, col4 = st.columns(4)
            for i, (col_name, col_type) in enumerate(col_data):
                if i % 4 == 0:
                    col1.write(f"**{col_name}**\n{col_type}")
                elif i % 4 == 1:
                    col2.write(f"**{col_name}**\n{col_type}")
                elif i % 4 == 2:
                    col3.write(f"**{col_name}**\n{col_type}")
                elif i % 4 == 3:
                    col4.write(f"**{col_name}**\n{col_type}")

if __name__ == "__main__":
    main()