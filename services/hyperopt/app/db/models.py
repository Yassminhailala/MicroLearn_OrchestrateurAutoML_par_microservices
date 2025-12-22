from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, func
from .session import Base
import uuid

class HyperOptRun(Base):
    __tablename__ = "hyperopt_runs"

    run_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model = Column(String, index=True)
    target_metric = Column(String)
    search_space = Column(JSON)
    best_params = Column(JSON, nullable=True)
    best_score = Column(Float, nullable=True)
    trials_completed = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, running, completed, stopped, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

class HyperOptTrial(Base):
    __tablename__ = "hyperopt_trials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, index=True)
    trial_number = Column(Integer)
    params = Column(JSON)
    score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
