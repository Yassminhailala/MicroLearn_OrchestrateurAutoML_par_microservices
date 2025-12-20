from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from .database import Base
import uuid

class ModelSelectionLog(Base):
    __tablename__ = "model_selection_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    dataset_name = Column(String, index=True)
    task_type = Column(String) # classification, regression, etc.
    dataset_size = Column(String) # small, medium, large
    shape_rows = Column(Integer)
    shape_cols = Column(Integer)
    selected_models = Column(String) # JSON or Comma-separated list of models proposed
    justification = Column(String)
