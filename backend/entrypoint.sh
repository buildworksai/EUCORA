#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Entrypoint script for EUCORA Control Plane
# Automatically runs migrations and starts the server
#
# CRITICAL: This script is designed for customer demos - it must NEVER fail completely.
# Errors in non-critical operations (like seeding) will be logged but won't stop the server.

# Only exit on critical errors (database connection, migrations)
# Use set -e carefully - we want to catch errors but not exit on non-critical failures
set -euo pipefail

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
python manage.py setup_dev_data || {
  echo "⚠️  Warning: setup_dev_data failed, continuing anyway..."
}

# CRITICAL: Demo data and demo mode setup - must not fail container startup
echo "=== DEMO DATA SETUP (Non-blocking) ==="

# Function to safely enable demo mode with retries
enable_demo_mode_safe() {
  local max_retries=3
  local retry=0

  while [ $retry -lt $max_retries ]; do
    if python manage.py shell -c "
from apps.core.utils import set_demo_mode_enabled
try:
    result = set_demo_mode_enabled(True)
    print(f'Demo mode enabled: {result}')
    exit(0)
except Exception as e:
    print(f'Error enabling demo mode: {e}')
    exit(1)
" 2>&1; then
      echo "✅ Demo mode enabled successfully"
      return 0
    else
      retry=$((retry + 1))
      echo "⚠️  Attempt $retry/$max_retries failed, retrying in 2 seconds..."
      sleep 2
    fi
  done

  echo "❌ Failed to enable demo mode after $max_retries attempts, but continuing..."
  return 1
}

# Function to safely check and seed demo data
check_and_seed_demo_data() {
  local check_result
  check_result=$(python manage.py shell -c "
import sys
try:
    from apps.core.demo_data import demo_data_stats
    stats = demo_data_stats()
    total = sum(stats.values())
    if total == 0:
        print('EMPTY')
        sys.exit(1)
    else:
        print(f'EXISTS:{total}')
        print(f'Assets: {stats[\"assets\"]:,}', file=sys.stderr)
        print(f'Applications: {stats[\"applications\"]:,}', file=sys.stderr)
        print(f'Deployments: {stats[\"deployments\"]:,}', file=sys.stderr)
        sys.exit(0)
except Exception as e:
    print(f'ERROR:{e}', file=sys.stderr)
    sys.exit(2)
" 2>&1)

  local exit_code=$?

  if [ $exit_code -eq 0 ]; then
    echo "✅ Demo data already exists"
    echo "$check_result" | grep -v "EXISTS:" || true
    return 0
  elif [ $exit_code -eq 1 ]; then
    echo "📦 No demo data found. Seeding initial demo data..."
    seed_demo_data_safe || {
      echo "⚠️  Warning: Demo data seeding failed, but server will start anyway"
      echo "   You can seed data manually via /admin/demo-data or management command"
      return 1
    }
    return 0
  else
    echo "⚠️  Error checking demo data status: $check_result"
    echo "   Attempting to seed anyway..."
    seed_demo_data_safe || {
      echo "⚠️  Warning: Demo data seeding failed, but server will start anyway"
      return 1
    }
    return 0
  fi
}

# Function to safely seed demo data with retries
seed_demo_data_safe() {
  local max_retries=2
  local retry=0

  while [ $retry -lt $max_retries ]; do
    if python manage.py seed_demo_data \
      --assets 100 \
      --applications 10 \
      --deployments 20 \
      --users 5 \
      --events 100 \
      --batch-size 50 \
      2>&1; then
      echo "✅ Demo data seeded successfully"
      return 0
    else
      retry=$((retry + 1))
      if [ $retry -lt $max_retries ]; then
        echo "⚠️  Seeding attempt $retry failed, retrying in 3 seconds..."
        sleep 3
      fi
    fi
  done

  echo "❌ Demo data seeding failed after $max_retries attempts"
  return 1
}

# Execute demo setup (non-blocking)
# These functions handle their own errors, so we don't want set -e to kill the container
set +e
check_and_seed_demo_data || echo "⚠️  Demo data setup had issues, but continuing..."
enable_demo_mode_safe || echo "⚠️  Demo mode setup had issues, but continuing..."
set -e

echo "=== DEMO SETUP COMPLETE ==="

echo "Starting Django development server..."
# Use exec to replace shell with the server process
# This ensures proper signal handling and prevents the container from exiting
exec "$@"
