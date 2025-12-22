from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import requests
import os

from .database import engine, Base, get_db
from .models import ModelSelectionLog
from .schemas import SelectionRequest, SelectionResponse, ModelInfo, RecommendationResponse
from .selector import selector
from .minio_client import minio_client
import pandas as pd

import json

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Model Selector Service")

# DataPreparer API URL
DATA_PREPARER_URL = os.getenv("DATA_PREPARER_URL", "http://data_preparer:8000")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/select", response_model=SelectionResponse)
def select_models(request: SelectionRequest, db: Session = Depends(get_db)):
    """
    Selects the best models based on dataset metadata.
    """
    # 1. Call DataPreparer API to verify dataset exists and get metadata
    try:
        prep_resp = requests.get(f"{DATA_PREPARER_URL}/status/{request.dataset_id}", timeout=10)
        if prep_resp.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_id} not found in DataPreparer")
        
        prep_data = prep_resp.json()
        if prep_data.get("status") != "COMPLETED":
            raise HTTPException(status_code=400, detail=f"Dataset {request.dataset_id} is not ready yet")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Cannot reach DataPreparer service: {str(e)}")
    
    # 2. Fetch Data from MinIO (now that we verified it exists via DataPreparer)
    try:
        df = minio_client.get_dataset(request.dataset_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to load dataset from MinIO: {str(e)}")

    # 3. Detect Task Type
    target = request.target_column
    if target not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target column '{target}' not found in dataset")
        
    y = df[target]
    
    task_type = "Classification"
    unique_ratio = y.nunique() / len(y)
    
    if pd.api.types.is_numeric_dtype(y):
        if unique_ratio > 0.05: # Threshold for regression usually low unique count implies classification (categorical encoded as int)
             task_type = "Regression"
    
    # 4. Analyze meta for selector
    rows, cols = df.shape
    
    # 5. Run Selection
    # Adjust selector to accept specific params or just metadata object
    candidates = selector.select_models(task_type, rows, cols, request.metrics)
    
    # 6. Log to Database
    # Store just the model names as comma-separated string
    # We strip extra info for storage simplicity requested previously, 
    # but re-hydrate it for API response.
    candidates_names = ", ".join([c.model_name for c in candidates])
    
    size_label = "small"
    if rows >= 50000: size_label = "large"
    elif rows >= 1000: size_label = "medium"
    
    log_entry = ModelSelectionLog(
        dataset_name=f"dataset_{request.dataset_id}",
        dataset_id=request.dataset_id,
        target_column=request.target_column,
        evaluation_metrics=",".join(request.metrics),
        task_type=task_type,
        dataset_size=size_label,
        shape_rows=rows,
        shape_cols=cols,
        selected_models=candidates_names,
        justification=candidates[0].justification if candidates else "No candidates"
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    
    # Construct strictly standardized models list
    models_info = []
    for c in candidates:
        # Infer framework for now (Mock logic as data is limited)
        fw = "sklearn"
        if "CNN" in c.model_name or "ResNet" in c.model_name: fw = "pytorch"
        elif "XGBoost" in c.model_name: fw = "xgboost"
        
        models_info.append({
            "name": c.model_name,
            "framework": fw,
            "default_params": {"epochs": 20} if fw == "pytorch" else {}
        })

    return {
        "recommendation_id": log_entry.id,
        "selection_id": log_entry.id, # Keep for compat short term
        "dataset_id": request.dataset_id,
        "task_type": task_type,
        "models": models_info
    }

@app.get("/recommendations/{selection_id}", response_model=RecommendationResponse)
def get_recommendations(selection_id: str, db: Session = Depends(get_db)):
    """
    Retrieve stored recommendations by ID (for Trainer).
    """
    log = db.query(ModelSelectionLog).filter(ModelSelectionLog.id == selection_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Recommendation ID not found")
        
    # Rehydrate from stored CSV
    raw_names = [m.strip() for m in log.selected_models.split(",")] if log.selected_models else []
    
    models_info = []
    for name in raw_names:
        fw = "sklearn"
        if "CNN" in name or "ResNet" in name: fw = "pytorch"
        elif "XGBoost" in name: fw = "xgboost"
        
        models_info.append({
            "name": name,
            "framework": fw,
            "default_params": {"epochs": 20} if fw == "pytorch" else {}
        })
    
    return {
        "recommendation_id": log.id,
        "dataset_id": log.dataset_id,
        "target_column": log.target_column,
        "metrics": log.evaluation_metrics.split(",") if log.evaluation_metrics else [],
        "task_type": log.task_type,
        "models": models_info
    }
