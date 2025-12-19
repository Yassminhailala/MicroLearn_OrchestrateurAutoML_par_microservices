from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base

class PreparedDataset(Base):
    __tablename__ = "prepared_datasets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    input_bucket = Column(String)
    input_path = Column(String)
    output_bucket = Column(String)
    output_path = Column(String)
    pipeline_config = Column(JSON)
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
