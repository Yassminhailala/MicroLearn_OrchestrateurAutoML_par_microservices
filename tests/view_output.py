import pandas as pd
import io
from minio import Minio

# Configuration
MINIO_ENDPOINT = "localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_PROCESSED = "processed-data"
FILE_NAME = "cleaned_dataset.csv"

def view_results():
    print(f"Connecting to MinIO at {MINIO_ENDPOINT}...")
    client = Minio(
        MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )
    
    try:
        # Get the object
        print(f"Reading {FILE_NAME} from bucket {BUCKET_PROCESSED}...\n")
        response = client.get_object(BUCKET_PROCESSED, FILE_NAME)
        
        # Read content via pandas for nice formatting
        content = response.read()
        df = pd.read_csv(io.BytesIO(content))
        
        print("--- RESULTAT DU FICHIER : " + FILE_NAME + " ---")
        print(df.to_string()) # to_string() prints the whole dataframe
        print("---------------------------------------------")
        
        response.close()
        response.release_conn()
        
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier : {e}")
        print("Assurez-vous que le job est bien terminé et que le fichier existe.")

if __name__ == "__main__":
    view_results()
