🤖 Distributed AutoML Platform
_____________________________________________________________________________________________________________________________________________________________________________________________________________
A powerful, modular, and distributed AutoML platform built on a microservices architecture.
This platform enables users to upload datasets, receive AI-driven model recommendations, perform automated hyperparameter optimization, and deploy models as production-ready REST APIs.
The system is designed with scalability, reproducibility, and MLOps best practices in mind.
_____________________________________________________________________________________________________________________________________________________________________________________________________________
🛠️ Technology Stack
Core Technologies

Backend: Python (Flask, PyTorch, Scikit-learn, Ray)

Frontend: Streamlit

Infrastructure & MLOps

Object Storage: MinIO (S3-Compatible)

Experiment Tracking: MLflow

Database: PostgreSQL (one isolated instance per service)

Message Broker: NATS

Cache / Task Queue: Redis

DevOps

Containerization: Docker, Docker Compose
_____________________________________________________________________________________________________________________________________________________________________________________________________________
Prerequisites

Docker & Docker Compose
8 GB RAM (minimum)
16 GB RAM (recommended)
Installation
Clone the repository:
git clone MicroLearn_OrchestrateurAutoML_par_microservices
cd distributed-automl-platform
Launch all services:
docker-compose up -d --build

Access the frontend:
http://localhost:8501
_____________________________________________________________________________________________________________________________________________________________________________________________________________

🔄 Automated Workflow
The platform provides a fully automated data and model flow — no manual ID copying between steps.

📊 Data Preparation
Upload a CSV dataset.
A unique Dataset ID is generated and automatically propagated across services.

🤖 Model Selection
Select the target column.
The system recommends the most suitable models and launches a batch training job.

🚀 Training Monitor
Track training jobs in real time.
Model artifacts are stored in MinIO and logged in MLflow.

📈 Model Evaluation
Compare trained models through interactive charts and metrics.
Selecting a model prepares it for deployment.

🧪 Hyperparameter Optimization
Fine-tune the selected model using advanced optimization strategies.

📦 Model Deployment
Deploy the best model in one click as a TorchServe REST API.
_____________________________________________________________________________________________________________________________________________________________________________________________________________
🏗️ Architecture Overview!

[architecture microservices ](https://github.com/user-attachments/assets/158e03d1-baae-40a1-a669-2f25a7cee999)
_____________________________________________________________________________________________________________________________________________________________________________________________________________

Video de simulation :
https://youtu.be/SE2k13j0OL8?si=JzJVKHaA2Ls_DdfA

_____________________________________________________________________________________________________________________________________________________________________________________________________________

