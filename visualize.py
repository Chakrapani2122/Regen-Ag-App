import streamlit as st
import pandas as pd
from github import Github
from io import StringIO, BytesIO

def main():
    st.title("Visualize your Data")
    st.write("*Access only to team members.*")

    # Step 1: Ask for GitHub security token
    token = st.text_input("Enter your GitHub security token:", type="password")
    if not token:
        st.warning("Please provide your GitHub security token to proceed.")
        return

    # Step 2: Validate the token
    try:
        g = Github(token)
        repo = g.get_repo("Chakrapani2122/Regen-Ag-Data")
        st.success("Token validated successfully!")
    except Exception as e:
        st.error(f"Invalid token or repository access issue: {e}")
        return

    # Step 3: Ask user to upload a file or select from GitHub
    action = st.radio("Choose an action:", ("Upload a file", "Select a file from GitHub"))

    if action == "Upload a file":
        uploaded_file = st.file_uploader("Upload your file (xls, xlsx, csv, dat, txt):", 
                                        type=["xls", "xlsx", "csv", "dat", "txt"])
        if uploaded_file:
            st.success(f"File '{uploaded_file.name}' uploaded successfully.")
            if uploaded_file.name.endswith(("xls", "xlsx")):
                excel_data = pd.ExcelFile(uploaded_file)
                sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names)

                # Display file contents
                with st.expander("File Display"):
                    if sheet_name:
                        df = excel_data.parse(sheet_name)
                        st.write(df)

                # Display column names and data types
                with st.expander("Column Names and Data Types"):
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
                                    col1.write(f"{col_name} : \n{col_type}")
                                elif i % 4 == 1:
                                    col2.write(f"{col_name} : \n{col_type}")
                                elif i % 4 == 2:
                                    col3.write(f"{col_name} : \n{col_type}")
                                elif i % 4 == 3:
                                    col4.write(f"{col_name} : \n{col_type}")
    elif action == "Select a file from GitHub":
        try:
            contents = repo.get_contents("")
            folders = [content.path for content in contents if content.type == "dir"]

            # Organize dropdowns in a table with 3 columns
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

                        # Display file contents
                        with st.expander("File Display"):
                            if sheet_name:
                                df = excel_data.parse(sheet_name)
                                st.write(df)

                        # Display column names and data types
                        with st.expander("Column Names and Data Types"):
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
        except Exception as e:
            st.error(f"Error fetching repository contents: {e}")

    # Step 6: Visualization creation
    with st.expander("Create Visualizations"):
        if 'df' in locals() and not df.empty:
            x_axis = st.multiselect("Select columns for X-axis:", options=df.columns.tolist())
            y_axis = st.multiselect("Select columns for Y-axis:", options=df.columns.tolist())

            plot_type = st.selectbox("Select the type of visualization:", ["Line Plot", "Bar Plot", "Scatter Plot", "Histogram"])

            if st.button("Generate Visualization"):
                if not x_axis or not y_axis:
                    st.warning("Please select at least one column for both X-axis and Y-axis.")
                else:
                    import matplotlib.pyplot as plt
                    import io

                    fig, ax = plt.subplots()

                    if plot_type == "Line Plot":
                        for y in y_axis:
                            ax.plot(df[x_axis[0]], df[y], label=y)
                        ax.set_title("Line Plot")

                    elif plot_type == "Bar Plot":
                        for y in y_axis:
                            ax.bar(df[x_axis[0]], df[y], label=y)
                        ax.set_title("Bar Plot")

                    elif plot_type == "Scatter Plot":
                        for y in y_axis:
                            ax.scatter(df[x_axis[0]], df[y], label=y)
                        ax.set_title("Scatter Plot")

                    elif plot_type == "Histogram":
                        for x in x_axis:
                            ax.hist(df[x], bins=20, alpha=0.5, label=x)
                        ax.set_title("Histogram")

                    ax.set_xlabel(", ".join(x_axis))
                    ax.set_ylabel(", ".join(y_axis))
                    ax.legend()

                    st.pyplot(fig)

                    # Add a button to download the visualization
                    buf = io.BytesIO()
                    fig.savefig(buf, format="png")
                    buf.seek(0)

                    st.download_button(
                        label="Download Visualization",
                        data=buf,
                        file_name="visualization.png",
                        mime="image/png"
                    )
        else:
            st.warning("No data available for visualization. Please upload or select a file first.")

if __name__ == "__main__":
    main()