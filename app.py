import streamlit as st
import warnings
from about import main as about_main
from contact import main as contact_main
from upload import main as upload_main
from view import main as view_main
from visualize import main as visualize_main
import display_visualizations
from visualization import main as visualization_main
from data_schedule import main as data_schedule_main

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Set up the Streamlit app with favicon
st.set_page_config(page_title="KSU - Regenerative Agriculture", layout="wide", page_icon="assets/logo.png")

# Sidebar navigation with logo
st.sidebar.image("assets/logo.png", width=80, caption=None)
PAGES = {
    "Home": None,
    "View Data": view_main,
    "Upload Data": upload_main,
    "Visualizations": visualization_main,
    "About Us": about_main,
    "Contact Us": contact_main,
    "Data Schedule": data_schedule_main
}

st.sidebar.title("KSURA")
selection = st.sidebar.radio("", list(PAGES.keys()))

# Page routing
if selection == "Home":
    # Add logo and title in the same row
    col1, col2 = st.columns([1, 12])
    with col1:
        st.image("assets/logo.png")
    with col2:
        st.title("KSU: Regenerative Agriculture")


    
    st.write("## Welcome to KSURA")
    st.image("assets/team.png")
    st.markdown("""At **Kansas State University Regenerative Agriculture (KSURA)**, we're building a more sustainable future for farming in Kansas and beyond. 🌍 We're proud to collaborate with farmers, researchers, policymakers, and consumers to promote practices that restore soil health, boost biodiversity, and strengthen ecosystem services. 🌱

## What We Do

Our team is dedicated to advancing **regenerative agriculture** — a transformative approach to farming that improves soil, increases resilience, and enhances food systems. Through cutting-edge research, education, and partnerships, we're creating climate-smart, profitable solutions for today's challenges.

## Our Principles

We follow six key principles of regenerative agriculture:
- Maximize diversity
- Reduce tillage
- Keep the soil covered
- Maintain living roots
- Integrate livestock
- Tailor to local ecosystems

These principles help **restore soil health, sequester carbon, and build resilient farms** that thrive with nature, not against it.

## Get Involved

Join us through the **Kansas Soil Health Network (KSHN)**!
We're helping farmers adopt proven soil-friendly practices with support from partners like USDA, Kansas Corn Commission, and The Nature Conservancy.

- On-farm trials & research
- Demonstration farms
- Market opportunities for nutrient-rich crops

---

**Together, let's grow a more regenerative future.**
    """)
    
    

else:
    page = PAGES[selection]
    if callable(page):
        page()
    elif hasattr(page, 'main') and callable(page.main):
        page.main()