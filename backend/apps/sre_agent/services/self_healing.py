# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Self-healing service for executing remediation scripts.
"""
import logging
import subprocess
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from django.utils import timezone

from ..models import SelfHealingExecution, SelfHealingRule

logger = logging.getLogger(__name__)


class SelfHealingService:
    """Service for executing self-healing remediation scripts."""

    def __init__(self, base_path: str = "/app"):
        """
        Initialize self-healing service.

        Args:
            base_path: Base path for PowerShell scripts (default: /app for Docker)
        """
        self.base_path = Path(base_path)

    def can_execute(self, rule: SelfHealingRule) -> tuple[bool, Optional[str]]:
        """
        Check if rule can be executed (cooldown and max executions per hour).

        Args:
            rule: Self-healing rule to check

        Returns:
            (can_execute: bool, reason: str | None)
        """
        if not rule.is_active:
            return False, "Rule is not active"

        # Check cooldown period - use Status enum values (lowercase)
        completed_statuses = [
            SelfHealingExecution.Status.COMPLETED,
            SelfHealingExecution.Status.FAILED,
        ]
        recent_execution = (
            SelfHealingExecution.objects.filter(rule=rule, status__in=completed_statuses)
            .order_by("-completed_at")
            .first()
        )

        if recent_execution and recent_execution.completed_at:
            cooldown_end = recent_execution.completed_at + timedelta(minutes=rule.cooldown_minutes)
            if timezone.now() < cooldown_end:
                remaining_minutes = (cooldown_end - timezone.now()).total_seconds() / 60
                return False, f"Cooldown period active. {remaining_minutes:.1f} minutes remaining"

        # Check max executions per hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_count = SelfHealingExecution.objects.filter(
            rule=rule, created_at__gte=one_hour_ago, status__in=completed_statuses
        ).count()

        if recent_count >= rule.max_executions_per_hour:
            return False, f"Max executions per hour ({rule.max_executions_per_hour}) reached"

        return True, None

    def execute_script(self, execution: SelfHealingExecution, rule: SelfHealingRule) -> Dict[str, Any]:
        """
        Execute remediation script for self-healing rule.

        Args:
            execution: Self-healing execution record
            rule: Self-healing rule with script configuration

        Returns:
            {
                'success': bool,
                'stdout': str,
                'stderr': str,
                'exit_code': int
            }
        """
        if rule.script_type != SelfHealingRule.ScriptType.POWERSHELL:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Unsupported script type: {rule.script_type}",
                "exit_code": -1,
            }

        # Determine script path
        # remediation_script can be:
        # 1. Script filename (e.g., "Repair-ServiceHealth.ps1")
        # 2. Full path relative to base_path
        script_name = rule.remediation_script.strip()

        # If it's just a filename, prepend self-healing directory
        if not script_name.startswith("scripts/"):
            script_path = self.base_path / "scripts" / "self-healing" / script_name
        else:
            script_path = self.base_path / script_name

        if not script_path.exists():
            error_msg = f"Script not found: {script_path}"
            logger.error(error_msg, extra={"execution_id": str(execution.id), "rule_id": str(rule.id)})
            return {
                "success": False,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": -1,
            }

        # Build PowerShell command with parameters
        ps_params = [
            "pwsh",
            "-File",
            str(script_path),
            "-CorrelationId",
            str(execution.correlation_id),
        ]

        # Add target_config parameters
        target_config = rule.target_config or {}
        for key, value in target_config.items():
            if value is not None:
                ps_params.extend([f"-{key}", str(value)])

        try:
            logger.info(
                f"Executing self-healing script: {script_path}",
                extra={
                    "execution_id": str(execution.id),
                    "rule_id": str(rule.id),
                    "correlation_id": str(execution.correlation_id),
                },
            )

            # Execute PowerShell script
            result = subprocess.run(
                ps_params,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                check=False,
            )

            success = result.returncode == 0

            logger.info(
                f"Self-healing script execution {'succeeded' if success else 'failed'}",
                extra={
                    "execution_id": str(execution.id),
                    "rule_id": str(rule.id),
                    "correlation_id": str(execution.correlation_id),
                    "exit_code": result.returncode,
                },
            )

            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            error_msg = "Script execution timed out (5 minutes)"
            logger.error(
                error_msg,
                extra={
                    "execution_id": str(execution.id),
                    "rule_id": str(rule.id),
                    "correlation_id": str(execution.correlation_id),
                },
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": -1,
            }
        except Exception as e:
            error_msg = f"Script execution error: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "execution_id": str(execution.id),
                    "rule_id": str(rule.id),
                    "correlation_id": str(execution.correlation_id),
                },
                exc_info=True,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": -1,
            }

    def execute(self, execution: SelfHealingExecution) -> SelfHealingExecution:
        """
        Execute self-healing rule and update execution record.

        Args:
            execution: Self-healing execution record

        Returns:
            Updated execution record
        """
        rule = execution.rule

        # Check if execution is allowed
        can_execute, reason = self.can_execute(rule)
        if not can_execute:
            execution.status = SelfHealingExecution.Status.FAILED
            execution.error_message = reason
            execution.completed_at = timezone.now()
            execution.save()
            return execution

        # Update status to EXECUTING
        execution.status = SelfHealingExecution.Status.EXECUTING
        execution.started_at = timezone.now()
        execution.save()

        # Execute script
        result = self.execute_script(execution, rule)

        # Update execution record
        execution.output = result.get("stdout", "")
        execution.error_message = result.get("stderr", "") if not result.get("success") else None
        execution.status = (
            SelfHealingExecution.Status.COMPLETED if result.get("success") else SelfHealingExecution.Status.FAILED
        )
        execution.completed_at = timezone.now()
        execution.save()

        return execution
