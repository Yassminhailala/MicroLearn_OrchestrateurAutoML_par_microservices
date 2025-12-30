 Distributed AutoML Platform
_____________________________________________________________________________________________________________________________________________________________________________________________________________
A powerful, modular, and distributed AutoML platform built on a microservices architecture.
This platform enables users to upload datasets, receive AI-driven model recommendations, perform automated hyperparameter optimization, and deploy models as production-ready REST APIs.
The system is designed with scalability, reproducibility, and MLOps best practices in mind.
_____________________________________________________________________________________________________________________________________________________________________________________________________________

About MicroLearn

MicroLearn is a modular and scalable AutoML platform built on microservices. It simplifies ML workflows by enabling parallel model training, hyperparameter optimization, and reproducible experiments with real-time dashboards.
_____________________________________________________________________________________________________________________________________________________________________________________________________________
Why This Project Exists

Most AutoML tools are either:

-Monolithic and hard to scale

-Opaque (no control over training decisions)

-Research-only, not production-ready

This project was built to answer a different question:

How would you design AutoML as a real production system, not a notebook?

The result is a microservices-based AutoML platform focused on:

-Scalability

-Observability

-Reproducibility
_____________________________________________________________________________________________________________________________________________________________________________________________________________

 Technology Stack
Core Technologies

-Backend: Python (Flask, PyTorch, Scikit-learn, Ray)

-Frontend: Streamlit

-Infrastructure & MLOps

-Object Storage: MinIO (S3-Compatible)

-Experiment Tracking: MLflow

-Database: PostgreSQL (one isolated instance per service)

-Message Broker: NATS

-Cache / Task Queue: Redis

-DevOps

-Containerization: Docker, Docker Compose
_____________________________________________________________________________________________________________________________________________________________________________________________________________
Prerequisites

-Docker & Docker Compose

-8 GB RAM (minimum)

-16 GB RAM (recommended)

Installation
Clone the repository:

git clone MicroLearn_OrchestrateurAutoML_par_microservices

cd distributed-automl-platform

Launch all services:
docker-compose up -d --build

Access the frontend:
http://localhost:8501
_____________________________________________________________________________________________________________________________________________________________________________________________________________

 Project Structure:


<img width="654" height="316" alt="image" src="https://github.com/user-attachments/assets/5f63da75-c426-491a-81b8-6c5933e1b574" />

________________________________________________________________________________________________________________________________________________________________________________________

 Automated Workflow
The platform provides a fully automated data and model flow — no manual ID copying between steps.

 Data Preparation
Upload a CSV dataset.
A unique Dataset ID is generated and automatically propagated across services.

 Model Selection
Select the target column.
The system recommends the most suitable models and launches a batch training job.

 Training Monitor
Track training jobs in real time.
Model artifacts are stored in MinIO and logged in MLflow.

 Model Evaluation
Compare trained models through interactive charts and metrics.
Selecting a model prepares it for deployment.

 Hyperparameter Optimization
Fine-tune the selected model using advanced optimization strategies.

 Model Deployment
Deploy the best model in one click as a TorchServe REST API.
_____________________________________________________________________________________________________________________________________________________________________________________________________________
 Architecture Overview!

<img width="764" height="444" alt="Arch1" src="https://github.com/user-attachments/assets/8ab13945-345a-4297-b7cc-c20f34ca990e" />


_____________________________________________________________________________________________________________________________________________________________________________________________________________
Diagramme BPMN :

<img width="1553" height="824" alt="image" src="https://github.com/user-attachments/assets/d90c51af-0708-431f-bf67-65b70e9d0b21" />

_____________________________________________________________________________________________________________________________________________________________________________________________________________

 Future Improvements

- Real-time notifications for training jobs
- Integration with cloud services (AWS, GCP)

_____________________________________________________________________________________________________________________________________________________________________________________________________________


Video de simulation :
https://youtu.be/SE2k13j0OL8?si=JzJVKHaA2Ls_DdfA

_____________________________________________________________________________________________________________________________________________________________________________________________________________

