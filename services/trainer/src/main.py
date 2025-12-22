from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import logging
import os
import requests
from src.trainer_logic import start_training
from src.utils import get_job_status, get_job_result, update_job_status
from src.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AutoML Trainer Service")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_SELECTOR_URL = os.getenv("MODEL_SELECTOR_URL", "http://model_selector:8000")

class TrainRequest(BaseModel):
    dataset_id: str
    recommendation_id: str
    gpu_per_model: float = 0.5
    
class TrainResponse(BaseModel):
    batch_job_id: str
    status: str
    triggered_jobs: List[str]

from src.database import get_db
from src.models import TrainingBatch, TrainingJob # Ensure models are imported
from sqlalchemy.orm import Session
from fastapi import Depends

# ... (rest of imports)

async def orchestrate_training(batch_job_id: str, request: TrainRequest):
    """
    Orchestrates the training process: fetch models -> loop -> train
    """
    try:
        # Create DB session
        db = next(get_db())
        
        # 0. Persistence: Create Batch Record
        try:
            batch = TrainingBatch(
                id=batch_job_id,
                recommendation_id=request.recommendation_id,
                dataset_id=request.dataset_id
            )
            db.add(batch)
            db.commit()
            logger.info(f"Created batch record {batch_job_id}")
        except Exception as e:
            logger.error(f"Failed to create batch record: {e}")
            db.rollback()
            return

        # 1. Fetch Recommendations
        logger.info(f"Fetching recommendations for {request.recommendation_id} from {MODEL_SELECTOR_URL}")
        resp = requests.get(f"{MODEL_SELECTOR_URL}/recommendations/{request.recommendation_id}")
        resp.raise_for_status()
        data = resp.json()
        models = data.get("models", [])
        
        # New: Get Target and Metrics
        target_col = data.get("target_column")
        metrics = data.get("metrics", [])
        
        if not models:
            logger.warning(f"No models found for recommendation {request.recommendation_id}")
            return

        # 2. Loop and Train
        for model_obj in models:
            # Handle both string (legacy) and dict (new) for robustness during migration
            if isinstance(model_obj, str):
                model_name = model_obj
                model_params = {}
            else:
                model_name = model_obj.get("name")
                model_params = model_obj.get("default_params", {})

            job_id = str(uuid.uuid4())
            logger.info(f"Triggering training for {model_name} (Job {job_id})")
            
            # Merge GPU resource config with model default params
            # Priority: Request > Model Default > Hardcoded
            train_config = {"epochs": 20} # System default
            train_config.update(model_params) # Model specific defaults
            train_config.update({"gpu_resource": request.gpu_per_model}) # Request overrides
            
            # Add target and metrics to config
            if target_col: train_config["target_column"] = target_col
            if metrics: train_config["metrics"] = metrics

            job = TrainingJob(
                id=job_id,
                batch_id=batch_job_id,
                status="queued",
                model_type=model_name,
                data_id=request.dataset_id,
                hyperparameters=train_config
            )
            db.add(job)
            db.commit()
            
            # Launch actual training
            start_training(job_id, model_name, request.dataset_id, train_config)
            
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")


@app.post("/train", response_model=TrainResponse)
async def train(request: TrainRequest, background_tasks: BackgroundTasks):
    batch_job_id = str(uuid.uuid4())
    logger.info(f"Received training request for recommendation {request.recommendation_id}")
    
    # We acknowledge and start orchestration in background
    background_tasks.add_task(orchestrate_training, batch_job_id, request)
    
    return TrainResponse(
        batch_job_id=batch_job_id, 
        status="accepted",
        triggered_jobs=[] # We don't know IDs yet as they are generated in background
    )

@app.get("/train/status/{job_id}")
async def status(job_id: str, db: Session = Depends(get_db)):
    # 1. Check if it's a single Job
    # We use DB directly for more flexibility vs util
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if job:
        return {
            "status": job.status,
            "model_type": job.model_type,
            "data_id": job.data_id,
            "target_column": job.hyperparameters.get("target_column") if job.hyperparameters else None,
            "error": job.error
        }
        
    # 2. Check if it's a Batch
    batch = db.query(TrainingBatch).filter(TrainingBatch.id == job_id).first()
    if batch:
        # Return aggregated status or list of jobs
        # For simple UI display:
        jobs = batch.jobs
        if not jobs:
            return {"status": "queued", "type": "batch", "jobs": []}
            
        # Determine batch status
        statuses = [j.status for j in jobs]
        if "failed" in statuses:
            batch_status = "failed"
        elif "running" in statuses or "queued" in statuses:
            batch_status = "running"
        else:
            batch_status = "completed"
            
        return {
            "status": batch_status, 
            "type": "batch", 
            "jobs": [{"id": j.id, "status": j.status, "model": j.model_type} for j in jobs]
        }

    raise HTTPException(status_code=404, detail="Job or Batch not found")

@app.get("/train/result/{job_id}")
async def result(job_id: str):
    job_result = get_job_result(job_id)
    if not job_result:
        raise HTTPException(status_code=404, detail="Result not found or job still running")
    return job_result

@app.get("/health")
async def health():
    return {"status": "healthy"}
