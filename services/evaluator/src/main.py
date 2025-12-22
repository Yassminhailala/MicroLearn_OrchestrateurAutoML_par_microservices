from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import logging
import requests
import os
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database import engine, Base, get_db
from src.models import EvaluationJob, ModelResults
from src.evaluator_logic import run_evaluation

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AutoML Evaluator Service")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Trainer API URL
TRAINER_API_URL = os.getenv("TRAINER_API_URL", "http://trainer:8000")

class EvaluateRequest(BaseModel):
    experiment_id: str
    task_type: str  # classification | regression
    model_ids: List[str]
    dataset_id: Optional[str] = None  # If None, use dataset from model metadata
    target_column: Optional[str] = None

class EvaluateResponse(BaseModel):
    experiment_id: str
    job_ids: List[str]
    status: str

@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_batch(request: EvaluateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Batch evaluation endpoint.
    Evaluates multiple models from the same experiment.
    """
    job_ids = []
    
    for model_id in request.model_ids:
        # Fetch model metadata from Trainer API instead of DB
        try:
            trainer_url = f"{TRAINER_API_URL}/train/status/{model_id}"
            logger.info(f"Fetching metadata from: {trainer_url}")
            trainer_resp = requests.get(trainer_url, timeout=10)
            
            if trainer_resp.status_code != 200:
                logger.warning(f"Model {model_id} not found in Trainer (Status {trainer_resp.status_code}), skipping")
                continue
            
            model_data = trainer_resp.json()
            logger.info(f"Received metadata for {model_id}: {model_data}")
            
            model_name = model_data.get("model_type", "Unknown")
            # Correct mapping: use "data_id" from Trainer response
            dataset_id = request.dataset_id or model_data.get("data_id") or model_data.get("dataset_id")
            target_column = request.target_column or model_data.get("target_column")
            
            logger.info(f"Final mapping for {model_id}: dataset_id={dataset_id}, target_column={target_column}")
            
        except Exception as e:
            logger.error(f"Failed to fetch metadata for {model_id}: {e}")
            # Use defaults
            model_name = "Unknown"
            dataset_id = request.dataset_id
            target_column = request.target_column
        
        # Create Evaluation Job
        job_id = str(uuid.uuid4())
        logger.info(f"Creating job {job_id} for model {model_id} with dataset {dataset_id}")
        job = EvaluationJob(
            id=job_id,
            experiment_id=request.experiment_id,
            model_id=model_id,
            model_name=model_name,
            dataset_id=dataset_id,
            task_type=request.task_type,
            status="pending"
        )
        db.add(job)
        job_ids.append(job_id)
    
    db.commit()
    
    # Trigger background evaluations
    for job_id in job_ids:
        job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
        background_tasks.add_task(
            run_evaluation,
            job_id,
            job.experiment_id,
            job.model_id,
            job.model_name,
            job.dataset_id,
            target_column,
            job.task_type
        )
    
    return EvaluateResponse(
        experiment_id=request.experiment_id,
        job_ids=job_ids,
        status="accepted"
    )

@app.get("/status/{job_id}")
async def get_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": job.id,
        "experiment_id": job.experiment_id,
        "model_id": job.model_id,
        "status": job.status,
        "error": job.error
    }

@app.get("/results/{job_id}")
async def get_results(job_id: str, db: Session = Depends(get_db)):
    job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
        
    return {
        "job_id": job.id,
        "experiment_id": job.experiment_id,
        "model_id": job.model_id,
        "model_name": job.model_name,
        "metrics": job.metrics,
        "artifacts": job.artifacts
    }

@app.get("/compare/{experiment_id}")
async def compare_models(experiment_id: str, ranking_metric: str = "f1", db: Session = Depends(get_db)):
    """
    Generate comparative report for all models in an experiment.
    Returns a ranked table of model performances.
    """
    # Query all results for this experiment
    results = db.query(ModelResults).filter(
        ModelResults.experiment_id == experiment_id
    ).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found for this experiment")
    
    # Build comparison table
    models = []
    for result in results:
        # Fetch artifacts from the EvaluationJob
        job = db.query(EvaluationJob).filter(EvaluationJob.id == result.evaluation_job_id).first()
        model_data = {
            "model_id": result.model_id,
            "evaluation_job_id": result.evaluation_job_id,
            "model_name": result.model_name,
            "artifacts": job.artifacts if job else {},
            **result.all_metrics
        }
        models.append(model_data)
    
    # Sort by ranking metric (descending for most metrics, ascending for RMSE/MAE)
    reverse = ranking_metric not in ["rmse", "mae"]
    models_sorted = sorted(
        models,
        key=lambda x: x.get(ranking_metric, 0 if reverse else float('inf')),
        reverse=reverse
    )
    
    return {
        "experiment_id": experiment_id,
        "ranking_metric": ranking_metric,
        "total_models": len(models_sorted),
        "models": models_sorted
    }

@app.get("/experiment/{experiment_id}/status")
async def get_experiment_status(experiment_id: str, db: Session = Depends(get_db)):
    """
    Get overall status of an experiment's evaluation jobs.
    """
    jobs = db.query(EvaluationJob).filter(
        EvaluationJob.experiment_id == experiment_id
    ).all()
    
    if not jobs:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    status_counts = {}
    for job in jobs:
        status_counts[job.status] = status_counts.get(job.status, 0) + 1
    
    all_completed = all(job.status == "completed" for job in jobs)
    any_failed = any(job.status == "failed" for job in jobs)
    
    overall_status = "completed" if all_completed else ("failed" if any_failed else "running")
    
    return {
        "experiment_id": experiment_id,
        "overall_status": overall_status,
        "total_jobs": len(jobs),
        "status_breakdown": status_counts,
        "jobs": [
            {
                "job_id": job.id,
                "model_id": job.model_id,
                "model_name": job.model_name,
                "status": job.status
            }
            for job in jobs
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
