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
