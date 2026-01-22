/**
 * API type definitions (generated from Django OpenAPI schema).
 * 
 * Generate command: npx openapi-typescript http://localhost:8000/api/schema/ -o src/types/api.ts
 */

export interface DeploymentIntent {
    id: number;
    correlation_id: string;
    app_name: string;
    version: string;
    target_ring: 'LAB' | 'CANARY' | 'PILOT' | 'DEPARTMENT' | 'GLOBAL';
    status: 'PENDING' | 'AWAITING_CAB' | 'APPROVED' | 'REJECTED' | 'DEPLOYING' | 'COMPLETED' | 'FAILED' | 'ROLLED_BACK';
    risk_score: number | null;
    requires_cab_approval: boolean;
    created_at: string;
    updated_at: string;
}

export interface CABApproval {
    id: number;
    deployment_intent: number;
    decision: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CONDITIONAL';
    approver: string | null;
    comments: string;
    conditions: string[];
    submitted_at: string;
    reviewed_at: string | null;
}

export interface EvidencePack {
    id: number;
    correlation_id: string;
    artifact_hash: string;
    artifact_signature: string;
    sbom_data: Record<string, unknown>;
    vulnerability_scan_results: Record<string, unknown>;
    scan_policy_decision: 'PASS' | 'FAIL' | 'EXCEPTION';
    rollback_plan: Record<string, unknown>;
    created_at: string;
}

export interface DeploymentEvent {
    id: number;
    correlation_id: string;
    event_type: string;
    event_data: Record<string, unknown>;
    actor: string;
    created_at: string;}