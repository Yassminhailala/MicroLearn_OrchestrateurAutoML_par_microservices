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
