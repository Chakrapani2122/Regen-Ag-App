import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")

def main():
    st.title("Data Schedule")
    
    try:
        df = pd.read_excel("assets/Data_Schedule.xlsx", sheet_name="Schedule")
        st.dataframe(df, height=600, use_container_width=True)          
    except Exception as e:
        st.error(f"Could not load Data_Schedule.xlsx: {e}")
        st.info("Please ensure the Data_Schedule.xlsx file exists in the assets folder with a 'Schedule' sheet.")
