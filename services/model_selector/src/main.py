from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .database import engine, Base, get_db
from .models import ModelSelectionLog
from .schemas import DatasetMetadata, SelectionResponse, ModelCandidate
from .selector import selector

import json

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Model Selector Service")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/select", response_model=SelectionResponse)
def select_models(metadata: DatasetMetadata, db: Session = Depends(get_db)):
    """
    Selects the best models based on dataset metadata.
    """
    # 1. Run Selection Logic
    candidates = selector.select_models(metadata)
    
    # 2. Log to Database
    # Convert candidates to JSON string for storage
    candidates_json = json.dumps([c.model_dump() for c in candidates])
    
    size_label = "small"
    if metadata.rows >= 50000: size_label = "large"
    elif metadata.rows >= 1000: size_label = "medium"
    
    log_entry = ModelSelectionLog(
        dataset_name=metadata.dataset_name,
        task_type=metadata.task_type,
        dataset_size=size_label,
        shape_rows=metadata.rows,
        shape_cols=metadata.columns,
        selected_models=candidates_json,
        justification=candidates[0].justification if candidates else "No candidates"
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    
    return SelectionResponse(
        recommended_models=candidates,
        selection_id=log_entry.id
    )
