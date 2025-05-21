import streamlit as st
import requests
from xml.etree import ElementTree as ET
from io import BytesIO
import base64
import warnings

warnings.filterwarnings("ignore")

def validate_github_token(token):
    headers = {"Authorization": f"token {token}"}
    url = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data"
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def main():
    st.title("Created Visualizations")

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

    # Replace all github module usage with requests-based API calls as in view.py
    # For file content, use the API as in view.py

    # Step 2: Fetch and parse visualizations.xml
    xml_path = "Visualizations/visualizations.xml"
    try:
        headers = {"Authorization": f"token {token}"}
        url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{xml_path}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        xml_content = response.json()["content"]
        xml_content = BytesIO(base64.b64decode(xml_content))
        tree = ET.parse(xml_content)
        root = tree.getroot()

        images = root.findall("Image")
        if not images:
            st.info("No visualizations found.")
            return
    except Exception as e:
        st.error(f"Could not fetch visualizations: {e}")
        return

    # Step 3: Display each visualization in a table with two columns
    for image in images:
        name = image.findtext("Name", "")
        path = image.findtext("Path", "")
        description = image.findtext("Description", "")
        date = image.findtext("Date", "")

        col1, col2 = st.columns([2, 3])
        with col1:
            # Fetch the image file from GitHub
            try:
                url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{path}"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                file_content = response.json()["content"]
                file_content = BytesIO(base64.b64decode(file_content))
                st.image(file_content, use_column_width=True)
            except Exception:
                st.warning(f"Could not load image: {name}")
        with col2:
            st.subheader(name)
            st.caption(f"Date: {date}")
            st.write(description)
        st.markdown("---")

if __name__ == "__main__":
    main()
