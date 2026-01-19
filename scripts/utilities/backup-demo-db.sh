#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
#
# Create a PostgreSQL backup of demo data for fast restore.
# Usage: ./backup-demo-db.sh [backup-file-path]
#
# This backup should be created AFTER seeding demo data with desired CAB Portal items.

set -euo pipefail

BACKUP_FILE="${1:-./backend/data/demo_db_backup.sql.gz}"
BACKUP_DIR=$(dirname "$BACKUP_FILE")

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "Creating database backup for demo data..."
echo "Backup file: $BACKUP_FILE"

# Create backup using pg_dump from the database container
# Only backup demo data (is_demo=True) to keep backup small
# Note: --clean and --data-only can't be used together, so we use --data-only only
docker exec eucora-db pg_dump \
    -U eucora_user \
    -d eucora \
    --no-owner \
    --no-acl \
    --data-only \
    --exclude-table=django_migrations \
    --exclude-table=django_content_type \
    --exclude-table=auth_permission \
    --exclude-table=django_session \
    --exclude-table=authtoken_token \
    --exclude-table=django_admin_log \
    | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)"
    echo ""
    echo "To restore this backup, use:"
    echo "  ./scripts/utilities/restore-demo-db.sh $BACKUP_FILE"
else
    echo "❌ Backup failed!"
    exit 1
fi
