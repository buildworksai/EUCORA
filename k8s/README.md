# Kubernetes Deployment Guide

## Overview

This directory contains Kubernetes manifests for deploying EUCORA in production.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- External secrets management (Vault, Azure Key Vault, AWS Secrets Manager)
- Persistent volume provisioner
- Ingress controller (nginx recommended)
- cert-manager for TLS certificates

## Deployment Steps

### 1. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Create Secrets

**IMPORTANT**: Never commit `secrets.yaml`. Use external secrets management.

```bash
# Copy template
cp k8s/secrets.yaml.template k8s/secrets.yaml

# Edit secrets.yaml with actual values from vault
# Then apply:
kubectl apply -f k8s/secrets.yaml
```

### 3. Create ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Deploy Database (PostgreSQL)

Use managed PostgreSQL service (Azure Database, AWS RDS, GCP Cloud SQL) or deploy via Helm:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  --namespace eucora \
  --set auth.postgresPassword=CHANGE_ME \
  --set auth.database=eucora
```

### 5. Deploy Redis

```bash
helm install redis bitnami/redis \
  --namespace eucora \
  --set auth.password=CHANGE_ME
```

### 6. Deploy MinIO (or use S3-compatible service)

```bash
helm install minio bitnami/minio \
  --namespace eucora \
  --set auth.rootUser=minioadmin \
  --set auth.rootPassword=CHANGE_ME
```

### 7. Deploy Backend Services

```bash
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/celery-worker-deployment.yaml
kubectl apply -f k8s/celery-beat-deployment.yaml
kubectl apply -f k8s/api-service.yaml
```

### 8. Deploy Frontend

```bash
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
```

### 9. Configure Ingress

Update `k8s/ingress.yaml` with your domain names, then:

```bash
kubectl apply -f k8s/ingress.yaml
```

### 10. Run Migrations

```bash
kubectl exec -it deployment/eucora-api -n eucora -- python manage.py migrate
```

### 11. Collect Static Files

```bash
kubectl exec -it deployment/eucora-api -n eucora -- python manage.py collectstatic --noinput
```

## Health Checks

- Liveness: `GET /health/live`
- Readiness: `GET /health/ready`

## Monitoring

Configure Prometheus scraping for:
- `/metrics` endpoint (if enabled)
- Celery worker metrics
- Database connection pool metrics

## Scaling

```bash
# Scale API replicas
kubectl scale deployment eucora-api --replicas=5 -n eucora

# Scale Celery workers
kubectl scale deployment eucora-celery-worker --replicas=4 -n eucora
```

## Troubleshooting

```bash
# Check pod status
kubectl get pods -n eucora

# View logs
kubectl logs -f deployment/eucora-api -n eucora

# Check events
kubectl get events -n eucora --sort-by='.lastTimestamp'
```
