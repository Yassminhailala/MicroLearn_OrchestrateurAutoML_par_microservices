import os
import boto3
from botocore.client import Config
import logging

logger = logging.getLogger(__name__)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "checkpoints"

def get_minio_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )

def download_model(model_id, dest_path):
    client = get_minio_client()
    # Check if a .joblib or .pt exists
    # For simplicity, we search in checkpoints/{model_id}/
    prefix = f"{model_id}/"
    try:
        response = client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        if "Contents" not in response:
            raise ValueError(f"No model found for model_id {model_id}")
        
        # Download the first file found (usually the model)
        obj_key = response["Contents"][0]["Key"]
        filename = os.path.basename(obj_key)
        full_dest = os.path.join(dest_path, filename)
        
        logger.info(f"Downloading {obj_key} to {full_dest}")
        client.download_file(BUCKET_NAME, obj_key, full_dest)
        return full_dest
    except Exception as e:
        logger.error(f"Failed to download model {model_id}: {e}")
        raise e
