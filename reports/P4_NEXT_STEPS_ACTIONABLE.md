# P4 Next Steps - Immediate Action Items

## Quick Reference: What to Fix Next

### 1. URL Routing Issues (HIGHEST PRIORITY)
**Problem**: Test endpoint references don't match actual URL patterns

**Example**:
```python
# Test does this:
url = reverse('cab_workflow:approve', kwargs={'correlation_id': ...})

# But URL pattern might be:
path('approve/<uuid:id>/', ...)  # Different parameter name or pattern
```

**How to Fix**:
1. Open each app's `urls.py` file
2. Find the actual URL pattern names and parameters
3. Update test `reverse()` calls to match
4. Run tests to verify fixes

**Apps Needing URL Verification**:
- `apps/cab_workflow/urls.py` - Test references 'cab_workflow:approve'
- `apps/event_store/urls.py` - Test references 'event_store:log', 'event_store:list'
- `apps/evidence_store/urls.py` - Multiple endpoint issues
- `apps/deployment_intents/urls.py` - Endpoint contract verification needed
- All other apps with view tests

**Time Estimate**: 30 minutes (once you identify the patterns)

---

### 2. Endpoint Contract Verification
**Problem**: Tests expect specific request/response structures

**What to Check**:
- Request body schema (what fields are required?)
- Response structure (what fields does API return?)
- Status codes (200 vs 201 vs 204?)
- Data types (int, string, object, array?)

**Example**:
```python
# Test expects:
response.data['events']  # But API might return 'data' or 'results'

# Or expects:
response.json()  # But API returns 400, not 200
```

**How to Fix**:
1. Read each view/endpoint implementation
2. Check what it actually returns
3. Update test assertions to match
4. Add comments explaining response structure

**Time Estimate**: 1-2 hours (checking 20+ endpoints)

---

### 3. Authentication/Permission Issues
**Problem**: Some endpoints may require specific user roles or permissions

**Fixtures Available**:
- `admin_user` - Full permissions
- `regular_user` - Limited permissions
- `authenticated_user` - Alias for admin_user
- `authenticated_client` - Auto-injects admin_user
- `authenticated_client_regular` - Regular user context

**How to Fix**:
```python
# If endpoint requires admin:
def test_admin_endpoint(authenticated_client, admin_user):
    response = authenticated_client.post(url, data)
    assert response.status_code == 200

# If endpoint requires specific role:
def test_publisher_endpoint(authenticated_client_regular, regular_user):
    # This test runs as regular_user, may get 403 if needs admin
    response = authenticated_client_regular.post(url, data)
    # Expect 403 Forbidden if permission denied
    assert response.status_code == 403
```

**Time Estimate**: 30 minutes (add role-specific fixtures as needed)

---

### 4. Test Pattern to Replicate

**Working Example** (Health tests - 4/4 PASSING):
```python
@pytest.mark.django_db
class TestHealthChecks:
    """Test health check endpoints."""
    
    def test_liveness_check(self, api_client):
        """Test that endpoint exists and returns 200."""
        response = api_client.get('/api/v1/health/live')
        
        assert response.status_code == 200
        assert response.json()['status'] == 'alive'

    def test_readiness_check(self, authenticated_client):
        """Test authenticated endpoint."""
        response = authenticated_client.get('/api/v1/health/ready')
        
        assert response.status_code == 200
```

**Key Points**:
- ✅ Use `api_client` for unauthenticated endpoints
- ✅ Use `authenticated_client` for protected endpoints
- ✅ Direct URL paths, not `reverse()` if routes are simple
- ✅ Use `response.json()` for JSON responses
- ✅ Check status_code and data fields separately

---

## Quick Fix Checklist

### For Each Failing Test:
```
[ ] 1. Get error message: Run test with -xvs flag
[ ] 2. Identify issue type:
      [ ] URL pattern? (NotFound 404)
      [ ] Auth? (Forbidden 403)
      [ ] Request structure? (BadRequest 400)
      [ ] Response structure? (AssertionError)
[ ] 3. Locate source:
      [ ] Find app's urls.py
      [ ] Find view implementation
      [ ] Read docstring/comments
[ ] 4. Fix test:
      [ ] Update URL reference
      [ ] Use correct fixtures
      [ ] Fix assertion
[ ] 5. Verify:
      [ ] Run test again
      [ ] Move to next test
```

---

## Batch Commands to Run

### Test a Single Module:
```bash
docker-compose -f docker-compose.dev.yml exec -T -e OTEL_ENABLED=false \
  eucora-api pytest apps/MODULE_NAME/tests/ -v --tb=short --no-cov
```

### Test a Single Test Class:
```bash
docker-compose -f docker-compose.dev.yml exec -T -e OTEL_ENABLED=false \
  eucora-api pytest apps/MODULE_NAME/tests/test_file.py::TestClassName -v --tb=short --no-cov
```

### Test a Single Test Method:
```bash
docker-compose -f docker-compose.dev.yml exec -T -e OTEL_ENABLED=false \
  eucora-api pytest apps/MODULE_NAME/tests/test_file.py::TestClassName::test_method -xvs --tb=short --no-cov
```

### Count Results:
```bash
# Count passing tests:
docker-compose -f docker-compose.dev.yml exec -T -e OTEL_ENABLED=false \
  eucora-api pytest --no-cov -v 2>&1 | grep -c "PASSED"

# Count failing tests:
docker-compose -f docker-compose.dev.yml exec -T -e OTEL_ENABLED=false \
  eucora-api pytest --no-cov -v 2>&1 | grep -c "FAILED"

# Count errors:
docker-compose -f docker-compose.dev.yml exec -T -e OTEL_ENABLED=false \
  eucora-api pytest --no-cov -v 2>&1 | grep -c "ERROR"
```

---

## Available Fixtures Reference

### Authentication
```python
def test_example(authenticated_client, admin_user):
    """authenticated_client = API client with admin_user logged in"""
    response = authenticated_client.post(url, data)

def test_example(authenticated_client_regular, regular_user):
    """authenticated_client_regular = API client with regular_user"""
    response = authenticated_client_regular.get(url)

def test_example(api_client):
    """api_client = Unauthenticated API client"""
    response = api_client.get(url)  # Might get 403 if endpoint requires auth
```

### Model Factories
```python
def test_example(sample_deployment_intent, sample_cab_request, sample_evidence_pack, sample_event):
    """These fixtures create test data in database"""
    # sample_deployment_intent already created
    # sample_cab_request already created
    # sample_evidence_pack already created
    # sample_event already created
    
    # Use them:
    assert sample_deployment_intent.app_name is not None
```

### Mocks
```python
def test_example(mock_http_session, mock_circuit_breaker, mock_entra_id):
    """Use these to mock external services"""
    mock_http_session.get.return_value = ...
    mock_circuit_breaker.is_closed.return_value = True
```

---

## Priority Order for Fixing Tests

### Tier 1 (High Impact - Fix First)
1. URL routing in view tests (~80 tests fail due to this)
2. Authentication patterns in protected endpoints (~40 tests)

### Tier 2 (Medium Impact)
3. Request/response schema validation (~30 tests)
4. Async task tests (~10 tests)

### Tier 3 (Lower Impact - Fix Last)
5. Integration/E2E tests (~15 tests)
6. Edge case/error handling tests (~15 tests)

---

## Success Criteria

✅ **Goal**: 400+ tests passing (75%+)

### Phase P4-2 Success
- [ ] All URL routing issues fixed
- [ ] Endpoint contracts verified
- [ ] 80+ tests passing (improvement from current)
- [ ] No 404 errors in test output

### Phase P4-3 Success
- [ ] Integration tests working
- [ ] Multi-module workflows validated
- [ ] Event tracking working

### Phase P4-4 Success
- [ ] Async task tests passing
- [ ] Background jobs working
- [ ] Error handling validated

### Phase P4 Complete
- [ ] 450+ tests passing (84%+)
- [ ] Coverage ≥90%
- [ ] All quality gates passing
- [ ] Ready for P5 (Security & Compliance)

---

## Resources

### Key Files to Reference
- `backend/conftest.py` - All fixtures defined here
- `docs/architecture/testing-standards.md` - Testing patterns
- `docs/api/` - API endpoint specifications (if available)

### Django/DRF Testing Docs
- https://docs.djangoproject.com/en/5.0/topics/testing/
- https://www.django-rest-framework.org/api-guide/testing/

### pytest-django Docs
- https://pytest-django.readthedocs.io/

---

**Next Action**: Pick the first failing test, identify the issue, and fix it using the patterns above. The fixtures are ready - tests just need endpoint reference updates!

**Estimated Time to 400+ Passing**: 3-4 hours with focused effort on URL routing fixes.
