import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, mean_squared_error, mean_absolute_error, r2_score, roc_curve, auc, confusion_matrix
from minio import Minio
import io
import os
import joblib
import json
import logging
from sqlalchemy.orm import Session
from src.models import EvaluationJob, ModelResults

# Config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_PROCESSED = "processed-data"
BUCKET_MODELS = "models" # User didn't specify, assuming models are here or we need to find them. 
# Notes: Trainer saves to 'checkpoints/{job_id}/model.ckpt' (Torch) or 'models/{job_id}/model.joblib' (Sklearn)?
# Trainer logic says: save_checkpoint_to_minio(job_id, filename) -> bucket "checkpoints"?
# Let's verify Trainer logic reuse if possible, or assume a bucket.
# Trainer Utils says: bucket_name="checkpoints" for save_checkpoint_to_minio.
BUCKET_CHECKPOINTS = "checkpoints"
BUCKET_ARTIFACTS = "evaluation-artifacts"

logger = logging.getLogger(__name__)

def get_minio_client():
    return Minio(
        MINIO_ENDPOINT.replace("http://", ""),
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

def load_data(dataset_id):
    """Loads feature dataframe."""
    if not dataset_id:
        raise ValueError("dataset_id is missing. Trainer did not return data_id.")
        
    client = get_minio_client()
    obj_name = f"processed_{dataset_id}.csv"
    try:
        response = client.get_object(BUCKET_PROCESSED, obj_name)
        return pd.read_csv(io.BytesIO(response.read()))
    except Exception as e:
        logger.error(f"Failed to load data {dataset_id}: {e}")
        raise e

def load_model(job_id):
    """Loads trained model from MinIO."""
    client = get_minio_client()
    
    # Trainer saves as: checkpoints/{job_id}/model_{job_id}.joblib
    # Or for Torch: checkpoints/{job_id}/model.ckpt
    
    # Try sklearn path first
    sklearn_path = f"{job_id}/model_{job_id}.joblib"
    try:
        client.fget_object(BUCKET_CHECKPOINTS, sklearn_path, "temp_model.joblib")
        model = joblib.load("temp_model.joblib")
        os.remove("temp_model.joblib")
        logger.info(f"Loaded sklearn model for job {job_id}")
        return model
    except Exception as e:
        logger.warning(f"Failed to load sklearn model at {sklearn_path}: {e}. Trying generic path...")
        
    # Try generic/torch path
    generic_path = f"{job_id}/model.joblib" # fallback
    try:
        client.fget_object(BUCKET_CHECKPOINTS, generic_path, "temp_model.joblib")
        model = joblib.load("temp_model.joblib")
        os.remove("temp_model.joblib")
        return model
    except Exception as e:
        logger.error(f"Failed to load model {job_id} from all known paths: {e}")
        raise e

def save_plot(fig, model_id, plot_name):
    """Saves plotly figure as HTML to MinIO."""
    client = get_minio_client()
    if not client.bucket_exists(BUCKET_ARTIFACTS):
        client.make_bucket(BUCKET_ARTIFACTS)
        
    html_content = fig.to_html(full_html=False, include_plotlyjs='cdn')
    html_bytes = io.BytesIO(html_content.encode('utf-8'))
    
    path = f"{model_id}/{plot_name}.html"
    client.put_object(
        BUCKET_ARTIFACTS, path, html_bytes, len(html_content), content_type="text/html"
    )
    return path # Return minio path

from src.database import SessionLocal

def run_evaluation(job_id: str, experiment_id: str, model_id: str, model_name: str, dataset_id: str, target_col: str, task_type: str):
    logger.info(f"--- Starting background evaluation for job {job_id} ---")
    logger.info(f"Context: experiment={experiment_id}, model={model_id}, dataset={dataset_id}, target={target_col}")
    db = SessionLocal()
    try:
        # Update status
        job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database!")
            return
            
        job.status = "running"
        db.commit()
        logger.info(f"Job {job_id} status updated to running")

        # 1. Load Resources
        logger.info(f"Loading data for dataset_id: {dataset_id}")
        df = load_data(dataset_id)
        logger.info(f"Data loaded successfully. Shape: {df.shape}")
        
        logger.info(f"Loading model for model_id: {model_id}")
        model = load_model(model_id)
        logger.info(f"Model loaded successfully.")
        
        if target_col not in df.columns:
            logger.error(f"Target {target_col} not found in dataset columns: {df.columns.tolist()}")
            raise ValueError(f"Target {target_col} not found in dataset")
            
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        # 1.5 Handle Categorical Features (Same logic as Trainer to avoid mismatches)
        # Ideally this preprocessing pipeline is saved with the model, but for this demo replicating logic:
        cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
        if cat_cols:
            X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
            X = X.astype(float)
            
        # Ensure columns match model expectation (simple intersection for safety)
        # Ideally we use the columns saved in model metadata.
        # For sklearn models, if feature count mismatch -> crash.
        # We assume X columns are identical to training time (same dataset ID).

        # 2. Predict
        y_pred = model.predict(X)
        try:
            y_prob = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None
        except:
            y_prob = None

        # 3. Calculate Metrics & Plots
        metrics = {}
        artifacts = {}
        
        if task_type == "classification":
            # Handle Categorical Target for Evaluation
            if y.dtype == 'object' or y.dtype.name == 'category':
                from sklearn.preprocessing import LabelEncoder
                le = LabelEncoder()
                y = le.fit_transform(y)
                
            metrics["accuracy"] = float(accuracy_score(y, y_pred))
            metrics["f1"] = float(f1_score(y, y_pred, average='weighted'))
            metrics["precision"] = float(precision_score(y, y_pred, average='weighted'))
            metrics["recall"] = float(recall_score(y, y_pred, average='weighted'))
            
            # Confusion Matrix Plot
            cm = confusion_matrix(y, y_pred)
            fig_cm = px.imshow(cm, text_auto=True, title="Confusion Matrix")
            artifacts["confusion_matrix"] = save_plot(fig_cm, model_id, "confusion_matrix")
            
            # ROC Curve (if binary)
            if y_prob is not None and len(np.unique(y)) == 2:
                fpr, tpr, _ = roc_curve(y, y_prob)
                fig_roc = px.area(
                    x=fpr, y=tpr,
                    title=f'ROC Curve (AUC={auc(fpr, tpr):.4f})',
                    labels=dict(x='False Positive Rate', y='True Positive Rate'),
                    width=700, height=500
                )
                fig_roc.add_shape(
                    type='line', line=dict(dash='dash'),
                    x0=0, x1=1, y0=0, y1=1
                )
                artifacts["roc_curve"] = save_plot(fig_roc, model_id, "roc_curve")
                metrics["auc"] = float(auc(fpr, tpr))

        else: # Regression
            metrics["rmse"] = float(np.sqrt(mean_squared_error(y, y_pred)))
            metrics["mae"] = float(mean_absolute_error(y, y_pred))
            metrics["r2"] = float(r2_score(y, y_pred))
            
            # Residual Plot
            residuals = y - y_pred
            fig_res = px.scatter(
                x=y_pred, y=residuals,
                title="Residuals vs Predicted",
                labels={'x': 'Predicted', 'y': 'Residuals'}
            )
            fig_res.add_hline(y=0, line_dash="dash", line_color="red")
            artifacts["residuals_plot"] = save_plot(fig_res, model_id, "residuals_plot")
            
            # Pred vs Actual
            fig_pva = px.scatter(
                x=y, y=y_pred,
                title="Actual vs Predicted",
                labels={'x': 'Actual', 'y': 'Predicted'}
            )
            fig_pva.add_shape(
                type="line", line=dict(dash='dash', color='red'),
                x0=y.min(), x1=y.max(), y0=y.min(), y1=y.max()
            )
            artifacts["prediction_plot"] = save_plot(fig_pva, model_id, "prediction_plot")

        # 4. Save Results
        job.status = "completed"
        job.metrics = metrics
        job.artifacts = artifacts
        
        # Save to persistent history as well
        history = ModelResults(
            experiment_id=experiment_id,
            model_id=model_id,
            model_name=model_name,
            dataset_id=dataset_id,
            evaluation_job_id=job_id,
            accuracy=metrics.get("accuracy"),
            f1_score=metrics.get("f1"),
            rmse=metrics.get("rmse"),
            auc=metrics.get("auc"),
            mae=metrics.get("mae"),
            r2=metrics.get("r2"),
            all_metrics=metrics
        )
        db.add(history)
        db.commit()
        
        logger.info(f"Evaluation {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"Evaluation {job_id} failed: {e}")
        job.status = "failed"
        job.error = str(e)
        db.commit()
    finally:
        db.close()
