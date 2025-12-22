import streamlit as st
import pandas as pd
import requests
import io
from config import MODEL_SELECTOR_URL, TRAINER_API_URL
from utils import get_minio_client

def model_selection_page():
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">🤖 Model Selection</div>
        <div class="header-subtitle">Get AI-powered recommendations based on your processed dataset</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Step 1: Input Dataset ID
    st.markdown('<div class="section-header"><span>1</span> Select Dataset</div>', unsafe_allow_html=True)
    
    dataset_id = st.text_input(
        "Enter Dataset ID",
        help="Paste the ID provided by the Data Preparation step"
    )
    
    if dataset_id:
        # Try to load dataset from MinIO to get columns for Target selection
        client = get_minio_client()
        bucket_name = "processed-data"
        file_path = f"processed_{dataset_id}.csv"
        
        try:
            # Check if exists
            obj = client.get_object(bucket_name, file_path)
            df = pd.read_csv(io.BytesIO(obj.read()))
            
            # Dataset Analysis - Preview Only
            st.markdown("### 🔍 Preview Dataset")
            st.dataframe(df.head(), use_container_width=True, height=250)
            
            # Configuration
            st.markdown('<div class="section-header"><span>2</span> Configuration</div>', unsafe_allow_html=True)
            
            col_conf1, col_conf2 = st.columns(2)
            
            with col_conf1:
                target_col = st.selectbox(
                    "Target Column",
                    options=df.columns.tolist(),
                    help="Select the column you want to predict"
                )
            
            with col_conf2:
                metrics = st.multiselect(
                    "Evaluation Metric(s)",
                    ["Accuracy", "F1 Score", "Precision", "Recall", "RMSE", "MAE", "R2"],
                    default=["Accuracy"],
                    help="Select one or more metrics for model evaluation"
                )

            # Get Recommendations
            st.markdown('<div class="section-header"><span>3</span> AI Recommendation</div>', unsafe_allow_html=True)
            
            # --- PERSISTENCE LOGIC START ---
            if "rec_recommendations" not in st.session_state:
                st.session_state["rec_recommendations"] = None
                st.session_state["rec_selection_id"] = None
                st.session_state["rec_task_type"] = None
            
            if st.button("🔍 Get Model Recommendations", type="primary"):
                if not metrics:
                    st.warning("Please select at least one evaluation metric.")
                else:
                    payload = {
                        "dataset_id": dataset_id,
                        "target_column": target_col,
                        "metrics": metrics
                    }
                    with st.spinner("🤖 Analyzing dataset and selecting best models..."):
                        try:
                            response = requests.post(f"{MODEL_SELECTOR_URL}/select", json=payload, timeout=60)
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state["rec_recommendations"] = data["models"]
                                st.session_state["rec_selection_id"] = data["recommendation_id"]
                                st.session_state["rec_task_type"] = data.get("task_type", "Unknown")
                                st.session_state["last_dataset_id"] = dataset_id
                            else:
                                st.error(f"Error: {response.text}")
                        except Exception as e:
                            st.error(f"Connection Error: {str(e)}")

            if st.session_state["rec_recommendations"]:
                recommendations = st.session_state["rec_recommendations"]
                selection_id = st.session_state["rec_selection_id"]
                detected_task = st.session_state["rec_task_type"]
                
                st.success(f"✅ Analysis Complete! Detected Task: **{detected_task}**")
                
                if recommendations:
                    st.markdown("### 🤖 Recommended Models")
                    for model in recommendations:
                        model_name = model.get('name', 'Unknown')
                        framework = model.get('framework', 'Unknown')
                        params = model.get('default_params', {})
                        
                        st.markdown(f"""
                        <div class="model-card">
                            <h3>🚀 {model_name} <span style="font-size: 0.8em; opacity: 0.7;">({framework})</span></h3>
                            <div class="model-justification">
                                <strong>Default Params:</strong> {params}<br>
                                <em>Optimization recommended by HyperOpt (Next Step)</em>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('<div class="section-header"><span>4</span> Automated Training</div>', unsafe_allow_html=True)
                    st.info(f"💡 The system suggests training **{len(recommendations)} models** with default hyperparameters.")
                    
                    if st.button("🔥 Train All Recommended Models", type="primary"):
                        with st.status("🚀 Initiating Training Sequence...", expanded=True) as status:
                            try:
                                payload = {
                                    "dataset_id": dataset_id,
                                    "recommendation_id": selection_id,
                                    "gpu_per_model": 0.5
                                }
                                resp = requests.post(f"{TRAINER_API_URL}/train", json=payload)
                                if resp.status_code == 200:
                                    jid = resp.json()["batch_job_id"]
                                    status.write(f"✅ Training batch started! Batch ID: `{jid}`")
                                    st.success(f"🎉 **Batch Created Successfully!**")
                                    st.markdown(f"""
                                    <div style="background-color: #d1fae5; padding: 20px; border-radius: 10px; border: 1px solid #10b981; margin: 20px 0; text-align: center;">
                                        <h3 style="color: #065f46; margin:0;">Batch ID</h3>
                                        <p style="color: #047857; margin: 10px 0;">Copy this ID to track progress in the Training Monitor:</p>
                                        <code style="font-size: 1.5rem; background: white; padding: 5px 15px; border-radius: 5px; border: 1px solid #10b981;">{jid}</code>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    status.write(f"❌ Batch start failed: {resp.text}")
                                    st.error(f"Trainer Error: {resp.text}")
                            except Exception as e:
                                status.write(f"❌ Error submitting batch: {e}")
                                st.error(str(e))
                            status.update(label="✅ Batch submission processed!", state="complete", expanded=False)
                else:
                    st.warning("No specific recommendations found.")

        except Exception as e:
            st.error(f"Could not load dataset with ID `{dataset_id}`. Please check the ID and try again.")
