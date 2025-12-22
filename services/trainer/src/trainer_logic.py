import torch
import pytorch_lightning as L
from pytorch_lightning.loggers import MLFlowLogger
import ray
from ray import train, tune
from ray.train import ScalingConfig
from ray.train.torch import TorchTrainer
import os
import logging
from src.utils import update_job_status, save_checkpoint_to_minio, get_minio_client
from sklearn.svm import SVR, SVC
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import joblib
import numpy as np
import pandas as pd
import io

logger = logging.getLogger(__name__)

# --- Helper Functions ---

def load_dataset_from_minio(dataset_id):
    """Loads dataframe from MinIO processed-data bucket."""
    client = get_minio_client()
    bucket = "processed-data"
    object_name = f"processed_{dataset_id}.csv"
    
    try:
        response = client.get_object(bucket, object_name)
        df = pd.read_csv(io.BytesIO(response.read()))
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id} from MinIO: {e}")
        raise e

def calculate_metrics(y_true, y_pred, metrics_list, task_type="classification"):
    """Calculates requested metrics."""
    results = {}
    
    # Normalize inputs
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    for metric in metrics_list:
        m = metric.lower()
        try:
            if m == "accuracy":
                results["accuracy"] = float(accuracy_score(y_true, y_pred))
            elif m == "f1 score" or m == "f1":
                results["f1"] = float(f1_score(y_true, y_pred, average='weighted'))
            elif m == "precision":
                results["precision"] = float(precision_score(y_true, y_pred, average='weighted'))
            elif m == "recall":
                results["recall"] = float(recall_score(y_true, y_pred, average='weighted'))
            elif m == "rmse":
                results["rmse"] = float(np.sqrt(mean_squared_error(y_true, y_pred)))
            elif m == "mae":
                results["mae"] = float(mean_absolute_error(y_true, y_pred))
            elif m == "r2":
                results["r2"] = float(r2_score(y_true, y_pred))
        except Exception as e:
            logger.warning(f"Could not calculate metric {metric}: {e}")
            results[metric] = None
            
    return results

# --- PyTorch Lightning Model ---

class SimpleLightningModel(L.LightningModule):
    def __init__(self, config):
        super().__init__()
        self.save_hyperparameters()
        input_size = config.get("input_size", 10)
        output_size = config.get("output_size", 1)
        
        # Simple flexible architecture
        self.net = torch.nn.Sequential(
            torch.nn.Linear(input_size, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, output_size)
        )
        self.lr = config.get("lr", 0.01)
        self.task_type = config.get("task_type", "regression")

    def forward(self, x):
        return self.net(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        
        if self.task_type == "classification":
            # Assuming CrossEntropyLoss for multi-class or BCE for binary
            # For simplicity in this demo, output_size should match classes
            # Here we assume scalar regression or manual handling for classification
            # This is a basic placeholder tailored for regression mostly
            loss = torch.nn.functional.mse_loss(y_hat.squeeze(), y)
        else:
            loss = torch.nn.functional.mse_loss(y_hat.squeeze(), y)
            
        self.log("train_loss", loss)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.lr)

def train_func(config):
    # Data Loading inside Worker
    # Note: In distributed ray, passing large logic via config is okay, but dataset logic ideally 
    # should be handled cleanly. Here we re-load.
    try:
        df = load_dataset_from_minio(config["data_id"])
        target = config.get("target_column")
        if not target or target not in df.columns:
            raise ValueError(f"Target column {target} missing")
            
        X = df.drop(columns=[target]).values.astype(np.float32)
        y = df[target].values.astype(np.float32)
        
        # Simple TensorDataset
        dataset = torch.utils.data.TensorDataset(torch.from_numpy(X), torch.from_numpy(y))
        train_loader = torch.utils.data.DataLoader(dataset, batch_size=config.get("batch_size", 32))
        
        # Model
        config["input_size"] = X.shape[1]
        model = SimpleLightningModel(config)
        
        # MLflow
        mlflow_logger = MLFlowLogger(
            experiment_name=config.get("experiment_name", "automl_trainer"),
            tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        )
        
        trainer = L.Trainer(
            max_epochs=config.get("epochs", 5),
            logger=mlflow_logger,
            accelerator="auto" if torch.cuda.is_available() else "cpu",
            devices=1,
            enable_progress_bar=False
        )
        
        trainer.fit(model, train_loader)
        
        metrics = trainer.callback_metrics
        return {"loss": metrics.get("train_loss", 0.0).item(), "mlflow_run_id": mlflow_logger.run_id}
        
    except Exception as e:
        logger.error(f"Train func failed: {e}")
        return {"error": str(e)}


def train_sklearn(job_id, model_type, params):
    """
    Train Scikit-Learn models using REAL data.
    """
    logger.info(f"Starting Scikit-Learn training for {model_type} (Job {job_id})")
    
    # 1. Load Data
    data_id = params.get("data_id")
    target_col = params.get("target_column")
    metrics_req = params.get("metrics", ["accuracy"]) # default
    
    if not data_id or not target_col:
        raise ValueError("Missing data_id or target_column")

    df = load_dataset_from_minio(data_id)
    
    if target_col not in df.columns:
        raise ValueError(f"Target column {target_col} not found in dataset")

    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Handle Categorical Target for Classification
    is_classification = "Classifier" in model_type or "SVC" in model_type
    if is_classification:
        if y.dtype == 'object' or y.dtype.name == 'category':
            le = LabelEncoder()
            y = le.fit_transform(y)
    
    # Handle Categorical Features in X
    # Identify object/category columns
    cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_cols:
        logger.info(f"Auto-encoding categorical features: {cat_cols}")
        # Use simple One-Hot Encoding via pandas
        X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
        # Ensure boolean columns (created by get_dummies) are converted to int/float
        X = X.astype(float)

    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # SAFETY: Fill any remaining NaN values (prevents sklearn crashes)
    if X_train.isnull().any().any():
        logger.warning("NaN values detected, filling with mean/0")
        X_train = X_train.fillna(X_train.mean()).fillna(0)
        X_test = X_test.fillna(X_train.mean()).fillna(0)
    
    # Filter params for model init to avoid passing data_id etc.
    internal_keys = ["model_type", "data_id", "experiment_name", "epochs", "gpu_resource", "target_column", "metrics"]
    model_params = {k:v for k,v in params.items() if k not in internal_keys}

    # 2. Select Model
    model = None
    if "SVM" in model_type:
        if is_classification:
            model = SVC(**model_params)
        else:
            model = SVR(**model_params)
            
    elif "RandomForest" in model_type:
        if is_classification:
            model = RandomForestClassifier(**model_params)
        else:
            model = RandomForestRegressor(**model_params)
            
    elif "XGBoost" in model_type:
        if is_classification:
            model = xgb.XGBClassifier(**model_params)
        else:
            model = xgb.XGBRegressor(**model_params)
            
    else:
        raise ValueError(f"Unsupported sklearn model type: {model_type}")
        
    # 3. Fit
    model.fit(X_train, y_train)
    
    # 4. Evaluate
    y_pred = model.predict(X_test)
    
    # Calculate requested metrics
    eval_metrics = calculate_metrics(y_test, y_pred, metrics_req)
    
    # Add simple loss measure if not present and applicable
    # (Optional, keeping it simple to user request)
    
    # 5. Save Model
    filename = f"model_{job_id}.joblib"
    joblib.dump(model, filename)
    save_checkpoint_to_minio(job_id, filename)
    
    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)
        
    # Merge status
    result = {"status": "success"}
    result.update(eval_metrics)
    
    return result

def start_training(job_id, model_type, data_id, hyperparameters):
    try:
        update_job_status(job_id, "running")
        
        # Inject data_id if not in params (it passed as arg)
        hyperparameters["data_id"] = data_id
        
        # Clean params for sklearn (remove wrapper-specific keys)
        # We need to Keep 'target_column', 'metrics', 'data_id' for logic inside
        # But REMOVE them before passing to **params of the model constructor
        
        internal_keys = ["model_type", "data_id", "experiment_name", "epochs", "gpu_resource", "target_column", "metrics"]
        model_params = {k:v for k,v in hyperparameters.items() if k not in internal_keys}
        
        # Handle RF param string -> int conversion just in case
        if "n_estimators" in model_params:
             try: model_params["n_estimators"] = int(model_params["n_estimators"])
             except: pass

        # Pass FULL hyperparameters to train_sklearn so it can extract target/data_id
        # BUT pass filtered model_params to the dispatcher inside? 
        # Actually simplest is to modify train_sklearn to take full dict and filter there OR 
        # Refactor train_sklearn to take (job_id, model_type, full_config, model_params)
        # Let's clean up:
        
        # Dispatch
        if any(x in model_type for x in ["SVM", "RandomForest", "XGBoost"]):
             # We pass filtered params as the 4th arg if we change signature, 
             # OR we pass full params and let train_sklearn separate them?
             # Let's pass filtered 'model_params' for the model, and 'hyperparameters' for context?
             # My implementation of train_sklearn above expects 'params' to contain data_id/target.
             # So I should pass 'hyperparameters' to train_sklearn, and inside train_sklearn I filter again before `model(**params)`.
             
             # Re-refactor train_sklearn to be safe:
             # It uses params.get("data_id")...
             # And then `SVC(**params)`. THIS IS BUGGY if params still has data_id.
             
             # Let's fix this in the code I'm writing:
             # See below in ReplacementContent where I implement train_sklearn properly.
             
             # Calling structure:
             result = train_sklearn(job_id, model_type, hyperparameters)
             update_job_status(job_id, "completed", result=result)
             logger.info(f"Job {job_id} (Sklearn) completed successfully")
             
        else:
            # Deep Learning / Torch Logic
            if not ray.is_initialized():
                ray.init(ignore_reinit_error=True)
                
            config = {
                "model_type": model_type,
                "data_id": data_id,
                "epochs": 10,
                "experiment_name": f"job_{job_id}"
            }
            if hyperparameters:
                config.update(hyperparameters)
                
            use_gpu = torch.cuda.is_available()
            resources_per_worker = {"GPU": 0.5} if use_gpu else {"CPU": 1}
            
            trainer = TorchTrainer(
                train_func,
                train_loop_config=config,
                scaling_config=ScalingConfig(
                    num_workers=1, 
                    use_gpu=use_gpu,
                    resources_per_worker=resources_per_worker
                )
            )
            
            result = trainer.fit()
            
            checkpoint_path = f"checkpoints/{job_id}/model.ckpt"
            save_checkpoint_to_minio(job_id, checkpoint_path)
            
            update_job_status(job_id, "completed", result=result.metrics)
            logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        update_job_status(job_id, "failed", error=str(e))
