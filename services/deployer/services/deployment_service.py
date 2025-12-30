import os
import subprocess
import logging
import shutil
from utils.minio_utils import download_model

logger = logging.getLogger(__name__)

MODELS_TEMP_DIR = "models_temp"

def deploy_rest(model_id, model_path):
    """Generates a TorchServe .mar file and placeholder for serving."""
    mar_name = f"{model_id}.mar"
    mar_path = os.path.join(MODELS_TEMP_DIR, mar_name)
    
    # In a real scenario, you'd have a specific handler.py
    # We create a dummy one if it doesn't exist
    handler_path = os.path.join(MODELS_TEMP_DIR, "handler.py")
    if not os.path.exists(handler_path):
        with open(handler_path, "w") as f:
            f.write("# Dummy TorchServe Handler\nimport logging\ndef handle(data, context):\n    return [{'prediction': 'success'}]")

    try:
        cmd = [
            "torch-model-archiver",
            "--model-name", model_id,
            "--version", "1.0",
            "--serialized-file", model_path,
            "--handler", handler_path,
            "--export-path", MODELS_TEMP_DIR,
            "-f"
        ]
        logger.info(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        # Move .mar file to model store
        model_store_dir = "/app/model_store"
        if not os.path.exists(model_store_dir):
            os.makedirs(model_store_dir, exist_ok=True)
            
        final_mar_path = os.path.join(model_store_dir, mar_name)
        shutil.move(mar_path, final_mar_path)
        
        # Register with TorchServe Management API
        import requests
        management_url = "http://localhost:8082/models"
        params = {
            "model_name": model_id,
            "url": mar_name,
            "initial_workers": 1,
            "synchronous": True
        }
        
        # Check if model already exists and delete if so (for updates)
        try:
            requests.delete(f"{management_url}/{model_id}")
        except:
            pass
            
        response = requests.post(management_url, params=params)
        if response.status_code >= 400:
             logger.error(f"Failed to register model: {response.text}")
             raise Exception(f"TorchServe registration failed: {response.text}")

        # The external URL uses the container name (or mapped localhost port)
        # Since we are returning a URL for a user potentially outside, we should return the ingress path.
        # Inside the network it is http://deployer:8081/predictions/{model_id}
        # To the user it might be http://localhost:8081/predictions/{model_id}
        
        return f"http://localhost:8081/predictions/{model_id}"
    except Exception as e:
        logger.error(f"TorchServe archiving/deploying failed: {e}")
        raise e

def deploy_batch(model_id, model_path):
    """Generates a batch inference script."""
    script_path = os.path.join(MODELS_TEMP_DIR, f"batch_inference_{model_id}.py")
    with open(script_path, "w") as f:
        f.write(f"""
import joblib
import pandas as pd
import sys

def run_inference(input_csv, output_csv):
    model = joblib.load('{os.path.basename(model_path)}')
    data = pd.read_csv(input_csv)
    preds = model.predict(data)
    pd.DataFrame(preds).to_csv(output_csv, index=False)
    print("Batch inference completed.")

if __name__ == "__main__":
    run_inference(sys.argv[1], sys.argv[2])
""")
    return script_path

def deploy_edge(model_id, model_path):
    """Generates a Dockerfile for edge deployment."""
    edge_dir = os.path.join(MODELS_TEMP_DIR, f"edge_{model_id}")
    os.makedirs(edge_dir, exist_ok=True)
    
    # Copy model to edge dir
    shutil.copy(model_path, edge_dir)
    
    dockerfile_content = f"""
FROM python:3.10-slim
WORKDIR /app
COPY {os.path.basename(model_path)} .
RUN pip install joblib scikit-learn pandas flask
COPY server.py .
EXPOSE 8080
CMD ["python", "server.py"]
"""
    with open(os.path.join(edge_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)
        
    # Also need a simple server.py for the edge container
    with open(os.path.join(edge_dir, "server.py"), "w") as f:
        f.write("""
from flask import Flask, request, jsonify
import joblib
import os
app = Flask(__name__)
model = joblib.load(os.listdir('.')[0]) # loads first file (the model)
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json['data']
    return jsonify({'prediction': model.predict([data]).tolist()})
app.run(host='0.0.0.0', port=8080)
""")
    return f"{edge_dir}/Dockerfile"

def process_deployment(model_id, deploy_type):
    # 1. Download
    model_path = download_model(model_id, MODELS_TEMP_DIR)
    
    # 2. Deploy based on type
    if deploy_type == "rest":
        return deploy_rest(model_id, model_path)
    elif deploy_type == "batch":
        return deploy_batch(model_id, model_path)
    elif deploy_type == "edge":
        return deploy_edge(model_id, model_path)
    else:
        raise ValueError(f"Invalid deployment type: {deploy_type}")
