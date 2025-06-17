# Dockerfile for the Seismicity Poller Service 
# This service polls seismicity data from a feed and stores it in a database.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install feedparser geopy boto3

# Copy the polling script
COPY src/poll_seismic.py .

# Run the poller
CMD ["python", "poll_seismic.py"]


// Jenkinsfile
pipeline {
  agent any
  environment {
    REGISTRY = 'ghcr.io/itp24102'
    IMAGE = "${REGISTRY}/poller:latest"
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }
    stage('Build') {
      steps {
        dir('services/poller') {
          sh 'docker build -t ${IMAGE} .'
        }
      }
    }
    stage('Login to GHCR') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'ghcr-pat', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_TOKEN')]) {
          sh 'echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin'
        }
      }
    }
    stage('Push') {
      steps {
        sh 'docker push ${IMAGE}'
      }
    }
    stage('Trigger ArgoCD') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'argocd-cli', usernameVariable: 'ARGO_USER', passwordVariable: 'ARGO_PASS')]) {
          sh "argocd login $ARGO_SERVER --username $ARGO_USER --password $ARGO_PASS --insecure"
          sh 'argocd app sync seismicity-app'
        }
      }
    }
  }
}
