# EUCORA Backend - Quick Start Guide

## Prerequisites

- Docker Desktop installed and running
- Docker Compose v2.x

## Quick Start (Development)

### 1. Start Services

```bash
cd backend
docker-compose -f docker-compose.dev.yml up -d
```

**Services Started**:
- PostgreSQL 17 (port 5432)
- Redis 7 (port 6379)
- MinIO (ports 9000, 9001)
- Django Backend (port 8000)

### 2. Wait for Health Checks

```bash
# Check service status
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs -f eucora-api
```

### 3. Run Migrations

```bash
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py migrate
```

### 4. Create Superuser

```bash
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py createsuperuser
```

### 5. Access Services

- **Django Admin**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/docs/
- **MinIO Console**: http://localhost:9001 (minioadmin / minioadmin)

### 6. Test API Health

```bash
curl http://localhost:8000/api/v1/health/
```

## Stop Services

```bash
docker-compose -f docker-compose.dev.yml down
```

## Clean Up (Remove Volumes)

```bash
docker-compose -f docker-compose.dev.yml down -v
```

---

## Troubleshooting

### Build Taking Too Long

The first build can take 5-10 minutes due to Alpine Linux compiling dependencies (psycopg2, cryptography, etc.). Subsequent builds will be cached.

### Database Connection Error

Wait for PostgreSQL health check to pass:
```bash
docker-compose -f docker-compose.dev.yml logs db
```

### Redis Connection Error

Wait for Redis health check to pass:
```bash
docker-compose -f docker-compose.dev.yml logs redis
```

---

**EUCORA Control Plane - Built by BuildWorks.AI**
