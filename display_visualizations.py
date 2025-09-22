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
    
    # Visualization management options
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox("Sort by:", ["Date (Newest)", "Date (Oldest)", "Name (A-Z)", "Name (Z-A)"])
    with col2:
        search_viz = st.text_input("🔍 Search visualizations:", placeholder="Search by name or description")
    with col3:
        view_mode = st.selectbox("View mode:", ["Gallery", "List", "Grid"])

    # Step 1: Ask for GitHub security token
    token = st.text_input("Enter your security token:", type="password")
    if not token:
        st.warning("Please provide your security token to proceed.")
        return

    if validate_github_token(token):
        st.success("Token validated successfully!")
    else:
        st.error("Invalid token or access issue.")
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

    # Filter and sort visualizations
    filtered_images = images
    if search_viz:
        filtered_images = [img for img in images if search_viz.lower() in (img.findtext("Name", "").lower() + img.findtext("Description", "").lower())]
    
    # Sort visualizations
    if sort_by == "Date (Newest)":
        filtered_images = sorted(filtered_images, key=lambda x: x.findtext("Date", ""), reverse=True)
    elif sort_by == "Date (Oldest)":
        filtered_images = sorted(filtered_images, key=lambda x: x.findtext("Date", ""))
    elif sort_by == "Name (A-Z)":
        filtered_images = sorted(filtered_images, key=lambda x: x.findtext("Name", ""))
    elif sort_by == "Name (Z-A)":
        filtered_images = sorted(filtered_images, key=lambda x: x.findtext("Name", ""), reverse=True)
    
    st.write(f"**Showing {len(filtered_images)} of {len(images)} visualizations**")
    
    # Step 3: Display visualizations based on view mode
    if view_mode == "Gallery":
        for image in filtered_images:
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
                    
                    # Download button for each visualization
                    st.download_button(
                        label="💾 Download",
                        data=base64.b64decode(response.json()["content"]),
                        file_name=name,
                        mime="image/png",
                        key=f"download_{name}"
                    )
                except Exception:
                    st.warning(f"Could not load image: {name}")
            with col2:
                st.subheader(name)
                st.caption(f"📅 Created: {date}")
                st.write(description)
                
                # Tags or categories (if available)
                if "soil" in description.lower():
                    st.badge("🌱 Soil Health", type="secondary")
                if "crop" in description.lower():
                    st.badge("🌾 Crops", type="secondary")
                if "trend" in description.lower():
                    st.badge("📈 Trends", type="secondary")
            st.markdown("---")
    
    elif view_mode == "Grid":
        # Grid layout with 3 columns
        cols = st.columns(3)
        for i, image in enumerate(filtered_images):
            with cols[i % 3]:
                name = image.findtext("Name", "")
                path = image.findtext("Path", "")
                date = image.findtext("Date", "")
                
                try:
                    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{path}"
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    file_content = response.json()["content"]
                    file_content = BytesIO(base64.b64decode(file_content))
                    st.image(file_content, use_column_width=True)
                    st.caption(f"**{name}**")
                    st.caption(f"{date}")
                except Exception:
                    st.warning(f"Could not load: {name}")
    
    else:  # List view
        for image in filtered_images:
            name = image.findtext("Name", "")
            description = image.findtext("Description", "")
            date = image.findtext("Date", "")
            
            with st.container():
                col1, col2, col3 = st.columns([3, 6, 2])
                with col1:
                    st.write(f"**{name}**")
                with col2:
                    st.write(description[:100] + "..." if len(description) > 100 else description)
                with col3:
                    st.write(date)
            st.markdown("---")

if __name__ == "__main__":
    main()
