import streamlit as st
import pandas as pd
import os
from github import Github
from io import StringIO, BytesIO

def main():
    st.title("Upload the Data")
    st.write("*Access only to team members.*")

    # Step 1: Ask for GitHub security token
    token = st.text_input("Enter the security token:", type="password")
    if not token:
        st.warning("Please provide the security token to proceed.")
        return

    # Step 2: Validate the token
    try:
        g = Github(token)
        user = g.get_user()
        repo = g.get_repo("Chakrapani2122/Regen-Ag-Data")
        st.success(f"Token validated successfully!")
    except Exception as e:
        st.error(f"Invalid token or access issue: {e}")
        return

    # Step 3: File upload
    uploaded_files = st.file_uploader("Select files to upload (xls, xlsx, csv, dat, txt):", 
                                      type=["xls", "xlsx", "csv", "dat", "txt"], 
                                      accept_multiple_files=True)

    if uploaded_files:
        
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

        # Step 5: List folders in the Regen-Ag-Data repository
        try:
            repo = g.get_repo("Chakrapani2122/Regen-Ag-Data")
            contents = repo.get_contents("")
            # Exclude the 'Visualizations' folder from the list
            folders = [content.path for content in contents if content.type == "dir" and content.path != "Visualizations"]

            if not folders:
                st.warning("No folders found in the repository.")
                return

            folder_name = st.selectbox("Select a folder to upload the files:", folders)
        except Exception as e:
            st.error(f"Error fetching folders: {e}")
            return

        # Step 6: Upload files to GitHub repository
        if st.button("Upload Files"):
            try:
                for file in uploaded_files:
                    file_path = os.path.join(folder_name, file.name)
                    try:
                        # Check if file already exists
                        repo.get_contents(file_path)
                        st.warning(f"File '{file.name}' already exists at '{folder_name}'.")
                    except:
                        # Upload file
                        content = file.getvalue()
                        repo.create_file(file_path, f"Add {file.name}", content)
                        st.success(f"File '{file.name}' uploaded successfully.")
            except Exception as e:
                st.error(f"Error uploading files: {e}")