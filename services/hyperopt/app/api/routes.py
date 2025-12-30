from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..db.session import get_db
from ..db.models import HyperOptRun
from ..services.optimizer import run_optimization_task
from ..services.redis_queue import queue_optimization
from pydantic import BaseModel
import uuid

router = APIRouter()

class SearchSpace(BaseModel):
    # Flexible container for search space
    # e.g., {"n_estimators": [10, 100], "learning_rate": [0.01, 0.1], "model": ["RF", "XGB"]}
    params: Dict[str, Any]

class OptimizeRequest(BaseModel):
    model: str
    dataset_id: str
    target_column: str
    target_metric: str
    search_space: Dict[str, Any]
    n_trials: int = 20
    early_stopping: bool = True

class OptimizeResponse(BaseModel):
    run_id: str
    status: str

@router.post("/optimize", response_model=OptimizeResponse)
async def optimize(request: OptimizeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run_id = str(uuid.uuid4())
    
    # Create run record
    run = HyperOptRun(
        run_id=run_id,
        model=request.model,
        target_metric=request.target_metric,
        search_space=request.search_space,
        status="pending"
    )
    db.add(run)
    db.commit()
    
    # Queue in Redis (as requested)
    queue_optimization(run_id, request.dict())
    
    # For this implementation, we also trigger it in FastAPI BackgroundTasks 
    # to actually execute it unless we implement a separate worker script.
    background_tasks.add_task(
        run_optimization_task,
        run_id,
        request.model,
        request.dataset_id,
        request.target_column,
        request.target_metric,
        request.search_space,
        request.n_trials,
        request.early_stopping,
        next(get_db()) # Use a new session
    )
    
    return OptimizeResponse(run_id=run_id, status="accepted")

@router.get("/optimize/{run_id}")
async def get_run_status(run_id: str, db: Session = Depends(get_db)):
    run = db.query(HyperOptRun).filter(HyperOptRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    from ..db.models import HyperOptTrial
    trials = db.query(HyperOptTrial).filter(HyperOptTrial.run_id == run_id).order_by(HyperOptTrial.trial_number).all()
        
    return {
        "run_id": run.run_id,
        "model": run.model,
        "status": run.status,
        "best_params": run.best_params,
        "best_score": run.best_score,
        "trials_completed": run.trials_completed,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
        "trials": [
            {
                "number": t.trial_number,
                "score": t.score,
                "params": t.params
            } for t in trials
        ]
    }
