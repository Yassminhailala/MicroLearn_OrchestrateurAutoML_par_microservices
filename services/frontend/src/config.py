import os

# Configuration
API_URL = os.getenv("API_URL", "http://data_preparer:8000")
MODEL_SELECTOR_URL = os.getenv("MODEL_SELECTOR_URL", "http://model_selector:8000")
TRAINER_API_URL = os.getenv("TRAINER_API_URL", "http://trainer:8000")
EVALUATOR_API_URL = os.getenv("EVALUATOR_API_URL", "http://evaluator:8000")
HYPEROPT_API_URL = os.getenv("HYPEROPT_API_URL", "http://hyperopt:8000")

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_RAW = "raw-data"
MINIO_BUCKET_PROCESSED = "processed-data"
