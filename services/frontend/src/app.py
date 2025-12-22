import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import time
import os
import json

# Modular Imports
from views.data_preparation import data_preparation_page
from views.model_selection import model_selection_page
from views.hyperopt import hyperopt_page
from views.model_training import model_training_page
from views.model_evaluation import model_evaluation_page

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
    page_type = st.radio(
        "Navigation",
        ["📊 Data Preparation", "🤖 Model Selection", "🚀 Model Training", "📈 Model Evaluation", "🧪 HyperOpt"],
        key="navigation"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Info section
    with st.expander("ℹ️ About", expanded=False):
        st.markdown("""
        **AutoML Platform** provides:
        
        - 📊 **Data Preparation**: Clean and preprocess your data
        - 🤖 **Model Selection**: Get AI-powered model recommendations
        - 🧪 **HyperOpt**: Optimisation des hyperparamètres
        - ⚡ **Automated Pipelines**: End-to-end ML workflow
        
        Upload your data and let AI do the heavy lifting!
        """)


# Main app logic
if __name__ == "__main__":
    # Route to correct page
    if "Data Preparation" in page_type:
        data_preparation_page()
    elif "Model Selection" in page_type:
        model_selection_page()
    elif "Model Training" in page_type:
        model_training_page()
    elif "Model Evaluation" in page_type:
        model_evaluation_page()
    elif "HyperOpt" in page_type:
        hyperopt_page()
