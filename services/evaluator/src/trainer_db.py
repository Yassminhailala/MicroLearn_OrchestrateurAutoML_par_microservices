"""
Connection to Trainer DB to fetch model metadata.
"""
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Trainer DB Connection
TRAINER_POSTGRES_USER = os.getenv("TRAINER_POSTGRES_USER", "user")
TRAINER_POSTGRES_PASSWORD = os.getenv("TRAINER_POSTGRES_PASSWORD", "password")
TRAINER_POSTGRES_HOST = os.getenv("TRAINER_POSTGRES_HOST", "trainer_db")
TRAINER_POSTGRES_DB = os.getenv("TRAINER_POSTGRES_DB", "trainer")

TRAINER_DB_URL = f"postgresql://{TRAINER_POSTGRES_USER}:{TRAINER_POSTGRES_PASSWORD}@{TRAINER_POSTGRES_HOST}/{TRAINER_POSTGRES_DB}"

trainer_engine = create_engine(TRAINER_DB_URL)
TrainerSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=trainer_engine)
TrainerBase = declarative_base()

def get_trainer_db():
    db = TrainerSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Read-only model for Trainer's training_jobs table
class TrainingJob(TrainerBase):
    __tablename__ = "training_jobs"
    
    id = Column(String, primary_key=True)
    model_type = Column(String)
    dataset_id = Column(String)
    status = Column(String)
    hyperparameters = Column(JSON)
    created_at = Column(DateTime)
