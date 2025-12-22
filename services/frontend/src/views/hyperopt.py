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
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="section-header"><span>1</span> Configure Optimization</div>', unsafe_allow_html=True)
        model_type = st.selectbox("Model Type", ["RF", "XGBoost", "SVM"])
        target_metric = st.selectbox("Target Metric", ["auc", "accuracy", "f1", "rmse"])
        n_trials = st.slider("Number of Trials", 10, 100, 20)
        early_stopping = st.checkbox("Enable Early Stopping", value=True)
        
        st.markdown("### Search Space")
        if model_type == "RF":
            n_estimators_min = st.number_input("n_estimators min", 10, 500, 50)
            n_estimators_max = st.number_input("n_estimators max", 10, 500, 200)
            max_depth_min = st.number_input("max_depth min", 2, 20, 3)
            max_depth_max = st.number_input("max_depth max", 2, 20, 10)
            search_space = {
                "n_estimators": [n_estimators_min, n_estimators_max],
                "max_depth": [max_depth_min, max_depth_max]
            }
        elif model_type == "XGBoost":
            learning_rate_min = st.number_input("learning_rate min", 0.01, 1.0, 0.01)
            learning_rate_max = st.number_input("learning_rate max", 0.01, 1.0, 0.3)
            search_space = {
                "learning_rate": [learning_rate_min, learning_rate_max]
            }
        else:
            search_space = {"C": [0.1, 10.0]}

        if st.button("🚀 Start Optimization", type="primary"):
            payload = {
                "model": model_type,
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
        st.markdown('<div class="section-header"><span>2</span> Results & Monitoring</div>', unsafe_allow_html=True)
        run_id_input = st.text_input("Run ID to monitor", value=st.session_state.get("last_hyperopt_run_id", ""))
        
        if run_id_input:
            if st.button("🔄 Refresh Status"):
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
                st.markdown(f"**Status:** {run_data['status'].upper()}")
                st.progress(run_data['trials_completed'] / n_trials if n_trials > 0 else 0)
                
                col_m1, col_m2 = st.columns(2)
                col_m1.metric("Trials Completed", run_data['trials_completed'])
                col_m2.metric("Best Score", f"{run_data['best_score']:.4f}" if run_data['best_score'] else "N/A")
                
                if run_data['best_params']:
                    st.markdown("### 🏆 Best Hyperparameters")
                    st.json(run_data['best_params'])
                
                if run_data['status'] == "completed":
                    st.balloons()
