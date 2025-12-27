🤖 OrchestrateurAutoML
Plateforme AutoML Distribuée – Architecture Microservices

OrchestrateurAutoML est une plateforme AutoML modulaire et scalable, conçue pour automatiser l’ensemble du cycle de vie d’un modèle de Machine Learning, de la préparation des données jusqu’à l’évaluation finale des performances.

Elle permet de transformer des données brutes en modèles performants avec un minimum d’intervention humaine, tout en respectant les bonnes pratiques MLOps.

🚀 Vue d’ensemble

Automatisation complète du pipeline Machine Learning

Architecture microservices indépendante et scalable

Communication inter-services via APIs REST

Support du calcul distribué et des GPU

Suivi et versionnage des expériences et modèles

🏗️ Architecture Générale

Le système repose sur plusieurs microservices coordonnés, chacun ayant une responsabilité bien définie :

🔹 Frontend

Streamlit

Interface utilisateur pour :

Chargement des datasets

Configuration des entraînements

Visualisation des métriques et résultats

🔹 Data Preparer

Nettoyage automatique des données

Prétraitement (encoding, normalisation, etc.)

Extraction des métadonnées du dataset

🔹 Model Selector

Sélection intelligente des modèles adaptés au dataset :

RandomForest

XGBoost

CNN

Autres architectures ML / DL

🔹 Trainer

Entraînement distribué avec PyTorch et Ray

Support CPU / GPU

Gestion des jobs d’entraînement

🔹 HyperOpt

Optimisation automatique des hyperparamètres

Maximisation des performances des modèles

🔹 Evaluator

Évaluation avancée des performances

Comparaison des modèles entraînés

Génération de métriques et rapports

🔹 MLflow

Tracking des expériences

Versionnage des modèles

Centralisation des métriques et artefacts

🔹 MinIO

Stockage objet S3-compatible

Datasets, modèles et artefacts d’entraînement

🛠️ Stack Technique
Catégorie	Technologies
Langage	Python 3.9+
Framework Web	FastAPI, Uvicorn
Machine Learning	PyTorch, Scikit-Learn, Ray, Pandas
MLOps & Tracking	MLflow
Base de données	PostgreSQL (une instance par service)
Stockage & Cache	MinIO, Redis
Interface Utilisateur	Streamlit
Conteneurisation	Docker, Docker Compose
🔧 Installation & Lancement
✅ Prérequis

Docker

Docker Compose

📥 Cloner le dépôt
git clone <URL_DU_DEPOT>
cd OrchestrateurAutoML

▶️ Lancer la plateforme
docker-compose up --build

🌐 Accès à l’interface

Interface Streamlit :
http://localhost:8501
 (port configurable)

📌 Objectifs du Projet

Simplifier l’utilisation de l’AutoML

Favoriser la reproductibilité des expériences

Offrir une architecture robuste, modulaire et extensible

Intégrer les bonnes pratiques MLOps dès la conception



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





