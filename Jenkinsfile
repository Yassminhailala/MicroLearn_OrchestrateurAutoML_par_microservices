pipeline {
    agent any

    environment {
        // Définir des variables d'environnement si nécessaire
        COMPOSE_PROJECT_NAME = "automl-platform"
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                // Jenkins récupère automatiquement le code du repo configuré
                checkout scm
            }
        }

        stage('Build Services') {
            steps {
                echo 'Building Docker images...'
                // Reconstruit les images en parallèle pour gagner du temps
                bat 'docker-compose build --parallel'
            }
        }

        stage('Run Application') {
            steps {
                echo 'Cleaning up potential conflicts...'
                // Force remove containers by specific name to handle conflicts from other project contexts
                // Ignore errors (|| exit 0) if containers don't exist
                bat 'docker rm -f automl_postgres automl_minio automl_data_preparer automl_model_selector automl_model_selector_db automl_frontend automl_mlflow automl_trainer automl_trainer_db automl_evaluator automl_evaluator_db automl_adminer automl_deployer automl_deployer_db automl_hyperopt automl_hyperopt_db automl_hyperopt_redis automl_nats automl_orchestrator || exit 0'
                
                // Also run standard down just in case
                bat 'docker-compose down'

                echo 'Launching application...'
                // Relance les conteneurs en mode détaché (Run)
                bat 'docker-compose up -d'
                
                echo 'Verifying application status...'
                bat 'docker-compose ps'
            }
        }
        
        stage('Cleanup') {
            steps {
                echo 'Cleaning up unused images...'
                // Nettoie les images "dangling" pour économiser de l'espace disque
                bat 'docker image prune -f'
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded! Application is deployed. 🚀'
        }
        failure {
            echo 'Pipeline failed. Please check logs. ❌'
        }
    }
}
