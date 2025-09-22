import streamlit as st
import requests
from xml.etree import ElementTree as ET
from io import BytesIO
import base64
import warnings
from urllib.parse import quote

warnings.filterwarnings("ignore")

# Helper to render badges safely (fall back if st.badge isn't available)
def render_badge(text):
    try:
        if hasattr(st, 'badge'):
            st.badge(text, type='secondary')
        else:
            st.markdown(f"- {text}")
    except Exception:
        # Last-resort fallback
        st.write(text)

def validate_github_token(token):
    headers = {"Authorization": f"token {token}"}
    url = "https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data"
    response = requests.get(url, headers=headers)
    return response.status_code == 200


def display_image_compatible(img_bytesio, caption=None):
    """Display an image using whatever st.image parameter is supported by the installed Streamlit.

    Tries use_container_width, then use_column_width, then a fixed width.
    """
    try:
        img_bytesio.seek(0)
    except Exception:
        pass

    # Try modern parameter first
    try:
        return st.image(img_bytesio, caption=caption, use_container_width=True)
    except TypeError:
        pass

    # Try older (deprecated but present) parameter
    try:
        return st.image(img_bytesio, caption=caption, use_column_width=True)
    except TypeError:
        pass

    # Final fallback: fixed width (keeps display stable)
    try:
        return st.image(img_bytesio, caption=caption, width=400)
    except Exception as e:
        st.warning(f"Unable to display image: {e}")
        return None

def main():
    
    # Visualization management options
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox("Sort by:", ["Date (Newest)", "Date (Oldest)", "Name (A-Z)", "Name (Z-A)"])
    with col2:
        search_viz = st.text_input("🔍 Search visualizations:", placeholder="Search by name or description")
    with col3:
        view_mode = st.selectbox("View mode:", ["Gallery", "List", "Grid"])

    # Use the token saved in session_state (visualization.py handles prompting)
    token = st.session_state.get('gh_token', None)
    if not token:
        st.warning("Please provide your security token on the Visualizations page to proceed.")
        return

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
                    encoded_path = quote(path, safe='')
                    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{encoded_path}"
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    file_b64 = response.json().get("content")
                    if not file_b64:
                        raise ValueError("No content field in GitHub response")
                    file_bytes = base64.b64decode(file_b64)
                    file_content = BytesIO(file_bytes)
                    display_image_compatible(file_content)

                    # Download button for each visualization
                    st.download_button(
                        label="💾 Download",
                        data=file_bytes,
                        file_name=name,
                        mime="image/png",
                        key=f"download_{name}"
                    )
                except Exception as e:
                    st.warning(f"Could not load image: {name} — {e}")
            with col2:
                st.subheader(name)
                st.caption(f"📅 Created: {date}")
                st.write(description)
                
                # Tags or categories (if available)
                if "soil" in description.lower():
                    render_badge("🌱 Soil Health")
                if "crop" in description.lower():
                    render_badge("🌾 Crops")
                if "trend" in description.lower():
                    render_badge("📈 Trends")
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
                    encoded_path = quote(path, safe='')
                    url = f"https://api.github.com/repos/Chakrapani2122/Regen-Ag-Data/contents/{encoded_path}"
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    file_b64 = response.json().get("content")
                    if not file_b64:
                        raise ValueError("No content field in GitHub response")
                    file_bytes = base64.b64decode(file_b64)
                    file_content = BytesIO(file_bytes)
                    display_image_compatible(file_content)
                    st.caption(f"**{name}**")
                    st.caption(f"{date}")
                except Exception as e:
                    st.warning(f"Could not load: {name} — {e}")
    
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
