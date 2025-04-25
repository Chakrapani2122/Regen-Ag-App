import streamlit as st
import warnings
from about import main as about_main
from contact import main as contact_main
from upload import main as upload_main
from view import main as view_main
from visualize import main as visualize_main

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Set up the Streamlit app with favicon
st.set_page_config(page_title="Reagn Ag App", layout="wide", page_icon="assets/logo.png")

# Sidebar navigation with logo
st.sidebar.image("assets/logo.png", width=80, caption=None)
page = st.sidebar.radio("", ["Home", "View Data", "Upload Data", "Visualize", "About Us", "Contact Us"])

# Page routing
if page == "Home":
    # Add logo and title in the same row
    col1, col2 = st.columns([1, 12])
    with col1:
        st.image("assets/logo.png")
    with col2:
        st.title("KSU: Regenerative Agriculture")
    st.write("## 🌾 Welcome to KSURA")
    st.image("assets/team.png", use_container_width=True)
    st.markdown("""At **Kansas State University Regenerative Agriculture (KSURA)**, we're building a more sustainable future for farming in Kansas and beyond. 🌍 We're proud to collaborate with farmers, researchers, policymakers, and consumers to promote practices that restore soil health, boost biodiversity, and strengthen ecosystem services. 🌱

## 🚜 What We Do

Our team is dedicated to advancing **regenerative agriculture** — a transformative approach to farming that improves soil, increases resilience, and enhances food systems. Through cutting-edge research, education, and partnerships, we're creating climate-smart, profitable solutions for today’s challenges.

## 🌿 Our Principles

We follow six key principles of regenerative agriculture:
- 🌾 Maximize diversity
- 🚜 Reduce tillage
- 🍀 Keep the soil covered
- 🌱 Maintain living roots
- 🐄 Integrate livestock
- 🌎 Tailor to local ecosystems

These principles help **restore soil health, sequester carbon, and build resilient farms** that thrive with nature, not against it. 🌻

## 🤝 Get Involved

Join us through the **Kansas Soil Health Network (KSHN)**! 🌾  
We're helping farmers adopt proven soil-friendly practices with support from partners like USDA, Kansas Corn Commission, and The Nature Conservancy.

- 🔬 On-farm trials & research
- 🌱 Demonstration farms
- 💰 Market opportunities for nutrient-rich crops

---

**Together, let’s grow a more regenerative future. 🌾💚**
    
    """)
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