from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import uuid

class TrainingBatch(Base):
    __tablename__ = "training_batches"
    
    id = Column(String, primary_key=True)
    recommendation_id = Column(String)
    dataset_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    jobs = relationship("TrainingJob", back_populates="batch")

class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String, ForeignKey("training_batches.id"), nullable=True)
    batch = relationship("TrainingBatch", back_populates="jobs")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(String, default="queued") # queued, running, completed, failed
    model_type = Column(String)
    data_id = Column(String)
    hyperparameters = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
