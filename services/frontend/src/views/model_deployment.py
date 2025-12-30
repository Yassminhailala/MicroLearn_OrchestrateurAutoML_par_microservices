import streamlit as st
import requests
import pandas as pd
from config import DEPLOYER_API_URL, TRAINER_API_URL

def model_deployment_page():
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">🚀 Model Deployment</div>
        <div class="header-subtitle">Deploy your trained models as REST APIs, Batch jobs, or Edge containers</div>
    </div>
    """, unsafe_allow_html=True)

    st.info("💡 **How it works**: Select a model trained in previous steps, choose your deployment target, and let the platform package it for you.")

    # 1. Model Selection
    st.markdown('<div class="section-header"><span>1</span> Select Model to Deploy</div>', unsafe_allow_html=True)
    
    model_id = None
    
    # Try to fetch completed models from Trainer DB (via status endpoint if available, or manual input)
    col1, col2 = st.columns([2, 1])
    with col1:
        # User manual state sync using shared key
        model_id = st.text_input("Model ID", value=st.session_state.get("shared_model_id", ""), help="Enter the ID of the model you want to deploy")
        st.session_state["shared_model_id"] = model_id
    
    with col2:
        deployment_type = st.selectbox(
            "Deployment Type",
            ["rest", "batch", "edge"],
            help="REST: API via TorchServe, Batch: Offline script, Edge: Docker container"
        )

    # 2. Deployment Action
    st.markdown('<div class="section-header"><span>2</span> Configure & Launch</div>', unsafe_allow_html=True)
    
    if st.button("🚀 Launch Deployment", type="primary"):
        if not model_id:
            st.error("Please provide a Model ID.")
        else:
            with st.status(f"📦 Packaging model {model_id} for {deployment_type}...", expanded=True) as status:
                try:
                    payload = {
                        "model_id": model_id,
                        "type": deployment_type
                    }
                    resp = requests.post(f"{DEPLOYER_API_URL}/deploy/", json=payload, timeout=60)
                    
                    if resp.status_code == 201:
                        data = resp.json()
                        status.update(label="✅ Deployment Successful!", state="complete")
                        st.success(f"Deployment successful with ID: {data.get('deployment_id')}")
                        
                        if deployment_type == "rest":
                            st.markdown(f"### 🌐 REST Endpoint")
                            st.code(data.get("url"))
                        elif deployment_type == "batch":
                            st.markdown(f"### 📄 Batch Artifact Path")
                            st.code(data.get("url"))
                        elif deployment_type == "edge":
                            st.markdown(f"### 🐳 Edge Dockerfile Path")
                            st.code(data.get("url"))
                            
                        st.balloons()
                    else:
                        status.update(label="❌ Deployment Failed", state="error")
                        st.error(f"Error: {resp.text}")
                except Exception as e:
                    status.update(label="❌ Error", state="error")
                    st.error(f"Failed to connect to Deployer: {e}")

    # 3. History
    st.markdown('<div class="section-header"><span>3</span> Deployment History</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Refresh History"):
        try:
            resp = requests.get(f"{DEPLOYER_API_URL}/deploy/", timeout=10)
            if resp.status_code == 200:
                history = resp.json()
                if history:
                    df = pd.DataFrame(history)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No deployments found yet.")
            else:
                st.error("Failed to fetch history.")
        except Exception as e:
            st.error(f"Error fetching history: {e}")
