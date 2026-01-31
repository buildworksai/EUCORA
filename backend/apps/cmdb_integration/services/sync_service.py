# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CMDB Synchronization Service.

Orchestrates data synchronization between source systems and CMDB,
including comparison, discrepancy detection, and updates.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.utils import timezone

from ..models import CMDBConnection, CMDBDataQualityReport, CMDBDiscrepancy, CMDBSyncRecord, CMDBTableMapping
from .servicenow_client import MockServiceNowCMDBClient, ServiceNowCMDBClient
from .validation_engine import CMDBValidationEngine, RecordValidationResult

logger = logging.getLogger(__name__)


class CMDBSyncService:
    """
    Orchestrates CMDB synchronization operations.

    Responsibilities:
    - Compare source data with CMDB state
    - Detect and categorize discrepancies
    - Apply validated updates
    - Generate quality reports
    """

    def __init__(
        self,
        connection: CMDBConnection,
        use_mock: bool = False,
    ):
        """
        Initialize sync service.

        Args:
            connection: CMDB connection configuration
            use_mock: Use mock client for development
        """
        self.connection = connection
        self.use_mock = use_mock or getattr(settings, "CMDB_USE_MOCK", True)

        if self.use_mock:
            self.client = MockServiceNowCMDBClient(connection)
        else:
            self.client = ServiceNowCMDBClient(connection)

        self.validation_engine: Optional[CMDBValidationEngine] = None

    async def initialize(self) -> None:
        """Initialize async components."""
        self.validation_engine = await CMDBValidationEngine.create()

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.close()

    async def run_sync(
        self,
        sync_record: CMDBSyncRecord,
        source_data: Dict[str, List[Dict[str, Any]]],
        tables: Optional[List[str]] = None,
    ) -> CMDBSyncRecord:
        """
        Run synchronization process.

        Args:
            sync_record: Sync record to track progress
            source_data: Data from source systems, keyed by table
            tables: Optional list of tables to sync (all if None)

        Returns:
            Updated sync record
        """
        try:
            sync_record.status = CMDBSyncRecord.Status.RUNNING
            sync_record.started_at = timezone.now()
            await sync_record.asave()

            # Get enabled mappings
            mappings = await self._get_enabled_mappings(tables)

            total_processed = 0
            total_created = 0
            total_updated = 0
            total_skipped = 0
            total_validation_errors = 0
            all_errors = []

            for mapping in mappings:
                table = mapping.cmdb_table
                source_type = mapping.source_type

                # Get source data for this mapping
                table_source_data = source_data.get(source_type, source_data.get(table, []))

                if not table_source_data:
                    logger.info(f"No source data for {source_type}/{table}")
                    continue

                # Run comparison
                stats, errors = await self._sync_table(
                    sync_record=sync_record,
                    mapping=mapping,
                    source_records=table_source_data,
                )

                total_processed += stats.get("processed", 0)
                total_created += stats.get("created", 0)
                total_updated += stats.get("updated", 0)
                total_skipped += stats.get("skipped", 0)
                total_validation_errors += stats.get("validation_errors", 0)
                all_errors.extend(errors)

            # Update sync record
            sync_record.records_processed = total_processed
            sync_record.records_created = total_created
            sync_record.records_updated = total_updated
            sync_record.records_skipped = total_skipped
            sync_record.validation_errors = total_validation_errors
            sync_record.errors = all_errors
            sync_record.status = CMDBSyncRecord.Status.COMPLETED
            sync_record.completed_at = timezone.now()

            # Calculate quality score
            quality_report = await self._generate_quality_report(sync_record)
            sync_record.quality_score = quality_report.overall_score

            await sync_record.asave()

            # Update connection last sync
            self.connection.last_sync = timezone.now()
            self.connection.last_sync_status = "success"
            await self.connection.asave()

            return sync_record

        except Exception as e:
            logger.exception(f"Sync failed: {e}")
            sync_record.status = CMDBSyncRecord.Status.FAILED
            sync_record.errors = [{"error": str(e), "type": "sync_failure"}]
            sync_record.completed_at = timezone.now()
            await sync_record.asave()

            self.connection.last_sync_status = "failed"
            await self.connection.asave()

            raise

    async def _get_enabled_mappings(
        self,
        tables: Optional[List[str]] = None,
    ) -> List[CMDBTableMapping]:
        """Get enabled table mappings."""
        query = CMDBTableMapping.objects.filter(
            connection=self.connection,
            sync_enabled=True,
        )

        if tables:
            query = query.filter(cmdb_table__in=tables)

        return [mapping async for mapping in query.order_by("priority")]

    async def _sync_table(
        self,
        sync_record: CMDBSyncRecord,
        mapping: CMDBTableMapping,
        source_records: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """
        Sync a single table.

        Args:
            sync_record: Parent sync record
            mapping: Table mapping configuration
            source_records: Records from source system

        Returns:
            Tuple of (stats dict, errors list)
        """
        table = mapping.cmdb_table
        logger.info(f"Syncing {len(source_records)} records to {table}")

        stats = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "validation_errors": 0,
        }
        errors = []

        # Get current CMDB data
        cmdb_records = await self.client.query_all_cis(table)
        cmdb_by_key = self._build_lookup_index(cmdb_records, mapping)

        for source_record in source_records:
            stats["processed"] += 1

            try:
                # Map source fields to CMDB fields
                mapped_record = self._map_fields(source_record, mapping)

                # Find matching CMDB record
                lookup_key = self._get_lookup_key(source_record, mapping)
                existing_record = cmdb_by_key.get(lookup_key)

                # Validate record
                if self.validation_engine:
                    validation_result = self.validation_engine.validate_record(mapped_record, table)

                    if validation_result.has_critical_issues:
                        stats["validation_errors"] += 1
                        await self._create_validation_discrepancies(sync_record, validation_result, mapping.source_type)
                        continue

                if existing_record:
                    # Compare and detect discrepancies
                    discrepancies = self._compare_records(
                        source_record=mapped_record,
                        cmdb_record=existing_record,
                        table=table,
                        source_type=mapping.source_type,
                    )

                    if discrepancies:
                        for disc in discrepancies:
                            await CMDBDiscrepancy.objects.acreate(
                                sync_record=sync_record,
                                ci_sys_id=existing_record.get("sys_id", ""),
                                ci_name=existing_record.get("name", "Unknown"),
                                ci_class=table,
                                discrepancy_type=disc["type"],
                                field_name=disc.get("field", ""),
                                source_value=disc.get("source_value"),
                                cmdb_value=disc.get("cmdb_value"),
                                source_system=mapping.source_type,
                                recommended_action=disc.get("action", "review"),
                                confidence_score=disc.get("confidence", 0.8),
                                status=CMDBDiscrepancy.Status.PENDING,
                            )

                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    # New record - create discrepancy for review
                    await CMDBDiscrepancy.objects.acreate(
                        sync_record=sync_record,
                        ci_sys_id="",
                        ci_name=mapped_record.get("name", "Unknown"),
                        ci_class=table,
                        discrepancy_type=CMDBDiscrepancy.DiscrepancyType.MISSING,
                        source_value=str(mapped_record),
                        source_system=mapping.source_type,
                        recommended_action=CMDBDiscrepancy.RecommendedAction.CREATE,
                        confidence_score=0.9,
                        status=CMDBDiscrepancy.Status.PENDING,
                    )
                    stats["created"] += 1

            except Exception as e:
                logger.error(f"Error processing record: {e}")
                errors.append(
                    {
                        "record": str(source_record)[:200],
                        "error": str(e),
                    }
                )

        return stats, errors

    def _build_lookup_index(
        self,
        records: List[Dict[str, Any]],
        mapping: CMDBTableMapping,
    ) -> Dict[str, Dict[str, Any]]:
        """Build lookup index for CMDB records."""
        index = {}
        key_fields = mapping.field_mappings.get("_key_fields", ["name"])

        for record in records:
            key = self._get_record_key(record, key_fields)
            if key:
                index[key] = record

        return index

    def _get_lookup_key(
        self,
        record: Dict[str, Any],
        mapping: CMDBTableMapping,
    ) -> str:
        """Get lookup key for source record."""
        key_fields = mapping.field_mappings.get("_key_fields", ["name"])
        # Map source key fields to their mapped names
        mapped_key_fields = []
        for field in key_fields:
            mapped_field = mapping.field_mappings.get(field, field)
            mapped_key_fields.append(mapped_field)

        return self._get_record_key(record, key_fields)

    def _get_record_key(
        self,
        record: Dict[str, Any],
        key_fields: List[str],
    ) -> str:
        """Generate unique key from record fields."""
        key_parts = []
        for field in key_fields:
            value = record.get(field, "")
            if value:
                key_parts.append(str(value).lower())
        return "|".join(key_parts)

    def _map_fields(
        self,
        source_record: Dict[str, Any],
        mapping: CMDBTableMapping,
    ) -> Dict[str, Any]:
        """Map source fields to CMDB fields."""
        mapped = {}

        for source_field, cmdb_field in mapping.field_mappings.items():
            if source_field.startswith("_"):
                continue  # Skip metadata fields

            if source_field in source_record:
                mapped[cmdb_field] = source_record[source_field]

        return mapped

    def _compare_records(
        self,
        source_record: Dict[str, Any],
        cmdb_record: Dict[str, Any],
        table: str,
        source_type: str,
    ) -> List[Dict[str, Any]]:
        """Compare source and CMDB records for discrepancies."""
        discrepancies = []

        for field, source_value in source_record.items():
            cmdb_value = cmdb_record.get(field)

            # Skip empty source values
            if source_value is None or source_value == "":
                continue

            # Normalize for comparison
            source_str = str(source_value).strip().lower()
            cmdb_str = str(cmdb_value).strip().lower() if cmdb_value else ""

            if source_str != cmdb_str:
                discrepancies.append(
                    {
                        "type": CMDBDiscrepancy.DiscrepancyType.MISMATCH,
                        "field": field,
                        "source_value": str(source_value)[:500],
                        "cmdb_value": str(cmdb_value)[:500] if cmdb_value else None,
                        "action": CMDBDiscrepancy.RecommendedAction.UPDATE,
                        "confidence": 0.85,
                    }
                )

        return discrepancies

    async def _create_validation_discrepancies(
        self,
        sync_record: CMDBSyncRecord,
        validation_result: RecordValidationResult,
        source_type: str,
    ) -> None:
        """Create discrepancies from validation errors."""
        for error in validation_result.errors:
            await CMDBDiscrepancy.objects.acreate(
                sync_record=sync_record,
                ci_sys_id=validation_result.ci_sys_id,
                ci_name=validation_result.ci_name,
                ci_class=validation_result.ci_class,
                discrepancy_type=CMDBDiscrepancy.DiscrepancyType.INCOMPLETE,
                field_name=error.field_name or "",
                source_value=error.actual_value,
                cmdb_value=error.expected_value,
                source_system=source_type,
                recommended_action=CMDBDiscrepancy.RecommendedAction.REVIEW,
                confidence_score=0.7,
                status=CMDBDiscrepancy.Status.PENDING,
            )

    async def _generate_quality_report(
        self,
        sync_record: CMDBSyncRecord,
    ) -> CMDBDataQualityReport:
        """Generate quality report for sync."""
        # Count discrepancies by type
        discrepancy_counts = {}
        async for disc in sync_record.discrepancies.all():
            dtype = disc.discrepancy_type
            discrepancy_counts[dtype] = discrepancy_counts.get(dtype, 0) + 1

        # Calculate scores
        total_cis = sync_record.records_processed
        cis_with_issues = sum(discrepancy_counts.values())

        # Simple scoring - in production, use more sophisticated metrics
        completeness_score = 100.0 * (1 - discrepancy_counts.get("missing", 0) / max(total_cis, 1))
        accuracy_score = 100.0 * (1 - discrepancy_counts.get("mismatch", 0) / max(total_cis, 1))
        consistency_score = 100.0 * (1 - discrepancy_counts.get("duplicate", 0) / max(total_cis, 1))
        timeliness_score = 100.0 * (1 - discrepancy_counts.get("stale", 0) / max(total_cis, 1))

        overall_score = (completeness_score + accuracy_score + consistency_score + timeliness_score) / 4

        report = await CMDBDataQualityReport.objects.acreate(
            connection=self.connection,
            sync_record=sync_record,
            overall_score=max(0, min(100, overall_score)),
            completeness_score=max(0, min(100, completeness_score)),
            accuracy_score=max(0, min(100, accuracy_score)),
            consistency_score=max(0, min(100, consistency_score)),
            timeliness_score=max(0, min(100, timeliness_score)),
            total_cis=total_cis,
            cis_with_issues=cis_with_issues,
            critical_issues=discrepancy_counts.get("error", 0),
            warnings=sync_record.validation_errors,
            table_scores={},
        )

        return report

    async def apply_discrepancy(
        self,
        discrepancy: CMDBDiscrepancy,
    ) -> bool:
        """
        Apply a single discrepancy fix to CMDB.

        Args:
            discrepancy: Discrepancy to apply

        Returns:
            True if applied successfully
        """
        action = discrepancy.recommended_action
        table = discrepancy.ci_class

        try:
            if action == CMDBDiscrepancy.RecommendedAction.CREATE:
                # Parse source_value as record data
                import json

                record_data = json.loads(discrepancy.source_value) if discrepancy.source_value else {}
                await self.client.create_ci(table, record_data)

            elif action == CMDBDiscrepancy.RecommendedAction.UPDATE:
                if discrepancy.ci_sys_id and discrepancy.field_name:
                    await self.client.update_ci(
                        table,
                        discrepancy.ci_sys_id,
                        {discrepancy.field_name: discrepancy.source_value},
                    )

            elif action == CMDBDiscrepancy.RecommendedAction.DELETE:
                if discrepancy.ci_sys_id:
                    await self.client.delete_ci(table, discrepancy.ci_sys_id)

            discrepancy.status = CMDBDiscrepancy.Status.APPLIED
            discrepancy.resolved_at = timezone.now()
            await discrepancy.asave()

            return True

        except Exception as e:
            logger.error(f"Failed to apply discrepancy {discrepancy.id}: {e}")
            discrepancy.resolution_notes = f"Apply failed: {str(e)}"
            await discrepancy.asave()
            return False
