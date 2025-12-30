import streamlit as st
import pandas as pd
import requests
import time
import io
from config import API_URL, MINIO_BUCKET_RAW
from utils import get_minio_client

def data_preparation_page():
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">📊 Data Preparation</div>
        <div class="header-subtitle">Upload, clean, and transform your raw data into production-ready datasets</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Step 1: Upload
    st.markdown('<div class="section-header"><span>1</span> Upload Data</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Drop your CSV file here or click to browse",
        type="csv",
        help="Upload your dataset in CSV format"
    )
    
    if uploaded_file is not None:
        # Read data for preview
        original_df = pd.read_csv(uploaded_file)
        uploaded_file.seek(0)  # Reset pointer
        
        # Metrics Cards
        st.markdown("### Dataset Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{:,}</div>
                <div class="metric-label">Rows</div>
            </div>
            """.format(original_df.shape[0]), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{:,}</div>
                <div class="metric-label">Columns</div>
            </div>
            """.format(original_df.shape[1]), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{:,}</div>
                <div class="metric-label">Missing Values</div>
            </div>
            """.format(original_df.isna().sum().sum()), unsafe_allow_html=True)
        
        # Data Preview
        with st.expander("🔍 Preview Raw Data", expanded=False):
            st.dataframe(
                original_df.head(10),
                use_container_width=True,
                height=300
            )
        
        # Step 2: Configuration
        st.markdown('<div class="section-header"><span>2</span> Configuration</div>', unsafe_allow_html=True)
        
        st.markdown("### Processing Pipeline Configuration")
        
        col_conf1, col_conf2 = st.columns(2)
        
        with col_conf1:
            st.subheader(" Missing Values")
            
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
            st.markdown("#### ⚙️ Feature Engineering")
            scaling_option = st.selectbox(
                "Scaling Method",
                ["None", "Standard Scaler", "MinMax Scaler"],
                help="Standardize features for better model performance"
            )
            
            one_hot_encoding = st.checkbox(
                "One-Hot Encoding",
                value=True,
                help="Convert categorical variables using One-Hot Encoding"
            )
    
        # Build Pipeline
        pipeline_steps = []
        
        if num_strategy == "Fill with 0":
            pipeline_steps.append({"operator": "imputer", "params": {"strategy": "constant_zero"}})
        elif num_strategy == "Fill with Mean":
            pipeline_steps.append({"operator": "imputer", "params": {"strategy": "mean"}})
            
        if cat_strategy:
            pipeline_steps.append({"operator": "imputer", "params": {"strategy": "most_frequent"}})
        
        if scaling_option == "Standard Scaler":
            pipeline_steps.append({"operator": "standard_scaler", "params": {}})
        elif scaling_option == "MinMax Scaler":
            pipeline_steps.append({"operator": "minmax_scaler", "params": {}})
            
        if one_hot_encoding:
            pipeline_steps.append({"operator": "one_hot", "params": {"dtype": "int"}})
        
        # Step 3: Process
        st.markdown('<div class="section-header"><span>3</span> Process Data</div>', unsafe_allow_html=True)
        
        st.markdown("### Ready to Process?")
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.info(f"**Pipeline Steps**: {len(pipeline_steps)} operations configured")
        with col_info2:
            st.info("**Estimated Time**: 30-60 seconds")
        
        if st.button("🚀 Launch Data Cleaning Pipeline", type="primary"):
            client = get_minio_client()
            file_name = uploaded_file.name
            
            # Processing with detailed status
            with st.status("🔄 **Processing Data...**", expanded=True) as status:
                try:
                    # Step 1: Upload to MinIO
                    status.write("📤 **Uploading to storage...**")
                    if not client.bucket_exists(MINIO_BUCKET_RAW):
                        client.make_bucket(MINIO_BUCKET_RAW)
                    client.put_object(
                        MINIO_BUCKET_RAW, file_name, uploaded_file, uploaded_file.size, content_type="application/csv"
                    )
                    status.write("✅ Upload complete")
                    
                    # Step 2: Call API
                    status.write("⚡ **Triggering processing job...**")
                    payload = {
                        "input_data": {"bucket": MINIO_BUCKET_RAW, "path": file_name},
                        "pipeline": pipeline_steps
                    }
                    
                    response = requests.post(f"{API_URL}/prepare", json=payload)
                    response.raise_for_status()
                    job_id = response.json()["job_id"]
                    
                    # Store in shared state IMMEDIATELY
                    st.session_state["shared_dataset_id"] = job_id
                    
                    status.write(f"✅ Job started (ID: `{job_id}`)")
                    
                    # Step 3: Poll for results
                    status.write("⏳ **Processing in progress...**")
                    progress_bar = st.progress(0)
                    result_df = None
                    
                    for i in range(30):
                        time.sleep(1.5)
                        progress_bar.progress((i + 1) / 30)
                        
                        res = requests.get(f"{API_URL}/status/{job_id}")
                        if res.status_code == 200:
                            job_status = res.json()["status"]
                            if job_status == "COMPLETED":
                                out_data = res.json()
                                obj = client.get_object(out_data["output_bucket"], out_data["output_path"])
                                result_df = pd.read_csv(io.BytesIO(obj.read()))
                                progress_bar.progress(1.0)
                                
                                # Redundant but safe: sync again
                                st.session_state["shared_dataset_id"] = job_id
                                
                                status.update(
                                    label="✅ **Processing Complete!**",
                                    state="complete",
                                    expanded=False
                                )
                                break
                            elif job_status == "FAILED":
                                status.update(label="❌ **Processing Failed!**", state="error")
                                st.error(res.json().get("error", "Unknown error"))
                                st.stop()
                    
                    if result_df is not None:
                        st.balloons()
                        st.success("✨ Data processed successfully!")
                        
                        # Display ID prominent
                        st.markdown(f"""
                        <div style="background-color: #d1fae5; padding: 20px; border-radius: 10px; border: 1px solid #10b981; margin: 20px 0; text-align: center;">
                            <h3 style="color: #065f46; margin:0;">Dataset Ready!</h3>
                            <p style="color: #047857; margin: 10px 0;">Copy this <strong>Dataset ID</strong> for the Model Selector:</p>
                            <code style="font-size: 1.5rem; background: white; padding: 5px 15px; border-radius: 5px; border: 1px solid #10b981;">{job_id}</code>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Results Section
                        st.markdown("## 📊 Processed Data Preview")
                        
                        # Preview only
                        st.dataframe(result_df.head(20), use_container_width=True)
                        
                        # Download Section
                        st.markdown("### 📥 Download Results")
                        csv_data = result_df.to_csv(index=False)
                        
                        col_dl1, col_dl2, col_dl3 = st.columns([2, 1, 2])
                        with col_dl2:
                            st.download_button(
                                label="⬇️ Download Cleaned CSV",
                                data=csv_data,
                                file_name=f"processed_{file_name}",
                                mime="text/csv",
                                type="primary"
                            )
                        
                except Exception as e:
                    status.update(label="❌ **Error Occurred**", state="error")
                    st.error(f"**Error details:** {str(e)}")
