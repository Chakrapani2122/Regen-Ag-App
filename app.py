import streamlit as st
from about import main as about_main
from contact import main as contact_main
from upload import main as upload_main
from view import main as view_main
from visualize import main as visualize_main

# Set up the Streamlit app with favicon
st.set_page_config(page_title="Reagn Ag App", layout="wide", page_icon="assets/logo.png")

# Sidebar navigation with logo
st.sidebar.image("assets/logo.png", use_column_width=False)
page = st.sidebar.radio("", ["Home", "View Data", "Upload Data", "Visualize", "About Us", "Contact Us"])

# Page routing
if page == "Home":
    # Add logo and title in the same row
    col1, col2 = st.columns([1, 12])
    with col1:
        st.image("assets/logo.png")
    with col2:
        st.title("KSU: Regenerative Agriculture")
    st.write("Welcome to the Home Page!")
    st.write("Use the sidebar to navigate to different sections of the app.")
elif page == "About Us":
    about_main()
elif page == "Contact Us":
    contact_main()
elif page == "Upload Data":
    upload_main()
elif page == "View Data":
    view_main()
elif page == "Visualize":
    visualize_main()