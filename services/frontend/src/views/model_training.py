import streamlit as st
import requests
from config import TRAINER_API_URL

def model_training_page():
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">🚀 Training Monitor</div>
        <div class="header-subtitle">Track the progress of your distributed training jobs</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("ℹ️ **Note**: Use the 'Model Selection' page to trigger new training jobs based on AI recommendations.")
    
    # 1. Input Section
    st.markdown('<div class="section-header"><span>1</span> Trace Job</div>', unsafe_allow_html=True)
    
    # Auto-fill from session
    default_job_id = st.session_state.get("current_job_id", "")
    
    job_id = st.text_input(
        "Enter Batch ID or Job ID",
        value=default_job_id,
        help="Paste the ID returned after launching training"
    )

    if st.button("🔎 Check Status", type="primary") or job_id:
        if not job_id:
            st.warning("Please enter a Job ID.")
            return

        st.session_state["current_job_id"] = job_id
        
        # 2. Monitoring Section
        st.markdown('<div class="section-header"><span>2</span> Real-time Status</div>', unsafe_allow_html=True)
        
        status_container = st.empty()
        
        try:
            res = requests.get(f"{TRAINER_API_URL}/train/status/{job_id}")
            
            if res.status_code == 200:
                status_data = res.json()
                status = status_data.get("status", "unknown")
                type_ = status_data.get("type", "job")
                
                # Display Status
                st.markdown(f"### {type_.capitalize()} ID: `{job_id}`")
                
                if type_ == "batch":
                    # Batch Display
                    st.info(f"📦 **Batch Status:** {status.capitalize()}")
                    
                    jobs = status_data.get("jobs", [])
                    if jobs:
                        st.markdown("#### Child Jobs")
                        for j in jobs:
                            emoji = "⏳"
                            if j['status'] == 'running': emoji = "🔄"
                            elif j['status'] == 'completed': emoji = "✅"
                            elif j['status'] == 'failed': emoji = "❌"
                            
                            st.write(f"{emoji} **{j['model']}** (`{j['id']}`): {j['status']}")
                            
                else:
                    # Single Job Display
                    if status == "queued":
                        st.info(f"⏳ **Status:** En attente (Queued)...")
                    elif status == "running":
                        st.warning(f"🔄 **Status:** Entraînement en cours (Running)...")
                    elif status == "completed":
                        st.success(f"✅ **Status:** Entraînement terminé (Completed)!")
                        st.balloons()
                        
                        # Fetch Results
                        result_res = requests.get(f"{TRAINER_API_URL}/train/result/{job_id}")
                        if result_res.status_code == 200:
                            results = result_res.json()
                            st.markdown("### 📊 Training Results")
                            cols = st.columns(3)
                            cols[0].metric("Loss", f"{results.get('loss', 0):.4f}")
                            cols[1].metric("MLflow Run", results.get("mlflow_run_id", "N/A"))
                            
                            st.markdown("#### 🔗 External Dashboards")
                            st.markdown(f"- [Track in MLflow](http://localhost:5000)")
                            st.markdown(f"- [View Checkpoints in MinIO](http://localhost:9001)")
                    elif status == "failed":
                        st.error(f"❌ **Status:** Échec de l'entraînement (Failed)")
                        st.error(f"Error details: {status_data.get('error', 'Unknown error')}")
            
            else:
                st.error("Job or Batch not found. Please check Adminer.")
                
        except Exception as e:
            st.error(f"Connection Error: {str(e)}")
