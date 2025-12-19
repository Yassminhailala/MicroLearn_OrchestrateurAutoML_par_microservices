import streamlit as st
import pandas as pd
import requests
import time
from minio import Minio
import io
import os

# Configuration
API_URL = os.getenv("API_URL", "http://data_preparer:8000")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_RAW = "raw-data"
MINIO_BUCKET_PROCESSED = "processed-data"

# Setup MinIO Client
def get_minio_client():
    return Minio(
        MINIO_ENDPOINT.replace("http://", ""),
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

st.set_page_config(page_title="AutoML Data Preparer", layout="wide", page_icon="✨")

# Custom CSS for better cards
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("✨ AutoML Data Preparer")
st.markdown("Simply upload your raw data, choose your cleaning options, and get a production-ready dataset.")

# --- STEP 1: UPLOAD ---
st.header("1. Upload Data")
uploaded_file = st.file_uploader("Drop your CSV file here", type="csv")

if uploaded_file is not None:
    # Read locally for preview
    original_df = pd.read_csv(uploaded_file)
    uploaded_file.seek(0) # Reset pointer
    
    # Show stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", original_df.shape[0])
    col2.metric("Columns", original_df.shape[1])
    col3.metric("Missing Values", original_df.isna().sum().sum())

    with st.expander("👀 View Raw Data", expanded=True):
        st.dataframe(original_df.head(10), use_container_width=True)

    # --- STEP 2: CONFIGURE ---
    st.header("2. Configuration")
    
    col_conf1, col_conf2 = st.columns(2)
    
    with col_conf1:
        st.subheader("🧹 Missing Values")
        
        st.markdown("**Numeric Columns:**")
        num_strategy = st.radio(
            "Numerics",
            ["None", "Fill with 0", "Fill with Mean"],
            horizontal=True,
            key="num_strat"
        )
        
        st.markdown("**Categorical Columns:**")
        cat_strategy = st.checkbox("Impute Mode (Most Frequent)", value=True, help="Fills missing text values with the most frequent value.")
    
    with col_conf2:
        st.subheader("📏 Scaling & Encoding")
        scaling_option = st.selectbox("Scaling Method", ["None", "Standard Scaler", "MinMax Scaler"], help="Standardize features by removing the mean and scaling to unit variance.")
        one_hot = st.checkbox("One-Hot Encoding", value=False, help="Convert categorical variables into dummy/indicator variables.")

    # Build Pipeline
    pipeline_steps = []
    
    # Numeric Imputation
    if num_strategy == "Fill with 0":
        pipeline_steps.append({"operator": "imputer", "params": {"strategy": "constant_zero"}})
    elif num_strategy == "Fill with Mean":
        pipeline_steps.append({"operator": "imputer", "params": {"strategy": "mean"}})
        
    # Categorical Imputation
    if cat_strategy:
        pipeline_steps.append({"operator": "imputer", "params": {"strategy": "most_frequent"}})
    
    if scaling_option == "Standard Scaler":
        pipeline_steps.append({"operator": "standard_scaler", "params": {}})
    elif scaling_option == "MinMax Scaler":
        pipeline_steps.append({"operator": "minmax_scaler", "params": {}})
        
    if one_hot:
        pipeline_steps.append({"operator": "one_hot", "params": {"dtype": "int"}})

    # --- STEP 3: PROCESS ---
    st.markdown("---")
    st.header("3. Process")
    
    if st.button("🚀 Launch Data Cleaning Pipeline", type="primary"):
        client = get_minio_client()
        file_name = uploaded_file.name
        
        # 1. Upload
        with st.status("Processing data...", expanded=True) as status:
            status.write("Uploading to storage...")
            try:
                if not client.bucket_exists(MINIO_BUCKET_RAW):
                    client.make_bucket(MINIO_BUCKET_RAW)
                client.put_object(
                    MINIO_BUCKET_RAW, file_name, uploaded_file, uploaded_file.size, content_type="application/csv"
                )
                status.write("✅ Upload complete.")
            except Exception as e:
                status.update(label="Upload failed!", state="error")
                st.error(f"Error: {e}")
                st.stop()
            
            # 2. Call API
            status.write("Triggering processing job...")
            payload = {
                "input_data": {"bucket": MINIO_BUCKET_RAW, "path": file_name},
                "pipeline": pipeline_steps
            }
            
            try:
                response = requests.post(f"{API_URL}/prepare", json=payload)
                response.raise_for_status()
                job_id = response.json()["job_id"]
                status.write(f"✅ Job started (ID: {job_id})")
            except Exception as e:
                status.update(label="API Call failed!", state="error")
                st.error(f"Error: {e}")
                st.stop()
                
            # 3. Poll
            status.write("Waiting for results...")
            result_df = None
            for _ in range(40):
                time.sleep(1)
                res = requests.get(f"{API_URL}/status/{job_id}")
                if res.status_code == 200 and res.json()["status"] == "COMPLETED":
                    out_data = res.json()
                    obj = client.get_object(out_data["output_bucket"], out_data["output_path"])
                    result_df = pd.read_csv(io.BytesIO(obj.read()))
                    status.update(label="Processing Complete!", state="complete", expanded=False)
                    break
                elif res.json()["status"] == "FAILED":
                    status.update(label="Processing Failed!", state="error")
                    st.error(res.json().get("error"))
                    st.stop()
            
            if result_df is not None:
                st.success("✨ Data processed successfully!")
                
                # Comparison
                st.subheader("🔍 Result Comparison")
                col_orig, col_proc = st.columns(2)
                
                with col_orig:
                    st.markdown("**Original Data (First 5 rows)**")
                    st.dataframe(original_df.head(), use_container_width=True)
                    
                with col_proc:
                    st.markdown("**Processed Data (First 5 rows)**")
                    st.dataframe(result_df.head(), use_container_width=True)
                
                st.download_button(
                    label="⬇️ Download Cleaned CSV",
                    data=result_df.to_csv(index=False),
                    file_name=f"processed_{file_name}",
                    mime="text/csv",
                    type="primary"
                )

