import streamlit as st
import pandas as pd
import requests
import time
from minio import Minio
import io
import os
import json

# Configuration
API_URL = os.getenv("API_URL", "http://data_preparer:8000")
MODEL_SELECTOR_URL = os.getenv("MODEL_SELECTOR_URL", "http://model_selector:8000")
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

st.set_page_config(page_title="AutoML Platform", layout="wide", page_icon="🤖")

# Custom CSS avec design moderne
st.markdown("""
<style>
    /* Global styles */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Header styles */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Card styles */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        border: 1px solid #e0e6ed;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Button styles */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.2);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.3);
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4290 100%);
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 176, 155, 0.2);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 176, 155, 0.3);
        background: linear-gradient(135deg, #009e8a 0%, #87b536 100%);
    }
    
    /* Model card styles */
    .model-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #667eea;
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .model-card:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    .model-card h3 {
        color: #fff;
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .model-priority {
        background: #667eea;
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    .model-justification {
        color: #e0e6ed;
        font-size: 0.95rem;
        line-height: 1.5;
        margin-top: 0.5rem;
    }
    
    /* Section headers */
    .section-header {
        padding: 1rem 0;
        margin: 1.5rem 0;
        border-bottom: 2px solid #667eea;
        color: #1a1a1a;
        font-size: 1.5rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .section-header span {
        background: #667eea;
        color: white;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    [data-testid="stSidebar"] .sidebar-content {
        padding: 2rem 1rem;
    }
    
    [data-testid="stSidebar"] h1 {
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 1.8rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 0.5rem;
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: 0.75rem 1rem;
        border-radius: 8px;
        transition: all 0.3s ease;
        color: #e0e6ed !important;
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(102, 126, 234, 0.1);
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] label[data-testid="stRadio"]:has(input:checked) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        font-weight: 600;
    }
    
    /* Progress indicator */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Success/Error messages */
    .stAlert {
        border-radius: 8px;
        border: none;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Status indicator */
    [data-testid="stStatus"] {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* File uploader */
    .stFileUploader > div {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        background: rgba(102, 126, 234, 0.05);
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        border-color: #764ba2;
        background: rgba(102, 126, 234, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    # Logo and Title
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1 style='font-size: 1.8rem; margin-bottom: 0.5rem;'>🤖 AutoML Platform</h1>
                <p style='color: #a0aec0; font-size: 0.9rem;'>Automated Machine Learning</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["📊 Data Preparation", "🤖 Model Selection"],
        key="navigation"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Info section
    with st.expander("ℹ️ About", expanded=False):
        st.markdown("""
        **AutoML Platform** provides:
        
        - 📊 **Data Preparation**: Clean and preprocess your data
        - 🤖 **Model Selection**: Get AI-powered model recommendations
        - ⚡ **Automated Pipelines**: End-to-end ML workflow
        
        Upload your data and let AI do the heavy lifting!
        """)

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
            st.markdown("#### 🎯 Missing Values")
            st.markdown("**Numeric Columns:**")
            num_strategy = st.radio(
                "Handling Strategy",
                ["None", "Fill with 0", "Fill with Mean", "Fill with Median"],
                horizontal=False,
                key="num_strat"
            )
            
            st.markdown("**Categorical Columns:**")
            cat_strategy = st.checkbox(
                "Impute Mode (Most Frequent)",
                value=True,
                help="Fills missing categorical values with the most frequent value"
            )
            
            outlier_removal = st.checkbox(
                "Remove Outliers (IQR Method)",
                value=False,
                help="Remove outliers using Interquartile Range method"
            )
        
        with col_conf2:
            st.markdown("#### ⚙️ Feature Engineering")
            scaling_option = st.selectbox(
                "Scaling Method",
                ["None", "Standard Scaler", "MinMax Scaler", "Robust Scaler"],
                help="Standardize features for better model performance"
            )
            
            encoding_options = st.multiselect(
                "Encoding Methods",
                ["One-Hot Encoding", "Label Encoding", "Target Encoding"],
                default=["One-Hot Encoding"],
                help="Convert categorical variables for machine learning"
            )
            
            feature_selection = st.checkbox(
                "Automatic Feature Selection",
                value=False,
                help="Select most important features automatically"
            )
        
        # Build Pipeline
        pipeline_steps = []
        
        if num_strategy == "Fill with 0":
            pipeline_steps.append({"operator": "imputer", "params": {"strategy": "constant_zero"}})
        elif num_strategy == "Fill with Mean":
            pipeline_steps.append({"operator": "imputer", "params": {"strategy": "mean"}})
        elif num_strategy == "Fill with Median":
            pipeline_steps.append({"operator": "imputer", "params": {"strategy": "median"}})
            
        if cat_strategy:
            pipeline_steps.append({"operator": "imputer", "params": {"strategy": "most_frequent"}})
            
        if outlier_removal:
            pipeline_steps.append({"operator": "outlier_removal", "params": {"method": "iqr"}})
        
        if scaling_option == "Standard Scaler":
            pipeline_steps.append({"operator": "standard_scaler", "params": {}})
        elif scaling_option == "MinMax Scaler":
            pipeline_steps.append({"operator": "minmax_scaler", "params": {}})
        elif scaling_option == "Robust Scaler":
            pipeline_steps.append({"operator": "robust_scaler", "params": {}})
            
        if "One-Hot Encoding" in encoding_options:
            pipeline_steps.append({"operator": "one_hot", "params": {"dtype": "int"}})
        if "Label Encoding" in encoding_options:
            pipeline_steps.append({"operator": "label_encoder", "params": {}})
            
        if feature_selection:
            pipeline_steps.append({"operator": "feature_selection", "params": {"method": "variance_threshold"}})
        
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
                        
                        # Results Section
                        st.markdown("## 📊 Results")
                        
                        # Comparison
                        st.markdown("### Data Comparison")
                        tab1, tab2 = st.tabs(["📈 Statistics", "👁️ Preview"])
                        
                        with tab1:
                            col_comp1, col_comp2 = st.columns(2)
                            with col_comp1:
                                st.markdown("#### Original Data")
                                st.metric("Rows", original_df.shape[0])
                                st.metric("Columns", original_df.shape[1])
                                st.metric("Missing", original_df.isna().sum().sum())
                            
                            with col_comp2:
                                st.markdown("#### Processed Data")
                                st.metric("Rows", result_df.shape[0])
                                st.metric("Columns", result_df.shape[1])
                                st.metric("Missing", result_df.isna().sum().sum())
                        
                        with tab2:
                            col_view1, col_view2 = st.columns(2)
                            with col_view1:
                                st.markdown("**Original Data**")
                                st.dataframe(original_df.head(), use_container_width=True, height=250)
                            
                            with col_view2:
                                st.markdown("**Processed Data**")
                                st.dataframe(result_df.head(), use_container_width=True, height=250)
                        
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
                        
                        # Next Steps
                        st.markdown("### 🎯 Next Steps")
                        st.markdown("""
                        Your data is now ready for machine learning! You can:
                        1. Go to **Model Selection** to get AI-powered recommendations
                        2. Download the dataset for external use
                        3. Run another processing job with different parameters
                        """)
                        
                except Exception as e:
                    status.update(label="❌ **Error Occurred**", state="error")
                    st.error(f"**Error details:** {str(e)}")

def model_selection_page():
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">🤖 Model Selection</div>
        <div class="header-subtitle">Get AI-powered recommendations for the best models to train on your data</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload Section
    st.markdown('<div class="section-header"><span>1</span> Upload Processed Data</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload your cleaned dataset (CSV format)",
        type="csv",
        help="Upload the dataset processed in the Data Preparation step"
    )
    
    if uploaded_file is not None:
        # Read and analyze data
        df = pd.read_csv(uploaded_file)
        
        # Dataset Overview
        st.markdown("### 📈 Dataset Analysis")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{df.shape[0]:,}</div>
                <div class="metric-label">Rows</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{df.shape[1]:,}</div>
                <div class="metric-label">Features</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            size_mb = uploaded_file.size / 1e6
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{size_mb:.1f}</div>
                <div class="metric-label">Size (MB)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            dtypes_count = df.dtypes.nunique()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{dtypes_count}</div>
                <div class="metric-label">Data Types</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Data Preview
        with st.expander("🔍 Preview Dataset", expanded=False):
            st.dataframe(df.head(), use_container_width=True, height=250)
            
            # Data types overview
            st.markdown("#### Data Types Summary")
            dtype_summary = df.dtypes.value_counts().reset_index()
            dtype_summary.columns = ['Data Type', 'Count']
            st.dataframe(dtype_summary, use_container_width=True)
        
        # Configuration
        st.markdown('<div class="section-header"><span>2</span> Configuration</div>', unsafe_allow_html=True)
        
        st.markdown("### ⚙️ Model Selection Parameters")
        
        col_conf1, col_conf2 = st.columns(2)
        
        with col_conf1:
            dataset_name = st.text_input(
                "Dataset Name",
                value=uploaded_file.name.replace('.csv', ''),
                help="Give your dataset a descriptive name"
            )
            
            # Auto-detect task type
            target_col = st.selectbox(
                "Target Column",
                options=df.columns.tolist(),
                help="Select the column you want to predict"
            )
            
            # Infer task type based on target column
            if len(df) > 0:
                unique_values = df[target_col].nunique()
                total_values = len(df[target_col])
                
                if pd.api.types.is_numeric_dtype(df[target_col]):
                    if unique_values / total_values > 0.1:  # More than 10% unique values
                        default_task = "Regression"
                    else:
                        default_task = "Classification"
                else:
                    default_task = "Classification"
            else:
                default_task = "Classification"
        
        with col_conf2:
            task_type = st.selectbox(
                "Task Type",
                ["Classification", "Regression", "Clustering", "Time Series"],
                index=["Classification", "Regression", "Clustering", "Time Series"].index(default_task),
                help="Select the type of machine learning task"
            )
            
            # Additional parameters
            performance_priority = st.select_slider(
                "Performance Priority",
                options=["Speed", "Balanced", "Accuracy"],
                value="Balanced",
                help="Balance between model accuracy and training speed"
            )
            
            complexity_level = st.select_slider(
                "Model Complexity",
                options=["Simple", "Moderate", "Complex"],
                value="Moderate",
                help="Choose the complexity level of recommended models"
            )
        
        # Additional options
        with st.expander("⚡ Advanced Options", expanded=False):
            col_adv1, col_adv2 = st.columns(2)
            
            with col_adv1:
                max_training_time = st.number_input(
                    "Max Training Time (minutes)",
                    min_value=1,
                    max_value=240,
                    value=30,
                    help="Maximum allowed training time"
                )
                
                ensemble_preference = st.checkbox(
                    "Prefer Ensemble Models",
                    value=True,
                    help="Prioritize ensemble methods (Random Forest, Gradient Boosting, etc.)"
                )
            
            with col_adv2:
                interpretability = st.checkbox(
                    "Prioritize Interpretability",
                    value=False,
                    help="Prefer models that are easier to interpret (Decision Trees, Linear Models)"
                )
                
                handle_imbalanced = st.checkbox(
                    "Handle Imbalanced Data",
                    value=False,
                    help="Apply techniques for imbalanced datasets"
                )
        
        # Get Recommendations
        st.markdown('<div class="section-header"><span>3</span> Get Recommendations</div>', unsafe_allow_html=True)
        
        if st.button("🔍 Get Model Recommendations", type="primary"):
            # Prepare payload
            payload = {
                "dataset_name": dataset_name,
                "task_type": task_type,
                "target_column": target_col,
                "rows": df.shape[0],
                "columns": df.shape[1],
                "performance_priority": performance_priority.lower(),
                "complexity_level": complexity_level.lower(),
                "ensemble_preference": ensemble_preference,
                "interpretability": interpretability,
                "handle_imbalanced": handle_imbalanced
            }
            
            # Show analysis progress
            with st.spinner("🤖 Analyzing dataset characteristics..."):
                progress_bar = st.progress(0)
                
                for i in range(3):
                    time.sleep(0.5)
                    progress_bar.progress((i + 1) / 3)
                
                try:
                    response = requests.post(f"{MODEL_SELECTOR_URL}/select", json=payload, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    recommendations = data["recommended_models"]
                    
                    progress_bar.progress(1.0)
                    
                    # Display Results
                    st.success(f"✅ Analysis Complete! (Session ID: `{data['selection_id']}`)")
                    
                    # Metrics Summary
                    st.markdown("### 📊 Recommendation Summary")
                    
                    col_sum1, col_sum2, col_sum3 = st.columns(3)
                    
                    with col_sum1:
                        st.metric("Models Recommended", len(recommendations))
                    
                    with col_sum2:
                        avg_score = sum(m.get('confidence_score', 75) for m in recommendations) / len(recommendations)
                        st.metric("Average Confidence", f"{avg_score:.1f}%")
                    
                    with col_sum3:
                        best_model = recommendations[0]['model_name'] if recommendations else "N/A"
                        st.metric("Top Recommendation", best_model)
                    
                    # Model Cards
                    st.markdown("### 🏆 Recommended Models")
                    st.markdown("Models are ranked by suitability for your dataset and requirements.")
                    
                    for i, model in enumerate(recommendations, 1):
                        confidence = model.get('confidence_score', 75)
                        color_map = {
                            "High": "#00b09b",
                            "Medium": "#ffa500",
                            "Low": "#ff4b4b"
                        }
                        
                        if confidence >= 80:
                            confidence_level = "High"
                            color = color_map["High"]
                        elif confidence >= 60:
                            confidence_level = "Medium"
                            color = color_map["Medium"]
                        else:
                            confidence_level = "Low"
                            color = color_map["Low"]
                        
                        st.markdown(f"""
                        <div class="model-card" style="border-left-color: {color};">
                            <h3>
                                <span class="model-priority" style="background: {color};">{i}</span>
                                {model['model_name']}
                                <span style="font-size: 0.8rem; background: {color}20; color: {color}; padding: 2px 8px; border-radius: 12px; margin-left: auto;">
                                    {confidence}% Confidence
                                </span>
                            </h3>
                            <div class="model-justification">
                                <strong>Why this model?</strong><br>
                                {model['justification']}
                            </div>
                            <div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
                                <span style="background: {color}20; color: {color}; padding: 4px 12px; border-radius: 15px; font-size: 0.8rem;">
                                    ⚡ {model.get('training_speed', 'Medium')} Training
                                </span>
                                <span style="background: {color}20; color: {color}; padding: 4px 12px; border-radius: 15px; font-size: 0.8rem;">
                                    🎯 {model.get('accuracy_level', 'Medium')} Accuracy
                                </span>
                                <span style="background: {color}20; color: {color}; padding: 4px 12px; border-radius: 15px; font-size: 0.8rem;">
                                    📊 {model.get('complexity', 'Medium')} Complexity
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Next Steps
                    st.markdown("### 🚀 Next Steps")
                    col_next1, col_next2 = st.columns(2)
                    
                    with col_next1:
                        st.info("""
                        **Train Selected Model:**
                        1. Choose your preferred model from above
                        2. Click "Train Model" to start training
                        3. Monitor training progress
                        4. Evaluate results and deploy
                        """)
                    
                    with col_next2:
                        st.info("""
                        **Compare Models:**
                        1. Select multiple models to compare
                        2. Run parallel training jobs
                        3. Compare performance metrics
                        4. Choose the best performer
                        """)
                    
                    # Action Buttons
                    col_act1, col_act2, col_act3 = st.columns(3)
                    
                    with col_act1:
                        st.button("🔄 Analyze Again")
                    
                    with col_act2:
                        st.button("🚀 Train Top Model")
                    
                    with col_act3:
                        st.button("📊 Compare Models")
                        
                except requests.exceptions.ConnectionError:
                    st.error("""
                    ❌ **Connection Error**
                    
                    Could not connect to the Model Selector service. Please ensure:
                    1. The service is running
                    2. The correct URL is configured
                    3. Network connectivity is available
                    """)
                except requests.exceptions.Timeout:
                    st.error("""
                    ⏱️ **Request Timeout**
                    
                    The analysis is taking longer than expected. This could be due to:
                    - Large dataset size
                    - High server load
                    - Network latency
                    
                    Please try again in a few moments.
                    """)
                except Exception as e:
                    st.error(f"""
                    ❌ **Analysis Failed**
                    
                    **Error details:** {str(e)}
                    
                    Please check:
                    1. Your dataset format
                    2. Network connection
                    3. Service availability
                    """)

# Main app logic
if __name__ == "__main__":
    # Get current page from navigation
    if "navigation" in st.session_state:
        page_type = st.session_state.navigation
    else:
        page_type = "📊 Data Preparation"
    
    # Route to correct page
    if "Data Preparation" in page_type:
        data_preparation_page()
    elif "Model Selection" in page_type:
        model_selection_page()