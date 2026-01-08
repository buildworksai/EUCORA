#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Entrypoint script for EUCORA Control Plane
# Automatically runs migrations and starts the server

set -e

echo "Waiting for database to be ready..."
until python -c "
import psycopg2
import os
try:
    psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DB', 'eucora'),
        user=os.environ.get('POSTGRES_USER', 'eucora_user'),
        password=os.environ.get('POSTGRES_PASSWORD', 'eucora_dev_password'),
        host=os.environ.get('POSTGRES_HOST', 'localhost'),
        port=os.environ.get('POSTGRES_PORT', '5432')
    ).close()
    print('Database is ready!')
except Exception as e:
    print(f'Database not ready: {e}')
    exit(1)
" 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Running Django migrations..."
python manage.py migrate --noinput

echo "Setting up development data..."
python manage.py setup_dev_data

echo "Seeding initial demo data (small set for development)..."
python manage.py seed_demo_data \
  --assets 100 \
  --applications 10 \
  --deployments 20 \
  --users 5 \
  --events 100 \
  --batch-size 50 \
  --clear-existing || echo "Demo data seeding skipped (may already exist)"

echo "Enabling demo mode..."
python manage.py shell -c "
from apps.core.utils import set_demo_mode_enabled
set_demo_mode_enabled(True)
print('Demo mode enabled')
" || echo "Demo mode setup skipped"

echo "Starting Django development server..."
exec "$@"
