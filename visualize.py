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
from github_client import get_github_client

warnings.filterwarnings("ignore")

ROOT_EXCLUDED_FILES_VIZ = {".gitattributes", ".gitignore"}

def validate_github_token(token):
    client = get_github_client(token)
    return client.validate_token()

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


def nav_option_value(item_type, name):
    return f"{item_type}|{name}"


def parse_nav_option(option):
    if not option or "|" not in option:
        return None, None
    item_type, item_name = option.split("|", 1)
    return item_type, item_name


def get_file_icon(file_name):
    ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
    icon_by_extension = {
        "xls": "📊",
        "xlsx": "📊",
        "csv": "📈",
        "tsv": "📈",
        "txt": "📄",
        "dat": "📄",
        "docx": "📝",
        "md": "📝",
        "markdown": "📝",
        "pdf": "📕",
        "png": "🖼️",
        "jpg": "🖼️",
        "jpeg": "🖼️",
        "gif": "🖼️",
        "xml": "🧾",
        "json": "🧾",
        "zip": "🗜️",
    }
    return icon_by_extension.get(ext, "📄")


def format_viz_nav_option(option):
    if not option:
        return "Choose an item"
    item_type, item_name = parse_nav_option(option)
    if item_type == "folder":
        return f"📁 {item_name}"
    if item_type == "file":
        return f"{get_file_icon(item_name)} {item_name}"
    return option


@st.cache_data(show_spinner=False, ttl=120)
def get_repo_contents_viz_cached(token, path=""):
    client = get_github_client(token)
    items, error, auth_error = client.list_contents(path)
    if items is None:
        return [], [], error, auth_error

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
    return sorted(folders), sorted(files), None, False


def get_repo_contents_viz(token, path=""):
    folders, files, _, _ = get_repo_contents_viz_cached(token, path)
    return folders, files


def get_viz_file_content(token, path, file):
    file_path = f"{path}/{file}" if path else file
    client = get_github_client(token)
    content, error, auth_error, _ = client.get_file_content(file_path)
    if auth_error:
        st.session_state['gh_token'] = None
        st.session_state['gh_token_validated'] = False
        return None, "Authentication failed or token expired."
    return content, error


def render_viz_file_navigation(token):
    levels = []
    current_path = ""
    breadcrumbs = []
    level = 0

    while True:
        folders, files, error, auth_error = get_repo_contents_viz_cached(token, current_path)
        if auth_error:
            st.session_state['gh_token'] = None
            st.session_state['gh_token_validated'] = False
            st.error("Authentication failed. Please re-enter your security token.")
            return "", None, None
        if error:
            st.warning(error)
            break

        options = [""] + [nav_option_value("folder", f) for f in folders] + [nav_option_value("file", f) for f in files]
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

        item_type, item_name = parse_nav_option(stored)
        if item_type == "folder":
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
                             format_func=format_viz_nav_option)

    breadcrumbs = []
    selected_file = None
    for _, _, k in levels:
        stored = st.session_state.get(k, "")
        if not stored:
            break
        item_type, item_name = parse_nav_option(stored)
        if item_type == "folder":
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


_CHART_TYPES = [
    "Line Plot", "Bar Plot", "Scatter Plot", "Histogram",
    "Box Plot", "Heatmap", "Violin Plot", "Trend Analysis",
]
_CHART_STYLES = ["Default", "Seaborn", "ggplot (R-style)", "FiveThirtyEight", "Dark Mode"]
_CHART_STYLE_MAP = {
    "Default": "default",
    "Seaborn": "seaborn-v0_8",
    "ggplot (R-style)": "ggplot",
    "FiveThirtyEight": "fivethirtyeight",
    "Dark Mode": "dark_background",
}


def _apply_chart_style(style):
    plt.style.use(_CHART_STYLE_MAP.get(style, "default"))


def _render_chart_on_ax(df, x_axis, y_axis, plot_type, ax, custom_title=None, custom_x_label=None, custom_y_label=None):
    """Render a single chart type onto ax. Returns False for Pair Plot (unsupported on an axis)."""
    default_title = plot_type
    if plot_type == "Line Plot":
        for y in y_axis:
            ax.plot(df[x_axis[0]], df[y], label=y)
        default_title = "Line Plot"
    elif plot_type == "Bar Plot":
        for y in y_axis:
            ax.bar(df[x_axis[0]], df[y], label=y)
        default_title = "Bar Plot"
    elif plot_type == "Scatter Plot":
        for y in y_axis:
            ax.scatter(df[x_axis[0]], df[y], label=y)
        default_title = "Scatter Plot"
    elif plot_type == "Histogram":
        for x in x_axis:
            ax.hist(df[x], bins=20, alpha=0.5, label=x)
        default_title = "Histogram"
    elif plot_type == "Box Plot":
        sns.boxplot(data=df[y_axis], ax=ax)
        default_title = "Box Plot"
    elif plot_type == "Heatmap":
        sns.heatmap(df.corr(numeric_only=True), annot=True, cmap="coolwarm", ax=ax)
        default_title = "Heatmap"
    elif plot_type == "Violin Plot":
        sns.violinplot(data=df[y_axis], ax=ax)
        default_title = "Violin Plot"
    elif plot_type == "Trend Analysis":
        for y in y_axis:
            ax.plot(df[x_axis[0]], df[y], label=y, marker='o')
            z = np.polyfit(range(len(df)), df[y], 1)
            p = np.poly1d(z)
            ax.plot(df[x_axis[0]], p(range(len(df))), "--", alpha=0.7, label=f"{y} trend")
        default_title = "Trend Analysis"
    elif plot_type == "Pair Plot":
        return False
    
    ax.set_title(custom_title if custom_title else default_title)
    ax.set_xlabel(custom_x_label if custom_x_label else (", ".join(x_axis) if x_axis else ""))
    ax.set_ylabel(custom_y_label if custom_y_label else (", ".join(y_axis) if y_axis else ""))
    ax.legend()
    return True


def _fig_to_buffer(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return buf


def main():

    # Use token provided in session_state by the wrapper page
    token = st.session_state.get('gh_token', None)
    if not token:
        st.warning("Please provide your security token on the Visualizations page to proceed.")
        return

    # Step 2: File Selection
    action = st.radio("Choose an action:", ("Upload a file", "Select a file"), key="viz_action_radio")
    df = None

    if action == "Upload a file":
        uploaded_file = st.file_uploader("Upload your file (xls, xlsx, csv, dat, txt):",
                                        type=["xls", "xlsx", "csv", "dat", "txt"],
                                        key="viz_file_uploader")
        if uploaded_file:
            st.success(f"File '{uploaded_file.name}' uploaded successfully.")
            if uploaded_file.name.endswith(("xls", "xlsx")):
                excel_data = pd.ExcelFile(uploaded_file)
                sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names)
                df = excel_data.parse(sheet_name) if sheet_name else None
            elif uploaded_file.name.endswith(("csv", "dat", "txt")):
                raw = uploaded_file.read()
                for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                    try:
                        df = pd.read_csv(StringIO(raw.decode(enc)))
                        break
                    except Exception:
                        continue
                if df is None:
                    st.error("Unable to parse the uploaded file.")
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

    # Persist df across page navigations
    if df is not None:
        st.session_state['viz_df'] = df
        st.session_state['viz_df_source'] = action
    elif st.session_state.get('viz_df') is not None and st.session_state.get('viz_df_source') == action:
        df = st.session_state['viz_df']

    if df is not None:
        with st.expander("Data Preview", expanded=True):
            st.write(df)
        # ---- Comparative Visualization Mode ----------------------------------------
        compare_mode = st.checkbox(
            "🔀 Comparative Visualization — show two charts side by side",
            key="compare_mode_cb",
        )

        if compare_mode:
            st.write("### Comparative Visualization")

            _ac1, _ac2, _ = st.columns([1, 1, 2])
            with _ac1:
                align_x = st.checkbox(
                    "Align X-axis",
                    key="cmp_align_x",
                    help="Force both charts to share the same X-axis range",
                )
            with _ac2:
                align_y = st.checkbox(
                    "Align Y-axis",
                    key="cmp_align_y",
                    help="Force both charts to share the same Y-axis range",
                )

            st.markdown("**Chart 1**")
            _cc1, _cc2, _cc3, _cc4 = st.columns(4)
            with _cc1:
                x1 = st.multiselect("X-axis:", options=df.columns.tolist(), key="cmp_x1")
            with _cc2:
                y1 = st.multiselect("Y-axis:", options=df.columns.tolist(), key="cmp_y1")
            with _cc3:
                pt1 = st.selectbox("Chart type:", _CHART_TYPES, key="cmp_pt1")
            with _cc4:
                cs1 = st.selectbox("Style:", _CHART_STYLES, key="cmp_cs1")

            st.markdown("**Chart 2**")
            _cd1, _cd2, _cd3, _cd4 = st.columns(4)
            with _cd1:
                x2 = st.multiselect("X-axis:", options=df.columns.tolist(), key="cmp_x2")
            with _cd2:
                y2 = st.multiselect("Y-axis:", options=df.columns.tolist(), key="cmp_y2")
            with _cd3:
                pt2 = st.selectbox("Chart type:", _CHART_TYPES, key="cmp_pt2")
            with _cd4:
                cs2 = st.selectbox("Style:", _CHART_STYLES, key="cmp_cs2")

            st.markdown("**Customization**")
            _cmp_cust1, _cmp_cust2, _cmp_cust3 = st.columns(3)
            with _cmp_cust1:
                cmp_title1 = st.text_input("Chart 1 Title (optional):", key="cmp_title1")
            with _cmp_cust2:
                cmp_title2 = st.text_input("Chart 2 Title (optional):", key="cmp_title2")
            with _cmp_cust3:
                cmp_x_label = st.text_input("X-Axis Label (optional):", key="cmp_x_label")
            
            _cmp_y_label = st.text_input("Y-Axis Label (optional):", key="cmp_y_label")

            if "cmp_buf_combined" not in st.session_state:
                st.session_state["cmp_buf_combined"] = None

            if st.button("Generate Comparative Visualization", key="cmp_generate"):
                def _needs_x(pt):
                    return pt not in ("Histogram", "Box Plot", "Violin Plot", "Heatmap")
                def _needs_y(pt):
                    return pt not in ("Histogram",)

                _errs = []
                if _needs_x(pt1) and not x1:
                    _errs.append("Chart 1: select at least one X-axis column")
                if _needs_y(pt1) and not y1:
                    _errs.append("Chart 1: select at least one Y-axis column")
                if _needs_x(pt2) and not x2:
                    _errs.append("Chart 2: select at least one X-axis column")
                if _needs_y(pt2) and not y2:
                    _errs.append("Chart 2: select at least one Y-axis column")

                if _errs:
                    for _e in _errs:
                        st.warning(_e)
                else:
                    try:
                        _apply_chart_style(cs1)
                        _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(14, 6))
                        _ok1 = _render_chart_on_ax(
                            df, x1, y1, pt1, _ax1,
                            custom_title=cmp_title1 if cmp_title1 else None,
                            custom_x_label=cmp_x_label if cmp_x_label else None,
                            custom_y_label=_cmp_y_label if _cmp_y_label else None
                        )
                        _ok2 = _render_chart_on_ax(
                            df, x2, y2, pt2, _ax2,
                            custom_title=cmp_title2 if cmp_title2 else None,
                            custom_x_label=cmp_x_label if cmp_x_label else None,
                            custom_y_label=_cmp_y_label if _cmp_y_label else None
                        )

                        if not _ok1 or not _ok2:
                            st.warning("Pair Plot is not supported in comparative mode.")
                        else:
                            if align_x:
                                _xmin = min(_ax1.get_xlim()[0], _ax2.get_xlim()[0])
                                _xmax = max(_ax1.get_xlim()[1], _ax2.get_xlim()[1])
                                _ax1.set_xlim(_xmin, _xmax)
                                _ax2.set_xlim(_xmin, _xmax)
                            if align_y:
                                _ymin = min(_ax1.get_ylim()[0], _ax2.get_ylim()[0])
                                _ymax = max(_ax1.get_ylim()[1], _ax2.get_ylim()[1])
                                _ax1.set_ylim(_ymin, _ymax)
                                _ax2.set_ylim(_ymin, _ymax)
                            _fig.suptitle("Comparative Visualization", fontsize=13)
                            _fig.tight_layout()
                            st.session_state["cmp_buf_combined"] = _fig_to_buffer(_fig)
                    except Exception as _exc:
                        st.error(f"Error generating comparative visualization: {_exc}")
                    finally:
                        plt.close("all")

            _bc = st.session_state.get("cmp_buf_combined")
            if _bc:
                _bc.seek(0)
                st.image(_bc.read(), caption="Comparative Visualization", use_column_width=True)

                st.download_button(
                    "💾 Download Combined Visualization (PNG)",
                    data=st.session_state["cmp_buf_combined"].getvalue(),
                    file_name="comparative_visualization.png",
                    mime="image/png",
                    key="dl_cmp_combined",
                )

                st.markdown("---")
                st.markdown("#### Upload Comparative Visualization")
                _cmp_name = st.text_input("Enter a name for the visualization:", key="cmp_viz_name")
                _cmp_desc = st.text_area("Enter a description for the visualization:", key="cmp_viz_desc")
                if st.button("Upload Comparative Visualization", key="cmp_upload_btn"):
                    if not _cmp_name or not _cmp_desc:
                        st.warning("Please provide both a name and a description for the visualization.")
                    else:
                        try:
                            _cmp_path = f"Visualizations/{_cmp_name}.png"
                            _up_url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{_cmp_path}"
                            _up_resp = requests.put(
                                _up_url,
                                headers={"Authorization": f"token {token}"},
                                json={
                                    "message": f"Add visualization {_cmp_name}",
                                    "content": base64.b64encode(st.session_state["cmp_buf_combined"].getvalue()).decode("utf-8"),
                                    "sha": None,
                                },
                            )
                            _up_resp.raise_for_status()

                            _xml_path = "Visualizations/visualizations.xml"
                            _xml_headers = {"Authorization": f"token {token}"}
                            _xml_url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{_xml_path}"
                            _xml_content = "<Images></Images>"
                            _xml_sha = None
                            try:
                                _xml_resp = requests.get(_xml_url, headers=_xml_headers)
                                if _xml_resp.status_code == 200:
                                    _xml_json = _xml_resp.json()
                                    _xml_content = base64.b64decode(_xml_json["content"]).decode("utf-8")
                                    _xml_sha = _xml_json["sha"]
                                    if not _xml_content.strip():
                                        _xml_content = "<Images></Images>"
                            except Exception:
                                pass

                            _root = ET.fromstring(_xml_content)
                            _new_img = ET.SubElement(_root, "Image")
                            ET.SubElement(_new_img, "Name").text = f"{_cmp_name}.png"
                            ET.SubElement(_new_img, "Path").text = _cmp_path
                            ET.SubElement(_new_img, "Description").text = _cmp_desc
                            ET.SubElement(_new_img, "Date").text = datetime.now().strftime("%Y-%m-%d")

                            _upd_xml = ET.tostring(_root, encoding="unicode")
                            _xml_put_data = {
                                "message": f"Update visualizations.xml with {_cmp_name}",
                                "content": base64.b64encode(_upd_xml.encode("utf-8")).decode("utf-8"),
                            }
                            if _xml_sha:
                                _xml_put_data["sha"] = _xml_sha
                            _xml_put = requests.put(_xml_url, headers=_xml_headers, json=_xml_put_data)
                            _xml_put.raise_for_status()

                            st.success(f"Comparative visualization '{_cmp_name}' uploaded successfully.")
                        except Exception as _ue:
                            st.error(f"Error uploading visualization: {_ue}")

            st.stop()
        # ---------------------------------------------------------------------------
        # Step 3: Visualization Creation
        st.write("### Visualization Configuration")
        
        # Quick insights
        with st.expander("💡 Quick Data Insights"):
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                st.write(f"**Numeric columns:** {len(numeric_cols)}")
                st.write(f"**Highest correlation:** {df[numeric_cols].corr().abs().unstack().sort_values(ascending=False).iloc[1]:.3f}")
                st.write(f"**Missing values:** {df.isnull().sum().sum()}")
        
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            x_axis = st.multiselect("Select columns for X-axis:", options=df.columns.tolist(), key="viz_x_axis")

        with col2:
            y_axis = st.multiselect("Select columns for Y-axis:", options=df.columns.tolist(), key="viz_y_axis")

        with col3:
            plot_type = st.selectbox("Select the type of visualization:", [
                "Line Plot", "Bar Plot", "Scatter Plot", "Histogram", "Box Plot", "Heatmap", "Violin Plot", "Pair Plot", "Trend Analysis"
            ], key="viz_plot_type")
            
        with col4:
            chart_style = st.selectbox("Chart Style:", ["Default", "Seaborn", "ggplot (R-style)", "FiveThirtyEight", "Dark Mode"], key="viz_chart_style")

        # Maintain visualization state after interactions
        if 'visualization_buffer' not in st.session_state:
            st.session_state['visualization_buffer'] = None

        # Chart customization
        _cust_col1, _cust_col2, _cust_col3 = st.columns(3)
        with _cust_col1:
            custom_title = st.text_input("Chart Title (optional):", key="viz_custom_title")
        with _cust_col2:
            custom_x_label = st.text_input("X-Axis Label (optional):", key="viz_custom_x_label")
        with _cust_col3:
            custom_y_label = st.text_input("Y-Axis Label (optional):", key="viz_custom_y_label")

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

            if plot_type == "Pair Plot":
                sns.pairplot(df[x_axis + y_axis])
                st.pyplot()  # Pair plot creates its own figure
                st.session_state['visualization_buffer'] = None
            else:
                _ok = _render_chart_on_ax(
                    df, x_axis, y_axis, plot_type, ax,
                    custom_title=custom_title if custom_title else None,
                    custom_x_label=custom_x_label if custom_x_label else None,
                    custom_y_label=custom_y_label if custom_y_label else None
                )

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
        visualization_description = st.text_area("Enter a description for the visualization:", key="viz_description")

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