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

1. Frontend / Dashboard!
[capt1](https://github.com/user-attachments/assets/48419ddd-884e-4419-9f7b-56eb97dd5bff)
 2. Data Preparer
 ![capt7](https://github.com/user-attachments/assets/b8a0a137-7a98-4e30-858f-3ac58df43a34)
![capt5](https://github.com/user-attachments/assets/a64938c5-746a-490c-870d-75131443bf77)
![capt4](https://github.com/user-attachments/assets/033d5441-44da-439f-8ee7-c9ec5282db13)
![capt3](https://github.com/user-attachments/assets/1029c898-ff98-4d57-8464-f6c918e71513)
![capt2](https://github.com/user-attachments/assets/6a48dc5d-f906-4f4d-8214-f6c316fd8a67)


