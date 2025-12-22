import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px
import streamlit.components.v1 as components
from config import TRAINER_API_URL, EVALUATOR_API_URL, MINIO_BUCKET_PROCESSED
from utils import get_minio_client

# Define the bucket name for artifacts based on evaluator logic
BUCKET_ARTIFACTS = "evaluation-artifacts"

def model_evaluation_page():
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">📈 Model Evaluation</div>
        <div class="header-subtitle">Evaluate and compare all models from your AutoML experiments</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Info banner
    st.info("💡 **How it works**: Select an experiment to automatically evaluate all trained models and generate a comparative report.")
    
    # 1. Experiment Selection
    st.markdown('<div class="section-header"><span>1</span> Select Experiment</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    experiment_id = None
    task_type = "classification"
    ranking_metric = "f1"

    with col1:
        # Fetch available batch jobs from Trainer
        try:
            trainer_resp = requests.get(f"{TRAINER_API_URL}/train/batches", timeout=5)
            if trainer_resp.status_code == 200:
                batches = trainer_resp.json().get("batches", [])
                if batches:
                    batch_options = {f"{b['id']} ({b.get('status', 'unknown')} - {b.get('created_at', 'N/A')[:10]})": b['id'] for b in batches}
                    selected_display = st.selectbox(
                        "Experiment ID",
                        options=list(batch_options.keys()),
                        help="Select a training batch to evaluate"
                    )
                    experiment_id = batch_options[selected_display]
                else:
                    st.warning("No training batches found. Please train models first in the 'Model Training' page.")
                    experiment_id = st.text_input("Or enter Experiment ID manually", help="Paste a batch_job_id from training")
            else:
                experiment_id = st.text_input("Experiment ID", help="Enter the batch_job_id from your training run")
        except:
            experiment_id = st.text_input("Experiment ID", help="Enter the batch_job_id from your training run")
    
    with col2:
        task_type = st.selectbox("Task Type", ["classification", "regression"], help="Type of ML task")
    
    # Advanced mode (collapsed by default)
    with st.expander("⚙️ Advanced Options (Optional)", expanded=False):
        st.markdown("Override default settings if needed:")
        col_adv1, col_adv2 = st.columns(2)
        with col_adv1:
            override_dataset = st.text_input("Override Test Dataset ID", help="Leave empty to use training dataset")
        with col_adv2:
            override_target = st.text_input("Override Target Column", help="Leave empty to use training target")
        
        metrics_list = ["f1", "accuracy", "auc", "precision", "recall"] if task_type == "classification" else ["rmse", "mae", "r2"]
        ranking_metric = st.selectbox(
            "Ranking Metric",
            metrics_list,
            help="Metric used to rank models in comparison table"
        )
    
    # 2. Action Button
    st.markdown('<div class="section-header"><span>2</span> Run Evaluation</div>', unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    with col_btn2:
        run_evaluation = st.button("🚀 Evaluate All Models", type="primary", use_container_width=True)
    
    if run_evaluation:
        if not experiment_id:
            st.error("Please select or enter an Experiment ID.")
        else:
            with st.status("🔄 **Launching Evaluation Pipeline...**", expanded=True) as status:
                try:
                    # Fetch batch details from Trainer to get model_ids
                    status.write("📡 Fetching experiment details from Trainer...")
                    batch_resp = requests.get(f"{TRAINER_API_URL}/train/status/{experiment_id}")
                    
                    if batch_resp.status_code != 200:
                        st.error(f"Experiment not found: {experiment_id}")
                        status.update(label="❌ Experiment Not Found", state="error")
                        st.stop()
                    
                    batch_data = batch_resp.json()
                    model_ids = [job['id'] for job in batch_data.get('jobs', [])]
                    
                    if not model_ids:
                        st.error("No models found in this experiment.")
                        status.update(label="❌ No Models Found", state="error")
                        st.stop()
                    
                    status.write(f"✅ Found {len(model_ids)} models to evaluate")
                    
                    # Prepare evaluation payload
                    payload = {
                        "experiment_id": experiment_id,
                        "task_type": task_type,
                        "model_ids": model_ids
                    }
                    
                    if override_dataset:
                        payload["dataset_id"] = override_dataset
                    if override_target:
                        payload["target_column"] = override_target
                    
                    # Submit batch evaluation
                    status.write("⚡ Submitting batch evaluation...")
                    eval_resp = requests.post(f"{EVALUATOR_API_URL}/evaluate", json=payload)
                    
                    if eval_resp.status_code == 200:
                        eval_data = eval_resp.json()
                        job_ids = eval_data.get("job_ids", [])
                        status.write(f"✅ Evaluation started for {len(job_ids)} models")
                        
                        # Poll experiment status
                        status.write("⏳ Evaluating models...")
                        progress_bar = st.progress(0)
                        
                        for i in range(60):  # 90s timeout
                            time.sleep(1.5)
                            progress_bar.progress((i+1)/60)
                            
                            exp_status_resp = requests.get(f"{EVALUATOR_API_URL}/experiment/{experiment_id}/status")
                            if exp_status_resp.status_code == 200:
                                exp_status = exp_status_resp.json()
                                overall = exp_status.get("overall_status")
                                
                                if overall == "completed":
                                    status.write("✅ All evaluations completed!")
                                    st.session_state["last_evaluation_experiment_id"] = experiment_id
                                    st.session_state["eval_ranking_metric"] = ranking_metric
                                    progress_bar.progress(1.0)
                                    break
                                elif overall == "failed":
                                    status.write("❌ Some evaluations failed")
                                    st.session_state["last_evaluation_experiment_id"] = experiment_id
                                    st.session_state["eval_ranking_metric"] = ranking_metric
                                    break
                        
                        status.update(label="✅ Evaluation Pipeline Complete!", state="complete", expanded=False)
                        st.balloons()
                        
                    else:
                        st.error(f"Failed to start evaluation: {eval_resp.text}")
                        status.update(label="❌ Submission Failed", state="error")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
                    status.update(label="❌ Error", state="error")

    # 3. Results Display
    current_exp_id = st.session_state.get("last_evaluation_experiment_id") or experiment_id
    
    if current_exp_id:
        st.markdown('<div class="section-header"><span>3</span> Comparative Results</div>', unsafe_allow_html=True)
        
        try:
            # Fetch comparative report
            rank_m = st.session_state.get("eval_ranking_metric", ranking_metric)
            compare_resp = requests.get(f"{EVALUATOR_API_URL}/compare/{current_exp_id}?ranking_metric={rank_m}")
            
            if compare_resp.status_code == 200:
                comparison = compare_resp.json()
                models_data = comparison.get("models", [])
                
                if models_data:
                    df_results = pd.DataFrame(models_data)
                    
                    # Clean display - Remove some columns for the summary table
                    display_cols = ["model_name", rank_m] + [c for c in df_results.columns if c not in ["model_name", rank_m, "model_id", "evaluation_job_id", "artifacts"]]
                    
                    st.subheader(f"📊 Model Rankings by {rank_m.upper()}")
                    st.dataframe(
                        df_results[display_cols].style.highlight_max(axis=0, subset=[rank_m] if rank_m not in ["rmse", "mae"] else [])
                        .highlight_min(axis=0, subset=[rank_m] if rank_m in ["rmse", "mae"] else []),
                        use_container_width=True
                    )
                    
                    # Comparative Chart
                    st.subheader("📈 Performance Comparison")
                    fig = px.bar(
                        df_results, 
                        x="model_name", 
                        y=rank_m, 
                        color="model_name",
                        title=f"{rank_m.upper()} Comparison",
                        text_auto='.3f'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Detailed per-model view
                    st.markdown('<div class="section-header"><span>4</span> Individual Model Details</div>', unsafe_allow_html=True)
                    
                    selected_model_name = st.selectbox(
                        "Select a model to view detailed plots",
                        options=df_results["model_name"].tolist()
                    )
                    
                    if selected_model_name:
                        model_row = df_results[df_results["model_name"] == selected_model_name].iloc[0]
                        artifacts = model_row.get("artifacts", {})
                        eval_job_id = model_row.get("evaluation_job_id")
                        
                        st.markdown(f"### 🎯 Focus: {selected_model_name}")
                        
                        # Display metrics in cards
                        m_cols = st.columns(len(metrics_list))
                        for i, m in enumerate(metrics_list):
                            val = model_row.get(m)
                            if val is not None:
                                m_cols[i].metric(m.upper(), f"{val:.4f}")
                        
                        # Display Artifacts (Plots from MinIO)
                        if artifacts:
                            st.markdown("#### 🖼️ Evaluation Plots")
                            art_cols = st.columns(len(artifacts))
                            client = get_minio_client()
                            
                            for i, (art_name, art_path) in enumerate(artifacts.items()):
                                with art_cols[i]:
                                    try:
                                        # Fetch HTML from MinIO
                                        response = client.get_object(BUCKET_ARTIFACTS, art_path)
                                        html_content = response.read().decode('utf-8')
                                        st.markdown(f"**{art_name.replace('_', ' ').title()}**")
                                        components.html(html_content, height=450, scrolling=True)
                                    except Exception as e:
                                        st.error(f"Failed to load plot {art_name}: {e}")
                        else:
                            st.info("No plots available for this model.")
                else:
                    st.info("No completed evaluations found for this experiment yet.")
            else:
                st.info("Select an experiment and click 'Evaluate' to see results.")
        except Exception as e:
            st.error(f"Error loading results: {e}")

