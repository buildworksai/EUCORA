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

echo "Starting Django development server..."
exec "$@"
