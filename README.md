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
📸 Captures d’écran:!


![capt18](https://github.com/user-attachments/assets/beeb78aa-3263-4165-b447-a3e623d6a28f)
![capt17](https://github.com/user-attachments/assets/a3f6418c-54b0-47bf-b982-c23187652470)
![Capt16](https://github.com/user-attachments/assets/2b67625e-8e70-47bb-b484-a2cddaeb516b)
![capt15](https://github.com/user-attachments/assets/bcf3772c-3a94-465d-bd1d-9e0a472d601a)
![capt14](https://github.com/user-attachments/assets/1fecb7dc-bcbc-4860-9efd-f4c4e5391f2c)
![capt13](https://github.com/user-attachments/assets/00ada7e8-aabf-402f-aff7-afe7e337fcf5)
![capt12](https://github.com/user-attachments/assets/1af13dc2-dcae-4234-a76d-36280104865c)
![capt11](https://github.com/user-attachments/assets/33e46430-dce0-48a7-b7c6-431302de0ebc)
![capt10](https://github.com/user-attachments/assets/6b5c3e18-9d20-4cdd-abac-dbbffebec6d2)
![capt9](https://github.com/user-attachments/assets/4be03679-62e9-4f6f-a657-c1f975dfa3f9)
![capt8](https://github.com/user-attachments/assets/7cf22a18-aad0-4373-99a8-1d7189e5e1d8)
![capt7](https://github.com/user-attachments/assets/ea202419-43a1-4842-99d2-0fe342882f39)
![capt6](https://github.com/user-attachments/assets/b2d1d8ef-dd4a-481f-826f-f26f562e3c80)
![capt5](https://github.com/user-attachments/assets/a4c199fb-6f03-4dc1-8a3b-2a5546c83862)
![capt4](https://github.com/user-attachments/assets/804b17d8-1c67-4cfc-b536-9b745ee109fe)
![capt3](https://github.com/user-attachments/assets/ffd8e833-5443-41ef-9d13-aa01f957232f)
![capt2](https://github.com/user-attachments/assets/dcc585c6-b893-4bb7-ae8c-ed8db494f0cf)
![capt1](https://github.com/user-attachments/assets/b0ff69fa-ac6f-443d-b961-0784e11f88cd)





