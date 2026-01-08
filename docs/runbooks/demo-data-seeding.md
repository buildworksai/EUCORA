# Demo Data Seeding Runbook

**SPDX-License-Identifier: Apache-2.0**  
**Version**: v1.2  
**Status**: Active  
**Owner**: Platform Engineering  
**Last Updated**: 2026-01-06

---

## Purpose

Provide controlled demo data seeding for EUCORA environments without impacting production data.

## Prerequisites

- Admin access to the EUCORA Control Plane
- Backend services running with database access

## Management Command

Seed demo data with the Django management command:

```bash
python manage.py seed_demo_data \
  --assets 50000 \
  --applications 5000 \
  --deployments 10000 \
  --users 1000 \
  --events 100000 \
  --clear-existing \
  --batch-size 1000
```

## Admin API Endpoints

- `POST /api/v1/admin/seed-demo-data`
- `DELETE /api/v1/admin/clear-demo-data`
- `GET /api/v1/admin/demo-data-stats`
- `GET|POST /api/v1/admin/demo-mode`

## Demo Mode

When demo mode is enabled, list endpoints return demo-only records by default. Use query param `include_demo=all` to include both demo and production records in list APIs.

## Safety Notes

- Demo data is tagged with `is_demo=true` and can be purged without affecting production data.
- Audit events remain append-only for production; demo events are purged using a controlled cleanup routine.
