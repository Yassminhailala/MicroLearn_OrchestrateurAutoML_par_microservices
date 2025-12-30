import optuna
import logging
import requests
import time
import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..db.models import HyperOptRun, HyperOptTrial
from datetime import datetime

logger = logging.getLogger(__name__)

TRAINER_URL = os.getenv("TRAINER_URL", "http://trainer:8000")
EVALUATOR_URL = os.getenv("EVALUATOR_URL", "http://evaluator:8000")

def poll_trainer(job_id: str, timeout: int = 300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            resp = requests.get(f"{TRAINER_URL}/train/status/{job_id}")
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status")
                if status == "completed":
                    return True
                if status == "failed":
                    logger.error(f"Trainer job {job_id} failed: {data.get('error')}")
                    return False
        except Exception as e:
            logger.warning(f"Error polling trainer {job_id}: {e}")
        time.sleep(2)
    return False

def poll_evaluator(job_id: str, timeout: int = 300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            resp = requests.get(f"{EVALUATOR_URL}/status/{job_id}")
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status")
                if status == "completed":
                    return True
                if status == "failed":
                    logger.error(f"Evaluator job {job_id} failed: {data.get('error')}")
                    return False
        except Exception as e:
            logger.warning(f"Error polling evaluator {job_id}: {e}")
        time.sleep(2)
    return False

def create_objective(run_id: str, model_type: str, dataset_id: str, target_column: str, target_metric: str, search_space: Dict[str, Any]):
    logger.info(f"Creating objective for run {run_id} with search space: {search_space}")
    def objective(trial: optuna.Trial):
        params = {}
        for key, value in search_space.items():
            if isinstance(value, list) and len(value) == 2:
                # Robustly detect if it should be an integer range
                # If both are integers (or floats that are actually integers like 10.0)
                is_int_range = all(isinstance(v, (int, float)) and float(v).is_integer() for v in value)
                
                if is_int_range:
                    params[key] = trial.suggest_int(key, int(value[0]), int(value[1]))
                elif all(isinstance(v, (int, float)) for v in value):
                    params[key] = trial.suggest_float(key, float(value[0]), float(value[1]))
            elif isinstance(value, list):
                params[key] = trial.suggest_categorical(key, value)
        
        logger.info(f"Trial {trial.number} generated params: {params}")
        try:
            train_payload = {
                "model_type": model_type,
                "dataset_id": dataset_id,
                "target_column": target_column,
                "hyperparameters": params,
                "metrics": [target_metric]
            }
            train_resp = requests.post(f"{TRAINER_URL}/train/job", json=train_payload)
            if train_resp.status_code != 200:
                logger.error(f"Failed to trigger trainer: {train_resp.text}")
                return 0.0
            
            trainer_job_id = train_resp.json().get("job_id")
            
            # 2. Wait for Trainer
            if not poll_trainer(trainer_job_id):
                return 0.0
            
            # 3. Trigger Evaluation
            eval_payload = {
                "experiment_id": f"hyperopt_{run_id}",
                "task_type": "classification" if any(x in model_type for x in ["Classifier", "SVC"]) else "regression",
                "model_ids": [trainer_job_id],
                "dataset_id": dataset_id,
                "target_column": target_column
            }
            eval_resp = requests.post(f"{EVALUATOR_URL}/evaluate", json=eval_payload)
            if eval_resp.status_code != 200:
                logger.error(f"Failed to trigger evaluator: {eval_resp.text}")
                return 0.0
            
            evaluator_job_id = eval_resp.json().get("job_ids", [None])[0]
            if not evaluator_job_id:
                return 0.0
            
            # 4. Wait for Evaluator
            if not poll_evaluator(evaluator_job_id):
                return 0.0
            
            # 5. Get Score
            result_resp = requests.get(f"{EVALUATOR_URL}/results/{evaluator_job_id}")
            if result_resp.status_code == 200:
                metrics = result_resp.json().get("metrics", {})
                score = metrics.get(target_metric, 0.0)
                return float(score)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error in objective trial: {e}")
            return 0.0

    return objective

def run_optimization_task(
    run_id: str,
    model: str,
    dataset_id: str,
    target_column: str,
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

        # Determine direction: minimize for error-based metrics, maximize for others
        direction = "minimize" if target_metric.lower() in ["rmse", "mae", "mse"] else "maximize"
        study = optuna.create_study(direction=direction)
        objective = create_objective(run_id, model, dataset_id, target_column, target_metric, search_space)

        def callback(study, trial):
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
