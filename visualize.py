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
from urllib.parse import quote

warnings.filterwarnings("ignore")

ROOT_EXCLUDED_FILES_VIZ = {".gitattributes", ".gitignore"}

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

GITHUB_REPO_API_VIZ = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data"


def get_repo_contents_viz(token, path=""):
    encoded = quote(path, safe='/') if path else ""
    base = f"{GITHUB_REPO_API_VIZ}/contents"
    url = f"{base}/{encoded}" if encoded else base
    response = requests.get(url, headers={"Authorization": f"token {token}"}, timeout=30)
    if response.status_code != 200:
        return [], []
    items = response.json()
    folders, files = [], []
    for item in items:
        if item['type'] == 'dir':
            if not path and item['name'] == 'Visualizations':
                continue
            folders.append(item['name'])
        elif item['type'] == 'file':
            if not path and item['name'] in ROOT_EXCLUDED_FILES_VIZ:
                continue
            files.append(item['name'])
    return sorted(folders), sorted(files)


def get_viz_file_content(token, path, file):
    file_path = f"{path}/{file}" if path else file
    encoded = quote(file_path, safe='/')
    url = f"{GITHUB_REPO_API_VIZ}/contents/{encoded}"
    response = requests.get(url, headers={"Authorization": f"token {token}"}, timeout=30)
    if response.status_code != 200:
        return None, f"GitHub returned status {response.status_code}"
    try:
        metadata = response.json()
    except ValueError:
        return None, "Invalid JSON from GitHub"

    if metadata.get("encoding") == "base64" and metadata.get("content"):
        try:
            return base64.b64decode(metadata["content"]), None
        except Exception as exc:
            return None, f"Base64 decode error: {exc}"

    download_url = metadata.get("download_url")
    if download_url:
        r = requests.get(download_url, headers={"Authorization": f"token {token}"}, timeout=60)
        if r.status_code == 200:
            return r.content, None
        return None, f"Download URL returned status {r.status_code}"

    r = requests.get(
        url,
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.raw"},
        timeout=60,
    )
    if r.status_code == 200:
        return r.content, None
    return None, f"Raw content request returned status {r.status_code}"


def render_viz_file_navigation(token):
    levels = []
    current_path = ""
    breadcrumbs = []
    level = 0

    while True:
        folders, files = get_repo_contents_viz(token, current_path)
        options = [""] + [f"[Folder] {f}" for f in folders] + [f"[File] {f}" for f in files]
        if len(options) == 1:
            break

        key = f"viz_nav_level_{level}"
        label = "Select a folder or file:" if level == 0 else f"Level {level + 1}:"

        if key in st.session_state and st.session_state[key] not in options:
            st.session_state[key] = ""

        levels.append((label, options, key))

        stored = st.session_state.get(key, "")
        if not stored:
            break

        item_type, item_name = stored.split("] ", 1)
        if item_type == "[Folder":
            breadcrumbs.append(item_name)
            current_path = "/".join(breadcrumbs)
            level += 1
        else:
            break

    for row_start in range(0, len(levels), 3):
        row_levels = levels[row_start:row_start + 3]
        cols = st.columns(3)
        for col_idx, (lbl, opts, k) in enumerate(row_levels):
            with cols[col_idx]:
                st.selectbox(lbl, opts, key=k,
                             format_func=lambda item: item or "Choose an item")

    breadcrumbs = []
    selected_file = None
    for _, _, k in levels:
        stored = st.session_state.get(k, "")
        if not stored:
            break
        item_type, item_name = stored.split("] ", 1)
        if item_type == "[Folder":
            breadcrumbs.append(item_name)
        else:
            selected_file = item_name
            break

    selected_path = "/".join(breadcrumbs)
    selected_file_path = (
        f"{selected_path}/{selected_file}" if selected_path and selected_file else selected_file
    )
    return selected_path, selected_file, selected_file_path


# Legacy stub kept for any future internal call-sites
def get_github_file_content(token, path, file):
    content, _ = get_viz_file_content(token, path, file)
    return content


def main():

    # Use token provided in session_state by the wrapper page
    token = st.session_state.get('gh_token', None)
    if not token:
        st.warning("Please provide your security token on the Visualizations page to proceed.")
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
        selected_path, file_name, selected_file_path = render_viz_file_navigation(token)
        if selected_file_path:
            st.caption(f"Selected: {selected_file_path}")

        if file_name:
            file_content, file_error = get_viz_file_content(token, selected_path, file_name)
            if file_content is None:
                st.error(f"Unable to load: {selected_file_path or file_name}")
                if file_error:
                    st.caption(f"Details: {file_error}")
            else:
                if file_name.endswith(("xls", "xlsx")):
                    try:
                        excel_data = pd.ExcelFile(BytesIO(file_content))
                        sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names, key="viz_sheet")
                        if sheet_name:
                            df = excel_data.parse(sheet_name)
                    except Exception as exc:
                        st.error(f"Unable to read Excel file: {exc}")
                elif file_name.endswith(("csv", "dat", "txt")):
                    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                        try:
                            df = pd.read_csv(StringIO(file_content.decode(enc)))
                            break
                        except Exception:
                            continue
                    if df is None:
                        st.error("Unable to parse the file.")

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
            chart_style = st.selectbox("Chart Style:", ["Default", "Seaborn", "ggplot (R-style)", "FiveThirtyEight", "Dark Mode"])

        # Maintain visualization state after interactions
        if 'visualization_buffer' not in st.session_state:
            st.session_state['visualization_buffer'] = None

        if st.button("Generate Visualization"):
            # Apply the selected style
            if chart_style == "Default":
                plt.style.use('default')
            elif chart_style == "Seaborn":
                plt.style.use('seaborn-v0_8')
            elif chart_style == "ggplot (R-style)":
                plt.style.use('ggplot')
            elif chart_style == "FiveThirtyEight":
                plt.style.use('fivethirtyeight')
            elif chart_style == "Dark Mode":
                plt.style.use('dark_background')

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
        visualization_name = st.text_input("Enter a name for the visualization:", key="visualization_name")
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