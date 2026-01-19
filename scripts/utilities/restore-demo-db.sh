#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
#
# Restore a PostgreSQL backup of demo data.
# Usage: ./restore-demo-db.sh [backup-file-path]

set -euo pipefail

BACKUP_FILE="${1:-./backend/data/demo_db_backup.sql.gz}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring database backup: $BACKUP_FILE"
echo "⚠️  This will clear existing demo data and restore from backup..."

# Wait for database to be ready
until docker exec eucora-db pg_isready -U eucora_user -d eucora > /dev/null 2>&1; do
    echo "Waiting for database to be ready..."
    sleep 1
done

# Restore backup
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | docker exec -i eucora-db psql -U eucora_user -d eucora
else
    docker exec -i eucora-db psql -U eucora_user -d eucora < "$BACKUP_FILE"
fi

if [ $? -eq 0 ]; then
    echo "✅ Database restored successfully from: $BACKUP_FILE"
    echo ""
    echo "Note: You may need to enable demo mode:"
    echo "  docker exec eucora-control-plane python manage.py shell -c \"from apps.core.utils import set_demo_mode_enabled; set_demo_mode_enabled(True)\""
else
    echo "❌ Restore failed!"
    exit 1
fi
