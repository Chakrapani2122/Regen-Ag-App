import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def main():
    st.title("Data Schedule")
    
    try:
        df = pd.read_excel("assets/Data_Schedule.xlsx", sheet_name="Schedule")
        
        # Schedule overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tasks", len(df))
        with col2:
            completed = len(df[df.get('Status', '') == 'Completed']) if 'Status' in df.columns else 0
            st.metric("Completed", completed)
        with col3:
            pending = len(df[df.get('Status', '') == 'Pending']) if 'Status' in df.columns else 0
            st.metric("Pending", pending)
        with col4:
            overdue = len(df[df.get('Status', '') == 'Overdue']) if 'Status' in df.columns else 0
            st.metric("Overdue", overdue, delta_color="inverse")
        
        # Filters
        with st.expander("🔍 Filter Schedule"):
            col1, col2 = st.columns(2)
            with col1:
                if 'Status' in df.columns:
                    status_filter = st.multiselect("Filter by Status:", df['Status'].unique(), default=df['Status'].unique())
                else:
                    status_filter = []
            with col2:
                if 'Priority' in df.columns:
                    priority_filter = st.multiselect("Filter by Priority:", df['Priority'].unique(), default=df['Priority'].unique())
                else:
                    priority_filter = []
        
        # Apply filters
        filtered_df = df.copy()
        if status_filter and 'Status' in df.columns:
            filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
        if priority_filter and 'Priority' in df.columns:
            filtered_df = filtered_df[filtered_df['Priority'].isin(priority_filter)]
        
        # Display schedule with enhanced formatting
        st.write(f"**Showing {len(filtered_df)} of {len(df)} tasks**")
        
        # Color-code rows based on status
        def highlight_status(row):
            if 'Status' in row:
                if row['Status'] == 'Completed':
                    return ['background-color: #d4edda'] * len(row)
                elif row['Status'] == 'Overdue':
                    return ['background-color: #f8d7da'] * len(row)
                elif row['Status'] == 'In Progress':
                    return ['background-color: #fff3cd'] * len(row)
            return [''] * len(row)
        
        if not filtered_df.empty:
            styled_df = filtered_df.style.apply(highlight_status, axis=1)
            st.dataframe(styled_df, height=600, use_container_width=True)
        else:
            st.warning("No tasks match the selected filters.")
            
        # Quick actions
        st.write("### ⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📅 View This Week"):
                st.info("Filtering tasks for current week...")
        with col2:
            if st.button("⚠️ Show Overdue"):
                st.info("Showing overdue tasks...")
        with col3:
            if st.button("📈 Export Schedule"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="data_schedule.csv",
                    mime="text/csv"
                )
                
    except Exception as e:
        st.error(f"Could not load Data_Schedule.xlsx: {e}")
        st.info("Please ensure the Data_Schedule.xlsx file exists in the assets folder with a 'Schedule' sheet.")
