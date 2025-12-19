from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
import traceback

from .schemas import PreparationRequest, PreparationResponse
from .database import engine, Base, get_db
from .models import PreparedDataset
from .processing import processor
from .minio_client import minio_client
from .config import settings

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Data Preparer Service")

def process_data_task(job_id: str, request: PreparationRequest, db_session_factory):
    """
    Background task to process data.
    """
    db = db_session_factory()
    dataset_record = db.query(PreparedDataset).filter(PreparedDataset.job_id == job_id).first()
    
    try:
        dataset_record.status = "PROCESSING"
        db.commit()

        # 1. Load Data
        print(f"Loading data from {request.input_data.bucket}/{request.input_data.path}")
        df = minio_client.load_dataframe(request.input_data.bucket, request.input_data.path)
        
        # 2. Process Data
        # Ensure we convert Pydantic models to dicts if needed, depending on how processing.py expects them
        # processing.py expects List[PipelineStep] which is what request.pipeline is.
        df_clean = processor.process(df, request.pipeline)
        
        # 3. Save Data
        output_filename = f"processed_{job_id}.csv"
        output_path = request.output_path or output_filename
        output_bucket = settings.MINIO_BUCKET_PROCESSED
        
        s3_path = minio_client.save_dataframe(df_clean, output_bucket, output_path)
        
        # 4. Update DB
        dataset_record.status = "COMPLETED"
        dataset_record.output_bucket = output_bucket
        dataset_record.output_path = output_path
        db.commit()
        print(f"Job {job_id} completed successfully.")

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        traceback.print_exc()
        dataset_record.status = "FAILED"
        dataset_record.error_message = str(e)
        db.commit()
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/prepare", response_model=PreparationResponse)
def prepare_data(request: PreparationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Main endpoint to trigger data preparation.
    """
    job_id = str(uuid.uuid4())
    
    # Create DB Record
    new_dataset = PreparedDataset(
        job_id=job_id,
        input_bucket=request.input_data.bucket,
        input_path=request.input_data.path,
        pipeline_config=[step.model_dump() for step in request.pipeline], # Store detailed config
        status="PENDING"
    )
    db.add(new_dataset)
    db.commit()
    
    # Launch Background Task
    # We pass SessionLocal class or a method to create a new session because `db` dependency is closed after request
    from .database import SessionLocal
    background_tasks.add_task(process_data_task, job_id, request, SessionLocal)
    
    return {
        "job_id": job_id,
        "status": "PENDING",
        "output_location": None
    }

@app.get("/status/{job_id}")
def get_status(job_id: str, db: Session = Depends(get_db)):
    record = db.query(PreparedDataset).filter(PreparedDataset.job_id == job_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": record.job_id,
        "status": record.status,
        "output_bucket": record.output_bucket,
        "output_path": record.output_path,
        "error": record.error_message
    }
