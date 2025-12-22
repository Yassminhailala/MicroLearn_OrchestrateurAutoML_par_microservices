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
📸 Captures d’écran:![capt18](https://github.com/user-attachments/assets/54386a8c-5d1e-4890-8b8c-0ff1e1e12ef6)
![capt17](https://github.com/user-attachments/assets/a91148a7-7367-4bef-aad0-50d9a779c31f)
![Capt16](https://github.com/user-attachments/assets/f1b5a90c-44a7-44c1-a04c-1d66939077e2)
![capt15](https://github.com/user-attachments/assets/c7711502-01dd-4a3a-a47e-3d3ed3e858f1)
![capt14](https://github.com/user-attachments/assets/167057bf-4b82-4e47-af88-1fb7a6db1c74)
![capt13](https://github.com/user-attachments/assets/832065fe-aa3b-481f-b599-dc00e9e79576)
![capt12](https://github.com/user-attachments/assets/42c5f7ff-4b4d-4e9d-958b-1f26045ac548)
![capt11](https://github.com/user-attachments/assets/f4cbfd76-104d-410c-bb79-9e469c2359ef)
![capt10](https://github.com/user-attachments/assets/028aa936-bfe2-4910-96a7-bd344a5333a7)
![capt9](https://github.com/user-attachments/assets/04982c7c-87b6-456c-ad34-80a744a16ef6)
![capt8](https://github.com/user-attachments/assets/1ffd1f1c-70fc-409a-bc80-e41e5cd71901)
![capt7](https://github.com/user-attachments/assets/d6aa1c35-057f-4034-b204-5f428ae3a4b8)
![capt6](https://github.com/user-attachments/assets/b96cfa43-2cf6-405f-9cc4-53bfa4fbf222)
![capt5](https://github.com/user-attachments/assets/d270d63f-eea8-45d1-83dc-df6c4726ec85)
![capt4](https://github.com/user-attachments/assets/34c32113-dbed-4ad2-960b-cae12b49dc34)
![capt3](https://github.com/user-attachments/assets/9e6d7277-5995-49c7-8155-cd05724fb583)
![capt2](https://github.com/user-attachments/assets/0defb3df-d16b-44c8-874c-57080ce1dd87)
![capt1](https://github.com/user-attachments/assets/115b8e08-fa39-441a-a904-27ba542e21e4)





