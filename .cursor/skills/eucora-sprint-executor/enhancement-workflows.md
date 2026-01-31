# Enhancement Workflows

Detailed implementation workflows for each Phase 2 enhancement.

---

## E3: Comprehensive RBAC (Sprint 1-2)

**Spec**: `docs/planning/12-comprehensive-rbac.md`

### Backend Tasks

```
☐ Create backend/apps/rbac/ Django app
☐ Define models:
  - Role (name, description, is_system, permissions M2M)
  - Permission (resource, action, description)
  - UserRole (user FK, role FK, scope_type, scope_id)
  - PermissionAuditLog (user, action, target, changes, timestamp)
☐ Create migrations
☐ Seed 9 default roles:
  - platform_admin, application_manager, portfolio_manager
  - packaging_engineer, license_manager, cab_approver
  - security_reviewer, publisher, auditor
☐ Seed permissions (50+ resource:action pairs)
☐ Implement decorators:
  - @require_permission(permission_string)
  - @scope_to_user_resources
☐ Implement RBACViewSetMixin
☐ Add RBAC to ALL existing ViewSets
☐ Write tests (≥90% coverage)
```

### Frontend Tasks

```
☐ Create types in frontend/src/types/rbac.ts
☐ Create hooks:
  - usePermission()
  - useRoles()
  - useUserRoles()
☐ Create components:
  - PermissionGate
  - ProtectedRoute
  - RoleSelector
  - ScopeConfigurator
☐ Update UsersTab with role management
☐ Create RoleManagement page (admin only)
☐ Add ROUTE_GUARDS to all routes
☐ Run TypeScript check
```

### APIs

```
GET/POST /api/rbac/roles/
GET/PUT/DELETE /api/rbac/roles/{id}/
GET/POST /api/rbac/permissions/
GET/POST /api/rbac/user-roles/
GET /api/rbac/my-permissions/
POST /api/rbac/check-permission/
```

---

## E2: Storage Configuration (Sprint 1-2)

**Spec**: `docs/planning/11-storage-configuration.md`

### Backend Tasks

```
☐ Create backend/apps/storage/ Django app
☐ Define models:
  - StorageProvider (name, provider_type, is_primary, is_active)
  - MinIOConfig (endpoint, access_key, secret_key, bucket, use_ssl)
  - AWSS3Config (region, access_key, secret_key, bucket, endpoint)
  - AzureBlobConfig (account_name, account_key, container, connection_string)
  - StorageMetrics (provider FK, total_size, used_size, object_count)
☐ Create migrations
☐ Implement StorageBackend abstract interface:
  - upload(key, data, content_type)
  - download(key)
  - delete(key)
  - exists(key)
  - list_objects(prefix)
  - get_presigned_url(key, expires_in)
☐ Implement MinIOBackend
☐ Implement AWSS3Backend
☐ Implement AzureBlobBackend
☐ Implement StorageService (unified, failover)
☐ Implement connection testing
☐ Write tests (≥90% coverage)
```

### Frontend Tasks

```
☐ Create types in frontend/src/types/storage.ts
☐ Create hooks:
  - useStorageProviders()
  - useStorageHealth()
☐ Create components:
  - StorageSettingsTab
  - ProviderConfigForm (MinIO, AWS, Azure variants)
  - ConnectionTestButton
  - StorageMetricsCard
☐ Add Storage tab to Settings page
☐ Run TypeScript check
```

### APIs

```
GET/POST /api/storage/providers/
GET/PUT/DELETE /api/storage/providers/{id}/
POST /api/storage/providers/{id}/test/
GET /api/storage/providers/{id}/health/
GET /api/storage/providers/{id}/metrics/
POST /api/storage/upload/
GET /api/storage/download/{key}/
DELETE /api/storage/delete/{key}/
```

---

## E7: Vector Storage - pgvector (Sprint 3-4)

**Spec**: `docs/planning/16-vector-storage-pgvector.md`

### Prerequisites

```
☐ E2 (Storage) must be complete
☐ PostgreSQL with pgvector extension
```

### Backend Tasks

```
☐ Enable pgvector: CREATE EXTENSION IF NOT EXISTS vector;
☐ Create backend/apps/knowledge/ Django app
☐ Define models:
  - EmbeddingConfig (provider, model_name, dimensions, api_key, is_default)
  - KnowledgeVector (source_type, source_id, chunk_index, content, embedding, metadata)
☐ Create HNSW index migration
☐ Implement EmbeddingProvider interface:
  - embed(texts: list[str]) -> list[list[float]]
☐ Implement OpenAIEmbeddingProvider
☐ Implement CohereEmbeddingProvider
☐ Implement LocalEmbeddingProvider (sentence-transformers)
☐ Implement EmbeddingService (factory pattern)
☐ Implement KnowledgeIndexingPipeline:
  - index_policy_document(document)
  - index_deployment_record(deployment)
☐ Implement KnowledgeRetrievalService:
  - semantic_search(query, limit, filters)
  - hybrid_search(query, keywords, limit)
☐ Write tests (≥90% coverage)
```

### Frontend Tasks

```
☐ Create types in frontend/src/types/knowledge.ts
☐ Create hooks:
  - useEmbeddingConfig()
  - useKnowledgeStats()
☐ Create components:
  - KnowledgeConfigTab
  - EmbeddingModelSelector
  - IndexStatisticsCard
☐ Add Knowledge tab to Settings page
☐ Run TypeScript check
```

### APIs

```
GET/POST /api/knowledge/embedding-config/
PUT /api/knowledge/embedding-config/{id}/
POST /api/knowledge/index/documents/
POST /api/knowledge/index/deployments/
POST /api/knowledge/search/
GET /api/knowledge/stats/
```

---

## E1: Document Management & RAG (Sprint 3-4)

**Spec**: `docs/planning/10-document-management-rag.md`

### Prerequisites

```
☐ E7 (pgvector) must be complete
☐ E2 (Storage) must be complete
```

### Backend Tasks

```
☐ Create backend/apps/policy_documents/ Django app
☐ Define models:
  - DocumentCategory (name, description, color, icon)
  - PolicyDocument (title, category FK, file_path, file_type, version, status, metadata)
  - DocumentChunk (document FK, chunk_index, content, embedding, start_offset, end_offset)
☐ Create migrations
☐ Implement text extraction:
  - extract_pdf_text() using pdfplumber
  - extract_docx_text() using python-docx
  - extract_html_text() using BeautifulSoup
☐ Implement SemanticChunker:
  - chunk_document(text, max_tokens, overlap)
☐ Implement DocumentProcessingPipeline (Celery task):
  - store_original()
  - extract_text()
  - chunk_content()
  - generate_embeddings()
☐ Implement PolicyContextRetriever:
  - get_context_for_query(query, categories, limit)
  - get_context_for_agent(agent_type, query)
☐ Write tests (≥90% coverage)
```

### Frontend Tasks

```
☐ Create types in frontend/src/types/policy-documents.ts
☐ Create hooks:
  - usePolicyDocuments()
  - useDocumentCategories()
  - useDocumentUpload()
☐ Create components:
  - PolicyDocumentsPage
  - DocumentLibrary
  - UploadDialog (drag-drop)
  - DocumentCard
  - DocumentDetailDialog
  - CategoryFilter
☐ Add route /admin/documents
☐ Run TypeScript check
```

### APIs

```
GET/POST /api/policy-documents/categories/
GET/POST /api/policy-documents/
GET/PUT/DELETE /api/policy-documents/{id}/
POST /api/policy-documents/{id}/upload/
GET /api/policy-documents/{id}/download/
POST /api/policy-documents/{id}/reprocess/
POST /api/policy-documents/search/
```

---

## E8: AI Agent Workflows (Sprint 5-6)

**Spec**: `docs/planning/17-ai-agent-workflows.md`

### Prerequisites

```
☐ E1 (Document/RAG) must be complete
☐ E3 (RBAC) must be complete
☐ E7 (pgvector) must be complete
```

### Backend Tasks

```
☐ Extend backend/apps/ai_agents/ app
☐ Define models:
  - WorkflowDefinition (agent_type, name, steps JSON, policy_requirements, risk_level)
  - WorkflowExecution (workflow FK, user FK, status, started_at, completed_at, context)
  - WorkflowStep (execution FK, step_index, name, status, input, output, llm_request, llm_response, requires_approval, approved_by, approved_at)
☐ Create migrations
☐ Implement WorkflowExecutor:
  - start_workflow(agent_type, user, context)
  - execute_step(execution, step_index)
  - check_approval_required(step, risk_level)
  - build_prompt_with_policy_context(step, context)
☐ Define workflows for all agent types:
  - packaging_assistant
  - deployment_advisor
  - license_reconciliation
  - incident_classifier
  - remediation_advisor
☐ Implement R1/R2/R3 classification
☐ Implement approval gates
☐ Add WebSocket for real-time updates
☐ Write tests (≥90% coverage)
```

### Frontend Tasks

```
☐ Create types in frontend/src/types/workflows.ts
☐ Create hooks:
  - useWorkflowExecution()
  - useWorkflowWebSocket()
☐ Create components:
  - WorkflowExecutionView
  - StepProgress
  - CurrentStepDetail
  - ApprovalGateView
  - PolicyContextPanel
  - WorkflowHistory
☐ Update AIAgentHub.tsx to use workflow execution
☐ Run TypeScript check
```

### APIs

```
GET /api/ai-agents/workflows/
GET /api/ai-agents/workflows/{id}/
POST /api/ai-agents/workflows/{id}/start/
GET /api/ai-agents/executions/{id}/
POST /api/ai-agents/executions/{id}/steps/{step_index}/approve/
POST /api/ai-agents/executions/{id}/steps/{step_index}/reject/
POST /api/ai-agents/executions/{id}/cancel/
WS /ws/ai-agents/executions/{id}/
```

---

## E5: Application Policy UI (Sprint 7-8)

**Spec**: `docs/planning/14-application-policy-ui.md`

### Prerequisites

```
☐ E3 (RBAC) must be complete
```

### Backend Tasks

```
☐ Create backend/apps/application_policies/ Django app
☐ Define models:
  - ApplicationPolicy (application FK, name, version, is_active)
  - PolicySetting (policy FK, category, setting_key, setting_value, platform)
  - PolicyTemplate (name, description, category, settings JSON, is_system)
☐ Create migrations
☐ Seed policy templates:
  - Enterprise Required
  - Security-Critical
  - Self-Service Optional
  - Developer Tools
  - Restricted Software
☐ Implement PolicyTranslator:
  - translate_to_intune(policy)
  - translate_to_jamf(policy)
  - translate_to_sccm(policy)
☐ Write tests (≥90% coverage)
```

### Frontend Tasks

```
☐ Create types in frontend/src/types/application-policies.ts
☐ Create hooks:
  - useApplicationPolicies()
  - usePolicyTemplates()
☐ Create components:
  - PolicyConfigurationPage
  - PolicySettingsForm
  - PolicyCategorySection
  - TemplatePicker
  - PlatformMappingPreview
☐ Integrate with DeploymentWizard
☐ Run TypeScript check
```

### APIs

```
GET/POST /api/application-policies/templates/
GET/POST /api/application-policies/
GET/PUT/DELETE /api/application-policies/{id}/
POST /api/application-policies/{id}/apply-template/
POST /api/application-policies/{id}/validate/
GET /api/application-policies/{id}/preview-mapping/
```

---

## E6: Application Stack UX (Sprint 7-8)

**Spec**: `docs/planning/15-application-stack-ux.md`

### Prerequisites

```
☐ E5 (Policy UI) must be complete
```

### Backend Tasks

```
☐ Extend backend/apps/application_portfolio/ or deployments app
☐ Add API endpoints:
  - GET /api/stack/ (hierarchical app → version → deployment → ring)
  - GET /api/stack/timeline/
  - POST /api/stack/actions/promote/
  - POST /api/stack/actions/pause/
  - POST /api/stack/actions/rollback/
☐ Add WebSocket for real-time updates
☐ Write tests (≥90% coverage)
```

### Frontend Tasks

```
☐ Create frontend/src/routes/ApplicationStack.tsx
☐ Create components:
  - TreeView
  - TimelineView
  - GridView
  - DependencyGraph (using ReactFlow)
  - DetailPanel
  - ApplicationDetail
  - VersionDetail
  - DeploymentDetail
  - RingDetail
  - QuickActionsDropdown
  - ViewModeSelector
  - AdvancedFilters
☐ Implement WebSocket for real-time updates
☐ Add route /deployments/stack
☐ Run TypeScript check
```

---

## E4: 1E DEX Integration (Sprint 9-10)

**Spec**: `docs/planning/13-1e-dex-integration.md`

### Prerequisites

```
☐ E2 (Storage) must be complete
```

### Backend Tasks

```
☐ Create backend/apps/integrations/dex/ module
☐ Define models:
  - DEXProvider (provider_type, config JSON, is_active, last_sync)
  - DEXDeviceMetrics (device_id, dex_score, boot_time, app_responsiveness, sentiment, carbon_footprint, power_consumption, synced_at)
  - DEXAggregateMetrics (date, avg_dex_score, avg_boot_time, total_carbon, device_count)
☐ Create migrations
☐ Implement OneEAPIClient:
  - authenticate() with NTLM/Basic
  - get_device_metrics(device_ids)
  - get_aggregate_metrics(date_range)
  - handle throttling and pagination
☐ Implement MockDEXClient (for dev/demo)
☐ Implement DEXSyncService
☐ Add Celery task for periodic sync
☐ Write tests (≥90% coverage)
```

### Frontend Tasks

```
☐ Create types in frontend/src/types/dex.ts
☐ Create hooks:
  - useDEXMetrics()
  - useDEXConfig()
☐ Enhance DEXDashboard.tsx:
  - Real-time DEX score gauge
  - Boot time histogram
  - User sentiment pie chart
  - Carbon footprint trends
  - Device health heatmap
☐ Add 1E configuration to Settings > Integrations
☐ Run TypeScript check
```

### APIs

```
GET/POST /api/integrations/dex/config/
POST /api/integrations/dex/test-connection/
POST /api/integrations/dex/sync/
GET /api/integrations/dex/metrics/
GET /api/integrations/dex/metrics/aggregate/
GET /api/integrations/dex/devices/{id}/
```

---

## E9: PowerShell Production Audit (Sprint 9-10)

**Spec**: `docs/planning/18-powershell-production-audit.md`

### Audit Tasks

```
☐ Audit CLI commands (scripts/cli/):
  - eucora-cli.ps1
  - Deploy-Package.ps1
  - Get-DeploymentStatus.ps1
  - ... (13 scripts total)

☐ Audit connectors (scripts/connectors/):
  - IntuneConnector.ps1
  - JamfConnector.ps1
  - SccmConnector.ps1
  - ... (7 scripts total)

☐ Audit utilities (scripts/utils/):
  - logging utilities
  - error handlers
  - ... (10+ scripts)

☐ Audit validation (scripts/validation/):
  - 4 validation scripts
```

### Hardening Tasks

```
☐ Replace hardcoded values with config file
☐ Create scripts/config/production.json
☐ Standardize error handling pattern
☐ Standardize logging pattern (structured JSON)
☐ Implement secure credential retrieval
☐ Add retry logic with exponential backoff
☐ Add rate limit handling
☐ Add Retry-After header support
☐ Add idempotency keys
☐ Add correlation IDs to all operations
```

### Testing Tasks

```
☐ Create Pester unit tests for all scripts
☐ Create integration tests for connectors
☐ Create security tests (no secrets in output)
☐ Document test coverage
```
