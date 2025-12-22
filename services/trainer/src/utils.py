import os
from minio import Minio
import logging
from .database import SessionLocal
from .models import TrainingJob
import json

logger = logging.getLogger(__name__)

def update_job_status(job_id, status, result=None, error=None):
    db = SessionLocal()
    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if job:
            job.status = status
            if result:
                job.result = result
            if error:
                job.error = error
            db.commit()
            db.refresh(job)
        else:
            # Create if not exists (though usually created at start)
            job = TrainingJob(id=job_id, status=status, result=result, error=error)
            db.add(job)
            db.commit()
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        db.rollback()
    finally:
        db.close()

def get_job_status(job_id):
    db = SessionLocal()
    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if job:
            return {
                "id": job.id,
                "status": job.status,
                "error": job.error,
                "created_at": str(job.created_at)
            }
        return None
    finally:
        db.close()

def get_job_result(job_id):
    db = SessionLocal()
    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if job and job.status == "completed":
            return job.result
        return None
    finally:
        db.close()

def get_minio_client():
    return Minio(
        os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        secure=False
    )

def save_checkpoint_to_minio(job_id, file_path_or_buffer):
    """
    Uploads a model file or memory buffer to MinIO bucket 'checkpoints'.
    """
    client = get_minio_client()
    bucket = "checkpoints"
    
    # Ensure bucket exists
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        
    object_name = f"{job_id}/{os.path.basename(file_path_or_buffer)}" if isinstance(file_path_or_buffer, str) else f"{job_id}/model.joblib"
    
    try:
        if isinstance(file_path_or_buffer, str):
            # It's a file path
            client.fput_object(bucket, object_name, file_path_or_buffer)
        else:
            # It's a bytes buffer (e.g. for Torch models in memory)
            client.put_object(bucket, object_name, file_path_or_buffer, len(file_path_or_buffer.getbuffer()))
            
        logger.info(f"Successfully uploaded checkpoint to MinIO: {bucket}/{object_name}")
    except Exception as e:
        logger.error(f"Failed to upload checkpoint to MinIO: {e}")
        raise e
