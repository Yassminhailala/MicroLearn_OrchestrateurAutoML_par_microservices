from minio import Minio
from .config import settings
import io
import pandas as pd
import os

class MinioClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        for bucket in [settings.MINIO_BUCKET_RAW, settings.MINIO_BUCKET_PROCESSED]:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    def load_dataframe(self, bucket: str, path: str) -> pd.DataFrame:
        response = self.client.get_object(bucket, path)
        try:
            # Assuming CSV for now, extendable to content-type checks
            return pd.read_csv(io.BytesIO(response.read()))
        finally:
            response.close()
            
    def save_dataframe(self, df: pd.DataFrame, bucket: str, path: str):
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        data_stream = io.BytesIO(csv_bytes)
        
        self.client.put_object(
            bucket,
            path,
            data_stream,
            length=len(csv_bytes),
            content_type="application/csv"
        )
        return f"s3://{bucket}/{path}"

minio_client = MinioClient()
