import streamlit as st
import pandas as pd
import requests
from io import BytesIO, StringIO
import matplotlib.pyplot as plt
import seaborn as sns
from xml.etree import ElementTree as ET
import io
from datetime import datetime
import base64

def validate_github_token(token):
    headers = {"Authorization": f"token {token}"}
    url = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data"
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def main():
    st.title("Visualize Your Data")
    st.write("*Access only to team members.*")

    # Step 1: GitHub Token Validation
    token = st.text_input("Enter your GitHub security token:", type="password")
    if not token:
        st.warning("Please provide your GitHub security token to proceed.")
        return

    if validate_github_token(token):
        st.success("Token validated successfully!")
    else:
        st.error("Invalid token or repository access issue.")
        return

    # Step 2: File Selection
    action = st.radio("Choose an action:", ("Upload a file", "Select a file from GitHub"))

    if action == "Upload a file":
        uploaded_file = st.file_uploader("Upload your file (xls, xlsx, csv, dat, txt):", 
                                        type=["xls", "xlsx", "csv", "dat", "txt"])
        if uploaded_file:
            st.success(f"File '{uploaded_file.name}' uploaded successfully.")
            if uploaded_file.name.endswith(("xls", "xlsx")):
                excel_data = pd.ExcelFile(uploaded_file)
                sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names)
                df = excel_data.parse(sheet_name) if sheet_name else None
    elif action == "Select a file from GitHub":
        try:
            # GitHub API call to get repository contents
            url = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/"
            headers = {"Authorization": f"token {token}"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            contents = response.json()

            folders = [content['path'] for content in contents if content['type'] == "dir" and content['path'] != "Visualizations"]

            # Organize folder, file, and sheet selection in a table with 3 columns and 2 rows
            col1, col2, col3 = st.columns(3)

            with col1:
                folder_name = st.selectbox("Select a folder:", folders)

            if folder_name:
                # GitHub API call to get folder contents
                url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{folder_name}"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                folder_contents = response.json()
                folder_files = [content['path'] for content in folder_contents if content['type'] == "file"]

                with col2:
                    file_name = st.selectbox("Select a file:", folder_files)

                if file_name and file_name.endswith(("xls", "xlsx")):
                    # GitHub API call to get file content
                    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{file_name}"
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    file_content = response.json()['content']
                    excel_data = pd.ExcelFile(BytesIO(base64.b64decode(file_content)))

                    with col3:
                        sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names)
                        df = excel_data.parse(sheet_name) if sheet_name else None
        except Exception as e:
            st.error(f"Error fetching repository contents: {e}")
            return

    if 'df' in locals() and df is not None:
        st.write("### Data Preview")
        st.write(df)

        # Step 3: Visualization Creation
        col1, col2, col3 = st.columns(3)

        with col1:
            x_axis = st.multiselect("Select columns for X-axis:", options=df.columns.tolist())

        with col2:
            y_axis = st.multiselect("Select columns for Y-axis:", options=df.columns.tolist())

        with col3:
            plot_type = st.selectbox("Select the type of visualization:", [
                "Line Plot", "Bar Plot", "Scatter Plot", "Histogram", "Box Plot", "Heatmap", "Violin Plot", "Pair Plot"
            ])

        # Maintain visualization state after interactions
        if 'visualization_buffer' not in st.session_state:
            st.session_state['visualization_buffer'] = None

        if st.button("Generate Visualization"):
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

            elif plot_type == "Box Plot":
                sns.boxplot(data=df[y_axis], ax=ax)
                ax.set_title("Box Plot")

            elif plot_type == "Heatmap":
                sns.heatmap(df.corr(), annot=True, cmap="coolwarm", ax=ax)
                ax.set_title("Heatmap")

            elif plot_type == "Violin Plot":
                sns.violinplot(data=df[y_axis], ax=ax)
                ax.set_title("Violin Plot")

            elif plot_type == "Pair Plot":
                sns.pairplot(df[x_axis + y_axis])
                st.pyplot()  # Pair plot creates its own figure
                return

            ax.set_xlabel(", ".join(x_axis))
            ax.set_ylabel(", ".join(y_axis))
            ax.legend()

            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            st.session_state['visualization_buffer'] = buf

        # Display the visualization if it exists
        if st.session_state['visualization_buffer']:
            buf = st.session_state['visualization_buffer']
            buf.seek(0)  # Ensure the buffer is at the start
            image = plt.imread(buf, format='png')
            st.image(image, caption="Generated Visualization", use_column_width=True)

        # Add a download button above the name input label
        if st.session_state['visualization_buffer']:
            st.download_button(
                label="Download Visualization",
                data=st.session_state['visualization_buffer'].getvalue(),
                file_name="visualization.png",
                mime="image/png"
            )

        # Add inputs for visualization name and description
        visualization_name = st.text_input("Enter a name for the visualization:")
        visualization_description = st.text_area("Enter a description for the visualization:")

        # Add an upload button
        if st.button("Upload Visualization"):
            if not visualization_name or not visualization_description:
                st.warning("Please provide both a name and a description for the visualization.")
            else:
                try:
                    visualization_path = f"Visualizations/{visualization_name}.png"
                    # GitHub API call to create or update file
                    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{visualization_path}"
                    response = requests.put(
                        url,
                        headers={"Authorization": f"token {token}"},
                        json={
                            "message": f"Add visualization {visualization_name}",
                            "content": st.session_state['visualization_buffer'].getvalue().decode("utf-8"),
                            "sha": None  # Always set sha to None for new files
                        }
                    )
                    response.raise_for_status()

                    xml_path = "Visualizations/visualizations.xml"
                    # Handle the case where the XML file does not exist or is empty
                    try:
                        xml_file = repo.get_contents(xml_path)
                        xml_content = xml_file.decoded_content.decode("utf-8")
                        sha = xml_file.sha  # Always get sha if file exists
                        if not xml_content.strip():
                            # If file is empty, initialize with root and update with sha
                            xml_content = "<Images></Images>"
                            repo.update_file(
                                xml_path,
                                "Initialize visualizations.xml",
                                xml_content,
                                sha=sha
                            )
                            # Re-fetch to get new sha after update
                            xml_file = repo.get_contents(xml_path)
                            xml_content = xml_file.decoded_content.decode("utf-8")
                            sha = xml_file.sha
                    except Exception:
                        xml_content = "<Images></Images>"
                        sha = None  # No sha since the file does not exist

                    root = ET.fromstring(xml_content)
                    new_image = ET.SubElement(root, "Image")
                    ET.SubElement(new_image, "Name").text = f"{visualization_name}.png"
                    ET.SubElement(new_image, "Path").text = visualization_path
                    ET.SubElement(new_image, "Description").text = visualization_description
                    creation_date = datetime.now().strftime("%Y-%m-%d")
                    ET.SubElement(new_image, "Date").text = creation_date

                    updated_xml_content = ET.tostring(root, encoding="unicode")
                    if sha:
                        repo.update_file(
                            xml_path,
                            f"Update visualizations.xml with {visualization_name}",
                            updated_xml_content,
                            sha=sha
                        )
                    else:
                        repo.create_file(
                            xml_path,
                            f"Create visualizations.xml with {visualization_name}",
                            updated_xml_content
                        )

                    st.success(f"Visualization '{visualization_name}' uploaded successfully.")
                except Exception as e:
                    st.error(f"Error uploading visualization: {e}")
    else:
        st.warning("No data available for visualization. Please upload or select a file first.")

if __name__ == "__main__":
    main()