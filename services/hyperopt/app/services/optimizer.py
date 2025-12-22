import optuna
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..db.models import HyperOptRun, HyperOptTrial
from datetime import datetime

logger = logging.getLogger(__name__)

def create_objective(model_type: str, search_space: Dict[str, Any], target_metric: str):
    """
    Creates an Optuna objective function based on model and search space.
    NOTE: In a real system, this would involve training the model on validation data.
    For this microservice, we simulate or assume a scoring mechanism.
    If the user expects real training, this service would need to call the Trainer service or have data access.
    For now, we implement the Optuna structure.
    """
    def objective(trial: optuna.Trial):
        params = {}
        for key, value in search_space.items():
            if isinstance(value, list) and len(value) == 2:
                if isinstance(value[0], int) and isinstance(value[1], int):
                    params[key] = trial.suggest_int(key, value[0], value[1])
                elif isinstance(value[0], float) and isinstance(value[1], float):
                    params[key] = trial.suggest_float(key, value[0], value[1])
            elif isinstance(value, list):
                params[key] = trial.suggest_categorical(key, value)
        
        # Simulate a score (e.g., inversely proportional to depth or learning rate for demo)
        # In production, replace this with actual model training/evaluation call
        score = 0.5
        if model_type == "RF":
            score = 0.8 + (params.get("max_depth", 10) / 100) - (params.get("n_estimators", 100) / 10000)
        elif model_type == "XGBoost":
            score = 0.85 + (params.get("learning_rate", 0.1) * 0.5)
        
        return min(max(score, 0.0), 1.0) # Clamp between 0 and 1

    return objective

def run_optimization_task(
    run_id: str,
    model: str,
    target_metric: str,
    search_space: Dict[str, Any],
    n_trials: int,
    early_stopping: bool,
    db: Session
):
    try:
        run = db.query(HyperOptRun).filter(HyperOptRun.run_id == run_id).first()
        if not run:
            logger.error(f"Run {run_id} not found")
            return

        run.status = "running"
        db.commit()

        study = optuna.create_study(direction="maximize")
        objective = create_objective(model, search_space, target_metric)

        def callback(study, trial):
            # Log trial to DB
            trial_record = HyperOptTrial(
                run_id=run_id,
                trial_number=trial.number,
                params=trial.params,
                score=trial.value
            )
            db.add(trial_record)
            
            run.trials_completed = len(study.trials)
            run.best_score = study.best_value
            run.best_params = study.best_params
            db.commit()
            
            if early_stopping and len(study.trials) >= 10 and study.best_value > 0.99:
                study.stop()

        study.optimize(objective, n_trials=n_trials, callbacks=[callback])

        run.status = "completed"
        run.completed_at = datetime.now()
        db.commit()
        logger.info(f"Optimization {run_id} completed")

    except Exception as e:
        logger.error(f"Optimization {run_id} failed: {e}")
        if run:
            run.status = "failed"
            db.commit()
