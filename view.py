import streamlit as st
import pandas as pd
from github import Github
from io import StringIO, BytesIO

def main():
    st.title("View Data")
    st.write("*Access only to team members.*")

    # Step 1: Ask for GitHub security token
    token = st.text_input("Enter security token:", type="password")
    if not token:
        st.warning("Please provide your security token to proceed.")
        return

    # Step 2: Validate the token
    try:
        g = Github(token)
        repo = g.get_repo("Chakrapani2122/Regen-Ag-Data")
        st.success("Token validated successfully!")
    except Exception as e:
        st.error(f"Invalid token or access issue: {e}")
        return

    # Step 3: List files and folders in the repository
    try:
        contents = repo.get_contents("")
        folders = [content.path for content in contents if content.type == "dir"]
        files = [content.path for content in contents if content.type == "file"]

        # Step 3: Organize dropdowns in a table with 3 columns and 2 rows
        col1, col2, col3 = st.columns(3)

        with col1:
            folder_name = st.selectbox("Select a folder:", folders)

        if folder_name:
            folder_contents = repo.get_contents(folder_name)
            folder_files = [content.path for content in folder_contents if content.type == "file"]

            with col2:
                file_name = st.selectbox("Select a file:", folder_files)

            if file_name:
                file_content = repo.get_contents(file_name).decoded_content
                if file_name.endswith(("xls", "xlsx")):
                    excel_data = pd.ExcelFile(BytesIO(file_content))

                    with col3:
                        sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names)

                    # Step 4: Display the selected file
                    with st.expander("File Display"):
                        if sheet_name:
                            df = excel_data.parse(sheet_name)
                            st.write(df)
                        else:
                            st.warning("No sheet selected.")

                    # Step 5: Display column names and data types
                    with st.expander("Data Types"):
                        if sheet_name:
                            df = excel_data.parse(sheet_name)
                            if not df.empty:
                                col_data = []
                                for col in df.columns:
                                    col_data.append((col, str(df[col].dtype)))

                                # Organize data into a table with 4 columns
                                col1, col2, col3, col4 = st.columns(4)
                                for i, (col_name, col_type) in enumerate(col_data):
                                    if i % 4 == 0:
                                        col1.write(f"**{col_name}** : \n{col_type}")
                                    elif i % 4 == 1:
                                        col2.write(f"**{col_name}** : \n{col_type}")
                                    elif i % 4 == 2:
                                        col3.write(f"**{col_name}** : \n{col_type}")
                                    elif i % 4 == 3:
                                        col4.write(f"**{col_name}** : \n{col_type}")
                        else:
                            st.warning("No sheet selected.")
                else:
                    st.warning("Please select a valid Excel file.")
    except Exception as e:
        st.error(f"Error fetching contents: {e}")