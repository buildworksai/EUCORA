# Demo Database Backup & Restore

## Quick Answer: **YES, it's easy and much faster!**

Instead of regenerating demo data every time (30-60 seconds), you can restore from a backup (2-5 seconds).

## How It Works

1. **Create Backup** (one-time, after seeding with desired CAB Portal items):
   ```bash
   ./scripts/utilities/backup-demo-db.sh
   ```
   This creates `backend/data/demo_db_backup.sql.gz`

2. **Restore on "Seed Demo Data" Click**:
   - The UI "Seed Demo Data" button now automatically restores from backup if it exists
   - Falls back to seeding if backup doesn't exist
   - Much faster: ~2-5 seconds vs 30-60 seconds

## Workflow

### Step 1: Seed Data with Your Desired CAB Portal Items
```bash
# Seed data with more CAB items
docker exec eucora-control-plane python manage.py seed_demo_data \
  --assets 100 \
  --applications 20 \
  --deployments 50 \
  --users 10 \
  --events 200 \
  --clear-existing

# Or use the UI to seed, then manually add more CAB Portal items
```

### Step 2: Create Backup
```bash
./scripts/utilities/backup-demo-db.sh
```

### Step 3: Test Restore
```bash
# Clear data
docker exec eucora-control-plane python manage.py shell -c "from apps.core.demo_data import clear_demo_data; clear_demo_data()"

# Restore from backup
./scripts/utilities/restore-demo-db.sh
```

### Step 4: Use in UI
- Click "Seed Demo Data" in `/admin/demo-data`
- It will automatically restore from backup (if exists)
- Much faster than regenerating!

## Backup File Location

- **Path**: `backend/data/demo_db_backup.sql.gz`
- **Size**: ~500KB - 2MB (compressed)
- **Git**: Ignored (in `.gitignore`)

## Manual Restore

If you need to restore manually:
```bash
./scripts/utilities/restore-demo-db.sh [path-to-backup]
```

## Force Seeding (Skip Backup)

To force seeding instead of restoring:
- UI: Add `force_seed: true` to the request payload
- API: `POST /api/v1/admin/seed-demo-data` with `{"force_seed": true}`

## Benefits

✅ **10-30x faster** (2-5 seconds vs 30-60 seconds)  
✅ **Consistent data** (same CAB Portal items every time)  
✅ **No Celery dependency** (works even if Celery is down)  
✅ **Automatic fallback** (seeds if backup missing)  

## After Container Rebuild

- **With `-v` flag**: Database wiped, backup still exists → restore works
- **Without `-v` flag**: Database persists, backup restore still works (overwrites)
