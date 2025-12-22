OrchestrateurAutoML - Architecture Microservices

OrchestrateurAutoML est une plateforme AutoML distribuée et modulaire, conçue pour automatiser l’intégralité du cycle de vie d’un modèle de machine learning, depuis la préparation des données jusqu’à l’évaluation finale.

🚀 Vue d’ensemble

Cette solution permet aux utilisateurs de transformer des données brutes en modèles performants avec un minimum d’intervention manuelle.
Grâce à une architecture microservices, chaque composant est indépendant, scalable et communique via des APIs REST.

🏗️ Architecture

Le système est composé de plusieurs microservices coordonnés :

Frontend (Streamlit) : Interface utilisateur intuitive pour le chargement des données, la configuration des entraînements et la visualisation des résultats.

Data Preparer : Nettoyage, prétraitement et extraction automatique des métadonnées des datasets.

Model Selector : Recommande les meilleurs modèles (XGBoost, RandomForest, CNN, etc.) en fonction des caractéristiques du dataset.

Trainer : Gère l’entraînement distribué des modèles avec PyTorch et Ray, avec support GPU.

HyperOpt : Service d’optimisation des hyperparamètres pour maximiser la performance des modèles.

Evaluator : Évaluation approfondie des performances et comparaison des modèles entraînés.

MLflow : Serveur de tracking pour le suivi des expériences et le versionnage des modèles.

MinIO : Stockage d’objets (S3-compatible) pour les datasets et artefacts de modèles.

🛠️ Stack Technique

Langage : Python 3.9+

Frameworks Web : FastAPI, Uvicorn

Machine Learning : PyTorch, Scikit-Learn, Ray, Pandas

Tracking & MLOps : MLflow

Base de données : PostgreSQL (instances dédiées par service)

Stockage & Cache : MinIO, Redis

Interface : Streamlit

Conteneurisation : Docker, Docker Compose

🔧 Installation et Lancement

Prérequis : Docker et Docker Compose installés sur votre machine.

Cloner le dépôt :

git clone <URL_DU_DEPOT>
cd OrchestrateurAutoML


Lancer les services :

docker-compose up --build


Accéder à l’interface Streamlit via le port configuré (ex. http://localhost:8501).
📸 Captures d’écran

Voici quelques captures illustrant l’interface et les fonctionnalités de l’application.

![capt18](https://github.com/user-attachments/assets/10b9e767-9836-4786-85dc-b120b0b560ff)
![capt17](https://github.com/user-attachments/assets/137193ba-f178-4a92-8c99-addf336a0f38)
![Capt16](https://github.com/user-attachments/assets/df8d5bf1-3434-4602-9369-bdbd51601019)
![capt15](https://github.com/user-attachments/assets/6b6f5baf-3c88-4c52-9d32-66e5ca7c1c0d)
![capt14](https://github.com/user-attachments/assets/4f95f282-4a54-4da3-8117-fa028c321f70)
![capt13](https://github.com/user-attachments/assets/d7be7f22-3050-4478-8aed-fe1645de6b26)
![capt12](https://github.com/user-attachments/assets/520aada6-a4b5-434b-9263-76ab020d5108)
![capt11](https://github.com/user-attachments/assets/767894eb-e476-4c3c-b4d1-b3aeec381c5d)
![capt10](https://github.com/user-attachments/assets/7153c791-842b-43a0-b6b8-cfc13bda4246)
![capt9](https://github.com/user-attachments/assets/96355b7f-51a4-4046-9cf2-e79100c66aa6)
![capt8](https://github.com/user-attachments/assets/013ddd09-c320-4617-93a3-e8175ae5f073)
![capt7](https://github.com/user-attachments/assets/b83865c6-3131-40ba-99c2-c219ea430a00)
![capt6](https://github.com/user-attachments/assets/240c69fd-25bd-44a9-ae53-6bf101a2627c)
![capt5](https://github.com/user-attachments/assets/c2987f08-6bd9-4601-a292-010e26eb9cb2)
![capt4](https://github.com/user-attachments/assets/c4fcf2a6-f239-4fa5-a43a-0b64c0594cfd)
![capt3](https://github.com/user-attachments/assets/908e49fa-6a7e-4f44-ae71-7ee424fe8270)
![capt2](https://github.com/user-attachments/assets/61a96a5a-73c2-4e93-83ab-841e7db9c567)
![capt1](https://github.com/user-attachments/assets/ebe67b77-b2e2-43a7-9677-1ac0d0378de2)
