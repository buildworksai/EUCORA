# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Packaging factory service layer with MOCK SBOM/scan for MVP.

NOTE: Real SBOM generation and vulnerability scanning deferred to post-launch.
Current implementation uses mocks with proper interfaces.
"""
import hashlib
import uuid
from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.core.structured_logging import StructuredLogger

from .models import PackagingPipeline, PackagingStageLog

User = get_user_model()


class PackagingFactoryService:
    """
    Service for packaging pipeline orchestration.

    Pipeline stages: INTAKE → BUILD → SIGN → SBOM → SCAN → POLICY → STORE
    """

    def __init__(self):
        """Initialize service with logger."""
        self.logger = StructuredLogger(__name__)

    def create_pipeline(
        self,
        package_name: str,
        package_version: str,
        platform: str,
        package_type: str,
        source_artifact_url: str,
        created_by: User,
        source_repo: Optional[str] = None,
        source_commit: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> PackagingPipeline:
        """
        Create new packaging pipeline.

        Args:
            package_name: Package name
            package_version: Package version
            platform: Target platform (windows, macos, linux)
            package_type: Package type (MSI, PKG, DEB, etc.)
            source_artifact_url: URL to source artifact
            created_by: User creating pipeline
            source_repo: Source repository URL
            source_commit: Source commit SHA
            correlation_id: Correlation ID for tracking

        Returns:
            Created pipeline instance
        """
        # Generate source artifact hash (mock for MVP)
        source_hash = self._mock_hash_artifact(source_artifact_url)

        pipeline = PackagingPipeline.objects.create(
            package_name=package_name,
            package_version=package_version,
            platform=platform,
            package_type=package_type,
            source_artifact_url=source_artifact_url,
            source_artifact_hash=source_hash,
            source_repo=source_repo,
            source_commit=source_commit,
            created_by=created_by,
            status="PENDING",
            correlation_id=correlation_id or str(uuid.uuid4()),
        )

        self.logger.info(
            f"Created packaging pipeline: {pipeline.id}",
            extra={
                "pipeline_id": str(pipeline.id),
                "package_name": package_name,
                "package_version": package_version,
                "platform": platform,
                "correlation_id": pipeline.correlation_id,
            },
        )

        return pipeline

    def execute_pipeline(self, pipeline_id: str, correlation_id: Optional[str] = None) -> PackagingPipeline:
        """
        Execute full packaging pipeline.

        Args:
            pipeline_id: Pipeline ID
            correlation_id: Correlation ID for tracking

        Returns:
            Updated pipeline instance
        """
        pipeline = PackagingPipeline.objects.get(id=pipeline_id)
        corr_id = correlation_id or pipeline.correlation_id

        try:
            # Stage 1: Intake
            self._execute_stage(pipeline, "INTAKE", corr_id)
            self._stage_intake(pipeline, corr_id)

            # Stage 2: Build
            self._execute_stage(pipeline, "BUILD", corr_id)
            self._stage_build(pipeline, corr_id)

            # Stage 3: Sign
            self._execute_stage(pipeline, "SIGN", corr_id)
            self._stage_sign(pipeline, corr_id)

            # Stage 4: SBOM Generation
            self._execute_stage(pipeline, "SBOM", corr_id)
            self._stage_sbom(pipeline, corr_id)

            # Stage 5: Vulnerability Scan
            self._execute_stage(pipeline, "SCAN", corr_id)
            self._stage_scan(pipeline, corr_id)

            # Stage 6: Policy Decision
            self._execute_stage(pipeline, "POLICY", corr_id)
            self._stage_policy(pipeline, corr_id)

            # Stage 7: Store
            self._execute_stage(pipeline, "STORE", corr_id)
            self._stage_store(pipeline, corr_id)

            # Mark completed
            pipeline.status = "COMPLETED"
            pipeline.completed_at = timezone.now()
            pipeline.save()

            self.logger.info(
                f"Pipeline completed: {pipeline.id}",
                extra={
                    "pipeline_id": str(pipeline.id),
                    "duration_seconds": pipeline.duration_seconds,
                    "correlation_id": corr_id,
                },
            )

        except Exception as e:
            pipeline.status = "FAILED"
            pipeline.error_message = str(e)
            pipeline.error_stage = pipeline.current_stage
            pipeline.save()

            self.logger.error(
                f"Pipeline failed: {pipeline.id}",
                extra={
                    "pipeline_id": str(pipeline.id),
                    "error": str(e),
                    "stage": pipeline.current_stage,
                    "correlation_id": corr_id,
                },
            )
            raise

        return pipeline

    def _execute_stage(self, pipeline: PackagingPipeline, stage: str, correlation_id: str):
        """Update pipeline status for stage execution."""
        pipeline.status = stage
        pipeline.current_stage = stage
        pipeline.save()

    def _stage_intake(self, pipeline: PackagingPipeline, correlation_id: str):
        """
        Intake stage: Validate source artifact.

        MOCK: Just logs and validates basic metadata.
        """
        log = PackagingStageLog.objects.create(
            pipeline=pipeline,
            stage_name="INTAKE",
            status="SUCCESS",
            output=f"Validated source artifact: {pipeline.source_artifact_url}",
            metadata={"source_hash": pipeline.source_artifact_hash, "package_type": pipeline.package_type},
        )
        log.completed_at = timezone.now()
        log.save()

    def _stage_build(self, pipeline: PackagingPipeline, correlation_id: str):
        """
        Build stage: Build package.

        MOCK: Simulates build process, generates output artifact URL.
        """
        # Mock build output
        output_url = (
            f"s3://artifacts/{pipeline.package_name}/{pipeline.package_version}/package.{pipeline.package_type.lower()}"
        )
        output_hash = self._mock_hash_artifact(output_url)

        pipeline.output_artifact_url = output_url
        pipeline.output_artifact_hash = output_hash
        pipeline.builder_identity = f"build-agent-{uuid.uuid4().hex[:8]}"
        pipeline.build_id = str(uuid.uuid4())
        pipeline.save()

        log = PackagingStageLog.objects.create(
            pipeline=pipeline,
            stage_name="BUILD",
            status="SUCCESS",
            output=f"Built package: {output_url}",
            metadata={"output_hash": output_hash, "build_id": pipeline.build_id},
        )
        log.completed_at = timezone.now()
        log.save()

    def _stage_sign(self, pipeline: PackagingPipeline, correlation_id: str):
        """
        Sign stage: Sign package.

        MOCK: Simulates signing with platform-specific certificate.
        """
        # Platform-specific signing certificate
        cert_map = {
            "windows": "Enterprise Code Signing Cert (SHA-256)",
            "macos": "Apple Developer ID Installer Cert",
            "linux": "GPG Signing Key (RSA 4096)",
        }

        pipeline.signing_certificate = cert_map.get(pipeline.platform, "Unknown Platform")
        pipeline.signature_url = f"{pipeline.output_artifact_url}.sig"
        pipeline.signed_at = timezone.now()
        pipeline.save()

        log = PackagingStageLog.objects.create(
            pipeline=pipeline,
            stage_name="SIGN",
            status="SUCCESS",
            output=f"Signed with: {pipeline.signing_certificate}",
            metadata={"certificate": pipeline.signing_certificate, "signature_url": pipeline.signature_url},
        )
        log.completed_at = timezone.now()
        log.save()

    def _stage_sbom(self, pipeline: PackagingPipeline, correlation_id: str):
        """
        SBOM stage: Generate Software Bill of Materials.

        MOCK: Generates mock SBOM in SPDX format.
        Real implementation: Use syft or cyclonedx-cli.
        """
        pipeline.sbom_format = "SPDX-2.3"
        pipeline.sbom_url = f"{pipeline.output_artifact_url}.sbom.json"
        pipeline.sbom_generated_at = timezone.now()
        pipeline.save()

        # Mock SBOM data
        mock_sbom = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": f"SPDXRef-{pipeline.id}",
            "name": pipeline.package_name,
            "documentNamespace": f"https://eucora.example.com/sbom/{pipeline.id}",
            "packages": [
                {
                    "name": pipeline.package_name,
                    "SPDXID": "SPDXRef-Package",
                    "versionInfo": pipeline.package_version,
                    "filesAnalyzed": False,
                }
            ],
        }

        log = PackagingStageLog.objects.create(
            pipeline=pipeline,
            stage_name="SBOM",
            status="SUCCESS",
            output=f"Generated SBOM: {pipeline.sbom_url}",
            metadata={"sbom_format": pipeline.sbom_format, "sbom_url": pipeline.sbom_url, "sbom_data": mock_sbom},
        )
        log.completed_at = timezone.now()
        log.save()

    def _stage_scan(self, pipeline: PackagingPipeline, correlation_id: str):
        """
        Scan stage: Vulnerability scanning.

        MOCK: Generates mock scan results with random vulnerability counts.
        Real implementation: Use trivy, grype, or snyk.
        """
        import random

        # Mock scan results (deterministic based on package name for testing)
        seed = sum(ord(c) for c in pipeline.package_name)
        random.seed(seed)

        pipeline.scan_tool = "trivy-mock-v0.1.0"
        pipeline.critical_count = random.randint(0, 2)
        pipeline.high_count = random.randint(0, 5)
        pipeline.medium_count = random.randint(2, 10)
        pipeline.low_count = random.randint(5, 20)
        pipeline.scan_completed_at = timezone.now()

        # Mock scan results data
        pipeline.scan_results = {
            "scanner": pipeline.scan_tool,
            "scan_time": pipeline.scan_completed_at.isoformat(),
            "target": pipeline.output_artifact_url,
            "summary": {
                "CRITICAL": pipeline.critical_count,
                "HIGH": pipeline.high_count,
                "MEDIUM": pipeline.medium_count,
                "LOW": pipeline.low_count,
            },
            "vulnerabilities": [],  # Empty for mock
        }
        pipeline.save()

        log = PackagingStageLog.objects.create(
            pipeline=pipeline,
            stage_name="SCAN",
            status="SUCCESS",
            output=(
                f"Scan completed: {pipeline.critical_count} Critical, "
                f"{pipeline.high_count} High, {pipeline.medium_count} Medium, "
                f"{pipeline.low_count} Low"
            ),
            metadata=pipeline.scan_results,
        )
        log.completed_at = timezone.now()
        log.save()

    def _stage_policy(self, pipeline: PackagingPipeline, correlation_id: str):
        """
        Policy stage: Determine if package passes policy gates.

        Policy: Block Critical/High vulnerabilities unless exception approved.
        """
        if pipeline.has_blocking_vulnerabilities:
            if pipeline.exception_id:
                # Exception approved
                pipeline.policy_decision = "EXCEPTION"
                pipeline.policy_reason = (
                    f"Blocking vulnerabilities found ({pipeline.critical_count} Critical, "
                    f"{pipeline.high_count} High) but exception {pipeline.exception_id} approved"
                )
            else:
                # Fail - blocking vulnerabilities without exception
                pipeline.policy_decision = "FAIL"
                pipeline.policy_reason = (
                    f"Blocking vulnerabilities found: {pipeline.critical_count} Critical, "
                    f"{pipeline.high_count} High. Exception required."
                )
                pipeline.status = "FAILED"
                pipeline.error_message = pipeline.policy_reason
                pipeline.error_stage = "POLICY"
                pipeline.save()

                log = PackagingStageLog.objects.create(
                    pipeline=pipeline,
                    stage_name="POLICY",
                    status="FAILED",
                    error_message=pipeline.policy_reason,
                    metadata={"critical_count": pipeline.critical_count, "high_count": pipeline.high_count},
                )
                log.completed_at = timezone.now()
                log.save()

                raise ValueError(pipeline.policy_reason)
        else:
            # Pass - no blocking vulnerabilities
            pipeline.policy_decision = "PASS"
            pipeline.policy_reason = "No blocking vulnerabilities found"

        pipeline.save()

        log = PackagingStageLog.objects.create(
            pipeline=pipeline,
            stage_name="POLICY",
            status="SUCCESS",
            output=f"Policy decision: {pipeline.policy_decision} - {pipeline.policy_reason}",
            metadata={"decision": pipeline.policy_decision, "reason": pipeline.policy_reason},
        )
        log.completed_at = timezone.now()
        log.save()

    def _stage_store(self, pipeline: PackagingPipeline, correlation_id: str):
        """
        Store stage: Store artifact in immutable storage.

        MOCK: Simulates storage in MinIO with hash verification.
        Real implementation: Actual MinIO upload with metadata.
        """
        # Mock storage confirmation
        storage_metadata = {
            "bucket": "eucora-artifacts",
            "key": f"{pipeline.package_name}/{pipeline.package_version}/package.{pipeline.package_type.lower()}",
            "hash": pipeline.output_artifact_hash,
            "size_bytes": 1024 * 1024 * 50,  # Mock 50MB
            "stored_at": timezone.now().isoformat(),
        }

        log = PackagingStageLog.objects.create(
            pipeline=pipeline,
            stage_name="STORE",
            status="SUCCESS",
            output=f"Stored artifact: {storage_metadata['bucket']}/{storage_metadata['key']}",
            metadata=storage_metadata,
        )
        log.completed_at = timezone.now()
        log.save()

    def _mock_hash_artifact(self, artifact_url: str) -> str:
        """
        Generate mock SHA-256 hash for artifact.

        Args:
            artifact_url: Artifact URL

        Returns:
            Mock SHA-256 hash (deterministic for testing)
        """
        return hashlib.sha256(artifact_url.encode()).hexdigest()

    def get_pipeline_status(self, pipeline_id: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get pipeline status with stage details.

        Args:
            pipeline_id: Pipeline ID
            correlation_id: Correlation ID for tracking

        Returns:
            Pipeline status dict
        """
        pipeline = PackagingPipeline.objects.get(id=pipeline_id)
        stage_logs = pipeline.stage_logs.all()

        return {
            "pipeline_id": str(pipeline.id),
            "package_name": pipeline.package_name,
            "package_version": pipeline.package_version,
            "platform": pipeline.platform,
            "status": pipeline.status,
            "current_stage": pipeline.current_stage,
            "policy_decision": pipeline.policy_decision,
            "created_at": pipeline.created_at.isoformat(),
            "completed_at": pipeline.completed_at.isoformat() if pipeline.completed_at else None,
            "duration_seconds": pipeline.duration_seconds,
            "stages": [
                {
                    "stage": log.stage_name,
                    "status": log.status,
                    "duration_seconds": log.duration_seconds,
                    "output": log.output,
                }
                for log in stage_logs
            ],
            "vulnerabilities": {
                "critical": pipeline.critical_count,
                "high": pipeline.high_count,
                "medium": pipeline.medium_count,
                "low": pipeline.low_count,
            },
        }
