import requests
import pandas as pd
import io
from minio import Minio
import time
import json

# Configuration for Host (outside Docker)
API_URL = "http://localhost:8001"
MINIO_ENDPOINT = "localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_RAW = "raw-data"
BUCKET_PROCESSED = "processed-data"

def setup_minio_and_upload_data():
    """Ensures buckets exist and uploads a dummy CSV."""
    client = Minio(
        MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )
    
    # Create buckets
    for bucket in [BUCKET_RAW, BUCKET_PROCESSED]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"Created bucket: {bucket}")

    # Create dummy data
    df = pd.DataFrame({
        "age": [25, 30, None, 40, 35],
        "salary": [50000, 60000, 55000, None, 65000],
        "city": ["Paris", "London", "Paris", "Berlin", "London"]
    })
    
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    data_stream = io.BytesIO(csv_bytes)
    
    client.put_object(
        BUCKET_RAW,
        "dataset.csv",
        data_stream,
        length=len(csv_bytes),
        content_type="application/csv"
    )
    print("Uploaded dummy 'dataset.csv' to 'raw-data'")
    return "dataset.csv"

def test_pipeline():
    # 1. Setup Data
    filename = setup_minio_and_upload_data()
    
    # 2. Define Pipeline Request
    payload = {
        "input_data": {
            "bucket": BUCKET_RAW,
            "path": filename
        },
        "pipeline": [
            {
                "operator": "fillna",
                "params": {"value": 0}
            },
            {
                "operator": "standard_scaler",
                "params": {}
            },
            {
                "operator": "one_hot",
                "params": {"columns": ["city"], "dtype": "int"}
            }
        ],
        "output_path": "cleaned_dataset.csv"
    }
    
    # 3. Call API
    print(f"\nSending request to {API_URL}/prepare ...")
    try:
        response = requests.post(f"{API_URL}/prepare", json=payload)
        response.raise_for_status()
        data = response.json()
        job_id = data["job_id"]
        print(f"Job started. ID: {job_id}")
    except Exception as e:
        print(f"Failed to call API: {e}")
        return

    # 4. Poll Status
    print("Polling status...")
    for _ in range(10):
        time.sleep(2)
        res = requests.get(f"{API_URL}/status/{job_id}")
        status_data = res.json()
        status = status_data["status"]
        print(f"Status: {status}")
        
        if status == "COMPLETED":
            print("\nSUCCESS! Job completed.")
            print(f"Output saved at: s3://{status_data['output_bucket']}/{status_data['output_path']}")
            return
        elif status == "FAILED":
            print(f"\nFAILURE! Job failed. Error: {status_data['error']}")
            return
            
    print("\nTimeout waiting for job completion.")

if __name__ == "__main__":
    test_pipeline()
