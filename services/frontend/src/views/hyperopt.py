import streamlit as st
import requests
from config import HYPEROPT_API_URL

def hyperopt_page():
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">🧪 Hyperparameter Optimization</div>
        <div class="header-subtitle">Tune your model's hyperparameters using Optuna (Bayesian Optimization)</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Context Selection
    st.markdown('<div class="section-header"><span>1</span> Context Selection</div>', unsafe_allow_html=True)
    
    col_ctx1, col_ctx2 = st.columns(2)
    with col_ctx1:
        dataset_id = st.text_input("Dataset ID", value=st.session_state.get("shared_dataset_id", ""), help="The unique ID of your prepared dataset.")
        st.session_state["shared_dataset_id"] = dataset_id
    with col_ctx2:
        target_col = st.text_input("Target Column", value=st.session_state.get("shared_target_column", ""), help="The column you want the model to predict.")
        st.session_state["shared_target_column"] = target_col
    
    recommendations = st.session_state.get("rec_recommendations", [])
    if recommendations:
        model_names = [m.get("name") for m in recommendations]
        selected_model_name = st.selectbox("Select Model to Optimize", model_names, help="Choose one of the models recommended by the AI.")
        task_type = st.session_state.get("rec_task_type", "Classification")
    else:
        selected_model_name = st.selectbox("Model Type", ["RandomForestClassifier", "RandomForestRegressor", "XGBoost", "SVC", "SVR"])
        task_type = "Classification" if "Classifier" in selected_model_name or "SVC" in selected_model_name else "Regression"

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="section-header"><span>2</span> Configuration</div>', unsafe_allow_html=True)
        
        target_metric = st.selectbox("Target Metric", 
            ["accuracy", "f1", "precision", "recall"] if "Classification" in task_type else ["rmse", "mae", "r2"],
            help="The evaluation score HyperOpt will try to maximize (or minimize).")
        
        n_trials = st.slider("Number of Trials", 5, 100, 10, help="How many different configurations HyperOpt should test.")
        early_stopping = st.checkbox("Enable Early Stopping", value=True, help="Stop optimization if no improvement is found after several trials.")
        
        st.markdown("### 🧩 Search Space")
        search_space = {}
        
        # Dynamic Parameters Display
        if "RandomForest" in selected_model_name:
            st.info("Configuring Random Forest parameters")
            col_rf1, col_rf2 = st.columns(2)
            with col_rf1:
                n_estimators_min = st.number_input("n_estimators min", 10, 500, 50, help="Minimum number of trees in the forest.")
                n_estimators_max = st.number_input("n_estimators max", 10, 1000, 200, help="Maximum number of trees in the forest.")
            with col_rf2:
                max_depth_min = st.number_input("max_depth min", 2, 20, 3, help="Minimum depth of each tree.")
                max_depth_max = st.number_input("max_depth max", 2, 50, 10, help="Maximum depth of each tree.")
            search_space = {
                "n_estimators": [int(n_estimators_min), int(n_estimators_max)],
                "max_depth": [int(max_depth_min), int(max_depth_max)]
            }
        elif "XGBoost" in selected_model_name:
            st.info("Configuring XGBoost parameters")
            learning_rate_min = st.number_input("learning_rate min", 0.001, 1.0, 0.01, format="%.3f", help="Minimum step size shrinkage used in update to prevent overfitting.")
            learning_rate_max = st.number_input("learning_rate max", 0.01, 1.0, 0.3, format="%.3f", help="Maximum step size shrinkage.")
            search_space = {
                "learning_rate": [float(learning_rate_min), float(learning_rate_max)]
            }
        elif "SVC" in selected_model_name or "SVR" in selected_model_name:
            st.info("Configuring SVM parameters")
            c_min = st.number_input("C min", 0.01, 100.0, 0.1, help="Regularization parameter. The strength of the regularization is inversely proportional to C.")
            c_max = st.number_input("C max", 0.1, 1000.0, 10.0, help="Maximum regularization parameter.")
            search_space = {
                "C": [float(c_min), float(c_max)]
            }

        if st.button("🚀 Start Optimization", type="primary", use_container_width=True):
            if not dataset_id or not target_col:
                st.error("Please provide Dataset ID and Target Column.")
            else:
                payload = {
                    "model": selected_model_name,
                    "dataset_id": dataset_id,
                    "target_column": target_col,
                    "target_metric": target_metric,
                    "search_space": search_space,
                    "n_trials": n_trials,
                    "early_stopping": early_stopping
                }
                try:
                    resp = requests.post(f"{HYPEROPT_API_URL}/optimize", json=payload)
                    if resp.status_code == 200:
                        run_id = resp.json()["run_id"]
                        st.success(f"Optimization started! Run ID: `{run_id}`")
                        st.session_state["last_hyperopt_run_id"] = run_id
                    else:
                        st.error(f"Error starting optimization: {resp.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    with col2:
        st.markdown('<div class="section-header"><span>3</span> Results & Monitoring</div>', unsafe_allow_html=True)
        run_id_input = st.text_input("Run ID to monitor", value=st.session_state.get("last_hyperopt_run_id", ""), help="Paste an ID to check its progress.")
        
        if run_id_input:
            if st.button("🔄 Refresh Status", use_container_width=True):
                try:
                    resp = requests.get(f"{HYPEROPT_API_URL}/optimize/{run_id_input}")
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state[f"run_{run_id_input}"] = data
                    else:
                        st.error("Run not found")
                except Exception as e:
                    st.error(f"Error fetching status: {e}")
            
            run_data = st.session_state.get(f"run_{run_id_input}")
            if run_data:
                # Dashboard
                st.markdown(f"**Status:** `{run_data['status'].upper()}`")
                prog = run_data['trials_completed'] / n_trials if n_trials > 0 else 0
                st.progress(min(prog, 1.0))
                
                col_m1, col_m2 = st.columns(2)
                col_m1.metric("Trials Completed", run_data['trials_completed'])
                col_m2.metric("Best Score", f"{run_data['best_score']:.4f}" if run_data.get('best_score') is not None else "N/A")
                
                # Trials Visualizations
                trials = run_data.get("trials", [])
                if trials:
                    st.markdown("### 📈 Trials Score Evolution")
                    # Prepare data for chart
                    score_data = [t["score"] for t in trials]
                    st.line_chart(score_data)
                    
                    with st.expander("📄 View All Trials History"):
                        df_trials = st.dataframe([
                            {"Trial": t["number"], "Score": t["score"], **t["params"]}
                            for t in trials
                        ], use_container_width=True)
                
                if run_data.get('best_params'):
                    st.markdown("### 🏆 Best Hyperparameters")
                    st.info("Use these parameters for your final model training.")
                    st.json(run_data['best_params'])
                
                if run_data['status'] == "completed":
                    st.balloons()
                    st.success("Optimization Done!")
