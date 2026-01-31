# Portfolio Management Demo & Testing Guide

## 🎯 Overview

The Portfolio Management backend is now **fully deployed and operational** in Docker with demo data ready for testing.

## 📊 Demo Data Summary

### Users Created
- **Portfolio Managers:**
  - `sarah_thompson` (password: `demo123`) - Manager of Enterprise Applications
  - `michael_chen` (password: `demo123`) - Manager of Security & Compliance

- **Application Managers:**
  - `jennifer_rodriguez` (password: `demo123`) - Owns 12 applications
  - `david_patel` (password: `demo123`)

### Portfolios
1. **Enterprise Applications** (ID: `afcf6f78-a538-43f8-b159-e5b3636e93e0`)
   - Manager: sarah_thompson
   - Budget: $2,500,000.00
   - Applications: 45
   - License Utilization: 77.0%
   - Health Score: 87.5
   - Compliance Score: 92.0
   - Scope: IT, Operations, Finance (NA, EMEA)

2. **Security & Compliance** (ID: `8c61c1e6-66a7-43a5-9a13-211623eb924a`)
   - Manager: michael_chen
   - Budget: $1,200,000.00
   - Applications: 22
   - License Utilization: 82.5%
   - Health Score: 94.2
   - Compliance Score: 98.5
   - Scope: Security, Risk, Legal (Global)

### Performance Snapshots
- **6 snapshots** created for jennifer_rodriguez
- Composite scores: 85.0, 82.0, 79.0 (trending data)
- Metrics include:
  - Deployment success rates (90-92%)
  - Health scores (84-88)
  - License utilization (76.5-81.5%)
  - MTTR (4.5-7.5 hours)

### True-Up Forecasts
1. **Microsoft Corporation - 2026-Q4**
   - Current: 850/1000 licenses (85%)
   - Forecast: 1,150 licenses (+35.3% growth)
   - Additional needed: 150 licenses
   - Estimated cost: $75,000
   - Confidence: 87%
   - Mitigation strategies: Right-sizing (80 licenses, $40K savings) + Harvesting (70 licenses, $35K savings)

2. **Adobe Systems - 2027-Q1**
   - Current: 380/500 licenses (76%)
   - Forecast: 480 licenses (+26.3% growth)
   - Within entitlement - no additional licenses needed
   - Confidence: 92%

## 🌐 API Endpoints

### Base URL
```
http://localhost:8000/api/v1/portfolio-management/
```

### Available Endpoints

#### Portfolios
```
GET    /portfolios/                      # List all portfolios
GET    /portfolios/{id}/                 # Get portfolio details
GET    /portfolios/{id}/metrics/         # Get portfolio metrics
POST   /portfolios/{id}/refresh_metrics/ # Trigger metric refresh
POST   /portfolios/                      # Create portfolio
PATCH  /portfolios/{id}/                 # Update portfolio
DELETE /portfolios/{id}/                 # Delete portfolio
```

#### Application Ownerships
```
GET    /ownerships/                      # List ownerships
GET    /ownerships/{id}/                 # Get ownership details
POST   /ownerships/                      # Create ownership
PATCH  /ownerships/{id}/                 # Update ownership
POST   /ownerships/{id}/activate/        # Activate ownership
POST   /ownerships/{id}/deactivate/      # Deactivate ownership
```

#### Performance Metrics
```
GET    /performance/                     # List performance snapshots
GET    /performance/{id}/                # Get snapshot details
GET    /performance/leaderboard/         # Top performers
```

Query parameters:
- `manager={user_id}` - Filter by manager
- `portfolio={portfolio_id}` - Filter by portfolio
- `period_start={date}` - Filter by start date
- `period_end={date}` - Filter by end date
- `limit={n}` - Limit results (leaderboard)

#### True-Up Forecasts
```
GET    /forecasts/                       # List forecasts
GET    /forecasts/{id}/                  # Get forecast details
GET    /forecasts/high_risk/             # High-risk forecasts only
POST   /forecasts/                       # Create forecast
PATCH  /forecasts/{id}/                  # Update forecast
```

Query parameters:
- `vendor={vendor_id}` - Filter by vendor
- `portfolio={portfolio_id}` - Filter by portfolio
- `forecast_period={period}` - Filter by period

#### Packaging Requests
```
GET    /packaging-requests/              # List requests
GET    /packaging-requests/{id}/         # Get request details
GET    /packaging-requests/my_requests/  # My requests
GET    /packaging-requests/assigned_to_me/ # Assigned to me
POST   /packaging-requests/              # Create request
POST   /packaging-requests/{id}/assign/  # Assign request
POST   /packaging-requests/{id}/complete/ # Complete request
PATCH  /packaging-requests/{id}/         # Update request
```

## 🧪 Testing the API

### 1. Authentication
All endpoints require authentication. Use Django admin or session-based auth for testing.

### 2. Test with curl

**Login (get session cookie):**
```bash
# Login to get session
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"sarah_thompson","password":"demo123"}'
```

**List Portfolios:**
```bash
curl -b cookies.txt http://localhost:8000/api/v1/portfolio-management/portfolios/
```

**Get Portfolio Details:**
```bash
# Replace with actual portfolio ID from demo data
curl -b cookies.txt http://localhost:8000/api/v1/portfolio-management/portfolios/afcf6f78-a538-43f8-b159-e5b3636e93e0/
```

**Get Portfolio Metrics:**
```bash
curl -b cookies.txt http://localhost:8000/api/v1/portfolio-management/portfolios/afcf6f78-a538-43f8-b159-e5b3636e93e0/metrics/
```

**List Performance Snapshots (with filtering):**
```bash
# Filter by manager
curl -b cookies.txt "http://localhost:8000/api/v1/portfolio-management/performance/?manager=203"

# Get leaderboard
curl -b cookies.txt "http://localhost:8000/api/v1/portfolio-management/performance/leaderboard/?limit=5"
```

**List True-Up Forecasts:**
```bash
curl -b cookies.txt http://localhost:8000/api/v1/portfolio-management/forecasts/

# High-risk only
curl -b cookies.txt http://localhost:8000/api/v1/portfolio-management/forecasts/high_risk/
```

### 3. Test with Swagger UI

Access the interactive API documentation:
```
http://localhost:8000/api/docs/
```

1. Click "Authorize" button
2. Login with demo credentials
3. Test endpoints interactively

## 📈 Sample API Responses

### Portfolio List Response
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "afcf6f78-a538-43f8-b159-e5b3636e93e0",
      "name": "Enterprise Applications",
      "manager": 201,
      "manager_name": "sarah_thompson",
      "total_applications": 45,
      "total_licenses_entitled": 5000,
      "total_licenses_consumed": 3850,
      "license_utilization_percent": 77.0,
      "health_score": 87.5,
      "compliance_score": 92.0,
      "budget_annual": "2500000.00",
      "created_at": "2026-01-30T...",
      "updated_at": "2026-01-30T..."
    }
  ]
}
```

### Performance Snapshot Response
```json
{
  "id": "...",
  "manager": 203,
  "manager_name": "jennifer_rodriguez",
  "portfolio": "afcf6f78-a538-43f8-b159-e5b3636e93e0",
  "portfolio_name": "Enterprise Applications",
  "recorded_at": "2026-01-30T...",
  "period_start": "2025-12-01T...",
  "period_end": "2025-12-31T...",
  "deployments_total": 25,
  "deployments_successful": 23,
  "success_rate_percent": 92.0,
  "avg_deployment_duration_days": 2.5,
  "avg_health_score": 88.0,
  "utilization_percent": 76.5,
  "composite_score": 85.0
}
```

### True-Up Forecast Response
```json
{
  "id": "...",
  "vendor": "91ad028b-e910-4d8f-8b4e-3b82bec0d8af",
  "vendor_name": "Microsoft Corporation",
  "portfolio": "afcf6f78-a538-43f8-b159-e5b3636e93e0",
  "portfolio_name": "Enterprise Applications",
  "forecast_period": "2026-Q4",
  "forecast_generated_at": "2026-01-30T...",
  "entitled_quantity_current": 1000,
  "consumed_quantity_current": 850,
  "utilization_current_percent": 85.0,
  "consumed_quantity_forecast": 1150,
  "consumption_growth_percent": 35.3,
  "additional_licenses_needed": 150,
  "estimated_cost_impact": "75000.00",
  "confidence_percent": 87.0,
  "mitigation_recommendations": [
    {
      "strategy": "right_sizing",
      "description": "Review over-entitled SKUs and reduce allocation",
      "licenses_saved": 80,
      "cost_savings": 40000.0
    }
  ],
  "potential_savings": "75000.00"
}
```

## 🔍 Database Verification

### Check Data Directly
```bash
# List portfolios
docker exec eucora-db psql -U eucora_user -d eucora -c \
  "SELECT name, budget_annual, total_applications FROM portfolio_management_portfolio;"

# List performance snapshots
docker exec eucora-db psql -U eucora_user -d eucora -c \
  "SELECT manager_id, composite_score, deployments_total FROM portfolio_management_performance LIMIT 5;"

# List forecasts
docker exec eucora-db psql -U eucora_user -d eucora -c \
  "SELECT forecast_period, consumed_quantity_forecast, additional_licenses_needed FROM portfolio_management_true_up_forecast;"
```

## 🚀 Next Steps for Testing

1. **Frontend Integration:**
   - Create Portfolio Manager dashboard
   - Build Application Manager views
   - Implement performance leaderboard
   - Display true-up forecasts with charts

2. **Service Layer Testing:**
   - Run unit tests: `docker exec eucora-control-plane python manage.py test apps.portfolio_management`
   - Test composite score calculations
   - Verify forecast generation logic
   - Test metric aggregation

3. **Load Testing:**
   - Test with larger datasets
   - Verify pagination and filtering
   - Check query performance with indexes

4. **Integration Testing:**
   - Link to actual Application records
   - Create real ApplicationOwnerships
   - Generate PackagingRequests
   - Test workflow transitions

## ✅ Success Criteria

- [x] Database schema created (5 tables)
- [x] Migrations applied successfully
- [x] Demo data loaded (2 portfolios, 4 users, 6 performance snapshots, 2 forecasts)
- [x] API endpoints accessible
- [x] Authentication working
- [x] Filtering and search functional
- [ ] Frontend integration complete
- [ ] End-to-end workflows tested

## 📞 Support

For issues or questions:
- Check logs: `docker logs eucora-control-plane`
- View API docs: http://localhost:8000/api/docs/
- Database access: `docker exec -it eucora-db psql -U eucora_user -d eucora`

---

**Status:** ✅ **Backend Complete & Ready for Frontend Integration**
