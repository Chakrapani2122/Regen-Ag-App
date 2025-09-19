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
import warnings
import numpy as np

warnings.filterwarnings("ignore")

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

def get_github_file_content(token, path, file):
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{path}/{file}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        import base64
        content = response.json()['content']
        return base64.b64decode(content)
    return None

def main():
    st.title("Visualize Your Data")
    st.write("*Access only to team members.*")

    # Step 1: GitHub Token Validation
    token = st.text_input("Enter your security token:", type="password")
    if not token:
        st.warning("Please provide your security token to proceed.")
        return

    if validate_github_token(token):
        st.success("Token validated successfully!")
    else:
        st.error("Invalid token or access issue.")
        return

    # Step 2: File Selection
    action = st.radio("Choose an action:", ("Upload a file", "Select a file"))
    df = None

    if action == "Upload a file":
        uploaded_file = st.file_uploader("Upload your file (xls, xlsx, csv, dat, txt):", 
                                        type=["xls", "xlsx", "csv", "dat", "txt"])
        if uploaded_file:
            st.success(f"File '{uploaded_file.name}' uploaded successfully.")
            if uploaded_file.name.endswith(("xls", "xlsx")):
                excel_data = pd.ExcelFile(uploaded_file)
                sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names)
                df = excel_data.parse(sheet_name) if sheet_name else None
    elif action == "Select a file":
        try:
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
                elif file_name.endswith(("csv", "dat", "txt")):
                    if file_content:
                        df = pd.read_csv(StringIO(file_content.decode("utf-8")))

        except Exception as e:
            st.error(f"Error fetching repository contents: {e}")
            return

    if df is not None:
        with st.expander("Data Preview", expanded=True):
            st.write(df)

        # Step 3: Visualization Creation
        st.write("### 📈 Visualization Configuration")
        
        # Quick insights
        with st.expander("💡 Quick Data Insights"):
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                st.write(f"**Numeric columns:** {len(numeric_cols)}")
                st.write(f"**Highest correlation:** {df[numeric_cols].corr().abs().unstack().sort_values(ascending=False).iloc[1]:.3f}")
                st.write(f"**Missing values:** {df.isnull().sum().sum()}")
        
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            x_axis = st.multiselect("Select columns for X-axis:", options=df.columns.tolist())

        with col2:
            y_axis = st.multiselect("Select columns for Y-axis:", options=df.columns.tolist())

        with col3:
            plot_type = st.selectbox("Select the type of visualization:", [
                "Line Plot", "Bar Plot", "Scatter Plot", "Histogram", "Box Plot", "Heatmap", "Violin Plot", "Pair Plot", "Trend Analysis"
            ])
            
        with col4:
            chart_style = st.selectbox("Chart Style:", ["Default", "Scientific", "Presentation"])

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
                
            elif plot_type == "Trend Analysis":
                for y in y_axis:
                    ax.plot(df[x_axis[0]], df[y], label=y, marker='o')
                    # Add trend line
                    z = np.polyfit(range(len(df)), df[y], 1)
                    p = np.poly1d(z)
                    ax.plot(df[x_axis[0]], p(range(len(df))), "--", alpha=0.7, label=f"{y} trend")
                ax.set_title("Trend Analysis")

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

        # Add download options
        if st.session_state['visualization_buffer']:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="💾 Download PNG",
                    data=st.session_state['visualization_buffer'].getvalue(),
                    file_name="visualization.png",
                    mime="image/png"
                )
            with col2:
                # Export data used in visualization
                if x_axis and y_axis:
                    export_df = df[x_axis + y_axis]
                    csv = export_df.to_csv(index=False)
                    st.download_button(
                        label="📄 Download Data (CSV)",
                        data=csv,
                        file_name="visualization_data.csv",
                        mime="text/csv"
                    )

        # Statistical summary for the visualization
        if st.session_state['visualization_buffer'] and len(y_axis) > 0:
            with st.expander("📊 Statistical Summary"):
                for col in y_axis:
                    if col in df.columns and df[col].dtype in ['int64', 'float64']:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric(f"{col} Mean", f"{df[col].mean():.2f}")
                        with col2:
                            st.metric(f"{col} Std", f"{df[col].std():.2f}")
                        with col3:
                            st.metric(f"{col} Min", f"{df[col].min():.2f}")
                        with col4:
                            st.metric(f"{col} Max", f"{df[col].max():.2f}")
        
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
                            "content": base64.b64encode(st.session_state['visualization_buffer'].getvalue()).decode("utf-8"),
                            "sha": None  # Always set sha to None for new files
                        }
                    )
                    response.raise_for_status()

                    xml_path = "Visualizations/visualizations.xml"
                    headers = {"Authorization": f"token {token}"}
                    xml_url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{xml_path}"
                    xml_content = "<Images></Images>"
                    sha = None
                    try:
                        xml_response = requests.get(xml_url, headers=headers)
                        if xml_response.status_code == 200:
                            xml_json = xml_response.json()
                            xml_content = base64.b64decode(xml_json["content"]).decode("utf-8")
                            sha = xml_json["sha"]
                            if not xml_content.strip():
                                xml_content = "<Images></Images>"
                    except Exception:
                        pass

                    root = ET.fromstring(xml_content)
                    new_image = ET.SubElement(root, "Image")
                    ET.SubElement(new_image, "Name").text = f"{visualization_name}.png"
                    ET.SubElement(new_image, "Path").text = visualization_path
                    ET.SubElement(new_image, "Description").text = visualization_description
                    creation_date = datetime.now().strftime("%Y-%m-%d")
                    ET.SubElement(new_image, "Date").text = creation_date

                    updated_xml_content = ET.tostring(root, encoding="unicode")
                    put_data = {
                        "message": f"Update visualizations.xml with {visualization_name}",
                        "content": base64.b64encode(updated_xml_content.encode("utf-8")).decode("utf-8")
                    }
                    if sha:
                        put_data["sha"] = sha
                    put_response = requests.put(xml_url, headers=headers, json=put_data)
                    put_response.raise_for_status()

                    st.success(f"Visualization '{visualization_name}' uploaded successfully.")
                except Exception as e:
                    st.error(f"Error uploading visualization: {e}")
    else:
        st.warning("No data available for visualization. Please upload or select a file first.")

if __name__ == "__main__":
    main()