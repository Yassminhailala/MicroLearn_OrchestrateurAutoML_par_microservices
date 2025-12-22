from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from src.database import Base
import uuid

class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"

    id = Column(String, primary_key=True, index=True)
    experiment_id = Column(String, index=True)  # NEW: Group evaluations
    model_id = Column(String, index=True)
    model_name = Column(String, nullable=True)  # NEW: For reporting
    dataset_id = Column(String, index=True)
    task_type = Column(String, nullable=True)  # NEW: classification/regression
    status = Column(String, default="pending") # pending, running, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    error = Column(Text, nullable=True)
    
    # Results snapshot
    metrics = Column(JSON, nullable=True) # { "accuracy": 0.9, "f1": 0.85 ... }
    artifacts = Column(JSON, nullable=True) # { "roc_curve": "s3://...", "confusion_matrix": "s3://..." }

class ModelResults(Base):
    """
    Persistent record of a model's performance, separates job memory from long-term stats.
    """
    __tablename__ = "model_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String, index=True)  # NEW: For comparative queries
    model_id = Column(String, index=True)
    model_name = Column(String, nullable=True)  # NEW: For reporting
    dataset_id = Column(String)
    evaluation_job_id = Column(String, ForeignKey("evaluation_jobs.id"))
    
    # Store key metrics as columns for easier SQL querying/aggregation later
    accuracy = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    auc = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)  # NEW
    r2 = Column(Float, nullable=True)   # NEW
    
    # Full dump
    all_metrics = Column(JSON)
