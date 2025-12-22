from minio import Minio
import os
import pandas as pd
import io

class MinioClient:
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=False
        )
        self.bucket = "processed-data"

    def get_dataset(self, dataset_id: str) -> pd.DataFrame:
        object_name = f"processed_{dataset_id}.csv"
        try:
            response = self.client.get_object(self.bucket, object_name)
            return pd.read_csv(io.BytesIO(response.read()))
        except Exception as e:
            print(f"Error loading dataset {dataset_id}: {e}")
            raise e

minio_client = MinioClient()
