import streamlit as st
from github import Github
from xml.etree import ElementTree as ET
from io import BytesIO
import requests

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

    g = Github(token)
    repo = g.get_repo("Chakrapani2122/Regen-Ag-Data")

    # Step 2: Fetch and parse visualizations.xml
    xml_path = "Visualizations/visualizations.xml"
    try:
        xml_file = repo.get_contents(xml_path)
        xml_content = xml_file.decoded_content.decode("utf-8")
        root = ET.fromstring(xml_content)
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
                file_content = repo.get_contents(path).decoded_content
                st.image(BytesIO(file_content), use_column_width=True)
            except Exception:
                st.warning(f"Could not load image: {name}")
        with col2:
            st.subheader(name)
            st.caption(f"Date: {date}")
            st.write(description)
        st.markdown("---")

if __name__ == "__main__":
    main()
