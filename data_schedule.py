import streamlit as st
import pandas as pd

def main():
    st.title("Data Schedule")

    try:
        df = pd.read_excel("assets/Data_Schedule.xlsx", sheet_name="Schedule")
        st.dataframe(df, height=600)
    except Exception as e:
        st.error(f"Could not load Data_Schedule.xlsx: {e}")
