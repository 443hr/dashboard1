# dashboard.py

import streamlit as st
import pandas as pd
from azure.storage.blob import BlobServiceClient
import os
import plotly.express as px
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure Blob Config
conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_BLOB_CONTAINER")
blob_name = "merged_data.xlsx"  # unified name for all uploads

@st.cache_data
def load_data():
    blob_service = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service.get_blob_client(container=container_name, blob=blob_name)
    data = blob_client.download_blob().readall()
    df = pd.read_excel(BytesIO(data))
    return df

def render_chart(df, chart_id):
    st.markdown(f"### Chart {chart_id + 1}")
    chart_type = st.selectbox(f"Chart Type {chart_id+1}", ["Bar", "Line", "Scatter", "Histogram", "Pie"], key=f"type_{chart_id}_{chart_id}")

    if chart_type in ["Bar", "Line", "Scatter", "Histogram"]:
        x_axis = st.selectbox(f"X-Axis {chart_id+1}", df.columns, key=f"x_{chart_id}_{chart_id}")
        y_axis = st.selectbox(f"Y-Axis {chart_id+1}", df.columns, key=f"y_{chart_id}_{chart_id}")

        if chart_type == "Bar":
            fig = px.bar(df, x=x_axis, y=y_axis)
        elif chart_type == "Line":
            fig = px.line(df, x=x_axis, y=y_axis)
        elif chart_type == "Scatter":
            fig = px.scatter(df, x=x_axis, y=y_axis)
        elif chart_type == "Histogram":
            fig = px.histogram(df, x=x_axis)

        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Pie":
        label_col = st.selectbox(f"Labels (Category) for Pie {chart_id+1}", df.columns, key=f"pie_label_{chart_id}_{chart_id}")
        value_col = st.selectbox(f"Values (Size) for Pie {chart_id+1}", df.columns, key=f"pie_value_{chart_id}_{chart_id}")
        fig = px.pie(df, names=label_col, values=value_col)
        st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("\U0001F4CA RMIT Data Dashboard (Azure Blob)")

    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading data from Azure Blob: {e}")
        return

    st.success("\u2705 Data loaded from Azure Blob")

    st.markdown("### Create Up to 4 Charts on One Screen")

    col1, col2 = st.columns(2)
    with col1:
        render_chart(df, 0)
    with col2:
        render_chart(df, 1)

    col3, col4 = st.columns(2)
    with col3:
        render_chart(df, 2)
    with col4:
        render_chart(df, 3)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8501))
    import sys
    sys.argv = [sys.argv[0], 'run', '--server.port', str(port), '--server.enableCORS', 'false']
    main()
