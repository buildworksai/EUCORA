---
name: kubernetes-patterns
description: Kubernetes deployment patterns for EUCORA including Deployments, Services, ConfigMaps, Secrets, Ingress, and Helm. Use when deploying to Kubernetes, configuring k8s resources, or managing container orchestration.
status: ✅ Working
last-validated: 2026-01-30
---

# Kubernetes Patterns

Kubernetes resource patterns for EUCORA production deployments.

---

## Quick Reference

| Resource | Pattern |
|----------|---------|
| Deployments | RollingUpdate, health probes, resource limits |
| Services | ClusterIP (internal), LoadBalancer (external) |
| ConfigMaps | Non-sensitive configuration |
| Secrets | External Secrets Operator + Vault |
| Ingress | nginx-ingress + cert-manager |
| Singleton | Recreate strategy (Celery Beat) |

---

## Deployment Patterns

### Standard API Deployment

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eucora-api
  namespace: eucora
  labels:
    app: eucora
    component: api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: eucora
      component: api
  template:
    metadata:
      labels:
        app: eucora
        component: api
    spec:
      serviceAccountName: eucora-api

      containers:
        - name: api
          image: eucora/backend:latest
          ports:
            - containerPort: 8000
              name: http

          # Environment from ConfigMap/Secret
          envFrom:
            - configMapRef:
                name: eucora-config
            - secretRef:
                name: eucora-secrets

          # Health probes
          livenessProbe:
            httpGet:
              path: /health/live/
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 3

          readinessProbe:
            httpGet:
              path: /health/ready/
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 3

          # Resource limits (MANDATORY)
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi

          # Volume mounts
          volumeMounts:
            - name: static-files
              mountPath: /app/staticfiles

      volumes:
        - name: static-files
          persistentVolumeClaim:
            claimName: eucora-static-pvc

      # Pod anti-affinity for HA
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: eucora
                    component: api
                topologyKey: kubernetes.io/hostname
```

### Celery Worker Deployment

```yaml
# k8s/celery-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eucora-celery-worker
  namespace: eucora
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
  selector:
    matchLabels:
      app: eucora
      component: celery-worker
  template:
    spec:
      containers:
        - name: worker
          image: eucora/backend:latest
          command: ["celery", "-A", "config", "worker", "-l", "info", "-c", "4"]

          envFrom:
            - configMapRef:
                name: eucora-config
            - secretRef:
                name: eucora-secrets

          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi

          # Liveness probe for worker
          livenessProbe:
            exec:
              command:
                - celery
                - -A
                - config
                - inspect
                - ping
            initialDelaySeconds: 60
            periodSeconds: 30
            timeoutSeconds: 10
```

### Celery Beat (Singleton Pattern)

```yaml
# k8s/celery-beat-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eucora-celery-beat
  namespace: eucora
spec:
  replicas: 1  # MUST be 1 - singleton
  strategy:
    type: Recreate  # Prevent duplicate schedulers
  selector:
    matchLabels:
      app: eucora
      component: celery-beat
  template:
    spec:
      containers:
        - name: beat
          image: eucora/backend:latest
          command: ["celery", "-A", "config", "beat", "-l", "info"]

          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 200m
              memory: 512Mi
```

---

## Service Patterns

### ClusterIP (Internal)

```yaml
# k8s/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: eucora-api
  namespace: eucora
spec:
  type: ClusterIP
  selector:
    app: eucora
    component: api
  ports:
    - name: http
      port: 80
      targetPort: 8000
```

### Headless Service (StatefulSets)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: eucora-db-headless
spec:
  type: ClusterIP
  clusterIP: None  # Headless
  selector:
    app: eucora
    component: postgres
  ports:
    - port: 5432
```

---

## ConfigMap and Secrets

### ConfigMap (Non-Sensitive)

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: eucora-config
  namespace: eucora
data:
  DEBUG: "False"
  ALLOWED_HOSTS: "eucora.example.com"
  CORS_ALLOWED_ORIGINS: "https://eucora.example.com"
  CELERY_BROKER_URL: "redis://redis:6379/0"
  LOG_LEVEL: "INFO"
```

### External Secrets (Azure Key Vault)

```yaml
# k8s/external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: eucora-secrets
  namespace: eucora
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: azure-keyvault
    kind: ClusterSecretStore
  target:
    name: eucora-secrets
    creationPolicy: Owner
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: eucora-database-url
    - secretKey: SECRET_KEY
      remoteRef:
        key: eucora-django-secret-key
    - secretKey: INTUNE_CLIENT_SECRET
      remoteRef:
        key: eucora-intune-client-secret
```

---

## Ingress with TLS

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: eucora-ingress
  namespace: eucora
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
    - hosts:
        - eucora.example.com
        - api.eucora.example.com
      secretName: eucora-tls
  rules:
    - host: eucora.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: eucora-frontend
                port:
                  number: 80
    - host: api.eucora.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: eucora-api
                port:
                  number: 80
```

---

## PersistentVolumeClaims

```yaml
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: eucora-static-pvc
  namespace: eucora
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: azure-file
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: eucora-media-pvc
  namespace: eucora
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: azure-file
  resources:
    requests:
      storage: 50Gi
```

---

## Namespace and RBAC

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: eucora
  labels:
    name: eucora
    environment: production
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: eucora-api
  namespace: eucora
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: eucora-api-role
  namespace: eucora
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: eucora-api-rolebinding
  namespace: eucora
subjects:
  - kind: ServiceAccount
    name: eucora-api
roleRef:
  kind: Role
  name: eucora-api-role
  apiGroup: rbac.authorization.k8s.io
```

---

## Health Probes

| Probe | Purpose | When Fails |
|-------|---------|------------|
| **Liveness** | Is container alive? | Restart container |
| **Readiness** | Can accept traffic? | Remove from Service |
| **Startup** | Still starting? | Delay liveness checks |

```yaml
livenessProbe:
  httpGet:
    path: /health/live/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready/
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3

startupProbe:
  httpGet:
    path: /health/live/
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 30  # 5 min startup window
```

---

## Helm Values (Reference)

```yaml
# values.yaml
replicaCount: 3

image:
  repository: eucora/backend
  tag: latest
  pullPolicy: Always

resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: eucora.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: eucora-tls
      hosts:
        - eucora.example.com

postgresql:
  enabled: true
  auth:
    existingSecret: eucora-secrets
    secretKeys:
      adminPasswordKey: POSTGRES_PASSWORD

redis:
  enabled: true
  auth:
    enabled: false
```

---

## Commands Reference

```bash
# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/

# Check deployment status
kubectl get deployments -n eucora
kubectl rollout status deployment/eucora-api -n eucora

# View logs
kubectl logs -f deployment/eucora-api -n eucora

# Scale deployment
kubectl scale deployment/eucora-api --replicas=5 -n eucora

# Rollback
kubectl rollout undo deployment/eucora-api -n eucora

# Debug pod
kubectl exec -it deployment/eucora-api -n eucora -- /bin/bash
```

---

## Anti-Patterns

| ❌ FORBIDDEN | ✅ CORRECT |
|--------------|------------|
| No resource limits | Always set limits |
| No health probes | Liveness + readiness mandatory |
| Secrets in ConfigMap | Use External Secrets |
| Root containers | Run as non-root user |
| Single replica for API | ≥3 replicas for HA |
| Multiple Celery Beat | Exactly 1 replica (Recreate) |
