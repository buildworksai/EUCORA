# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Gap Analysis Engine for Discovery Agent.

Identifies license and patch gaps based on discovered applications.
"""
import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.utils import timezone

from ..models import ApplicationVersion, LicenseGap, NormalizedApplication, PatchGap

logger = logging.getLogger(__name__)


@dataclass
class LicenseGapResult:
    """Result of license gap analysis."""

    application: NormalizedApplication
    gap_type: str
    detected_installs: int
    licensed_count: int
    gap_count: int
    risk_level: str
    estimated_cost: Optional[Decimal] = None


@dataclass
class PatchGapResult:
    """Result of patch gap analysis."""

    application: NormalizedApplication
    current_version: ApplicationVersion
    target_version: Optional[ApplicationVersion]
    affected_devices: int
    gap_type: str
    severity: str
    cve_ids: List[str] = field(default_factory=list)


class GapAnalysisEngine:
    """
    Analyzes license and patch gaps.

    Compares discovered applications against:
    - License entitlements
    - Current/EOL versions
    - Security updates
    """

    # Default license cost per seat for estimation
    DEFAULT_LICENSE_COST = Decimal("50.00")

    # Risk level thresholds
    RISK_THRESHOLDS = {
        "critical": 50,  # Gap > 50 units
        "high": 20,  # Gap > 20 units
        "medium": 5,  # Gap > 5 units
        "low": 0,  # Gap > 0 units
    }

    async def analyze_license_gaps(
        self,
        applications: Optional[List[NormalizedApplication]] = None,
    ) -> List[LicenseGapResult]:
        """
        Analyze license gaps for applications.

        Args:
            applications: Applications to analyze (all if None)

        Returns:
            List of identified license gaps
        """
        gaps = []

        if applications is None:
            applications = [app async for app in NormalizedApplication.objects.filter(is_managed=True)]

        for app in applications:
            # Skip if no license linked
            if not app.license_sku_id:
                # Check if this should have a license (managed and approved)
                if app.is_managed and app.is_approved:
                    gaps.append(
                        LicenseGapResult(
                            application=app,
                            gap_type=LicenseGap.GapType.MISSING_LICENSE,
                            detected_installs=app.total_installs,
                            licensed_count=0,
                            gap_count=app.total_installs,
                            risk_level=self._calculate_risk_level(app.total_installs),
                            estimated_cost=self.DEFAULT_LICENSE_COST * app.total_installs,
                        )
                    )
                continue

            # Get license entitlement
            try:
                sku = app.license_sku
                if not sku:
                    continue

                licensed_count = getattr(sku, "quantity", 0)
                detected_installs = app.total_installs
                gap_count = detected_installs - licensed_count

                if gap_count > 0:
                    # Over-deployed
                    gaps.append(
                        LicenseGapResult(
                            application=app,
                            gap_type=LicenseGap.GapType.OVER_DEPLOYMENT,
                            detected_installs=detected_installs,
                            licensed_count=licensed_count,
                            gap_count=gap_count,
                            risk_level=self._calculate_risk_level(gap_count),
                            estimated_cost=self.DEFAULT_LICENSE_COST * gap_count,
                        )
                    )
                elif gap_count < -10:  # Significant under-utilization
                    gaps.append(
                        LicenseGapResult(
                            application=app,
                            gap_type=LicenseGap.GapType.UNDER_LICENSED,
                            detected_installs=detected_installs,
                            licensed_count=licensed_count,
                            gap_count=gap_count,
                            risk_level="low",  # Under-utilization is low risk
                        )
                    )

            except Exception as e:
                logger.warning(f"Error analyzing license for {app.name}: {e}")

        return gaps

    async def analyze_patch_gaps(  # noqa: C901
        self,
        applications: Optional[List[NormalizedApplication]] = None,
    ) -> List[PatchGapResult]:
        """
        Analyze patch gaps for applications.

        Args:
            applications: Applications to analyze (all if None)

        Returns:
            List of identified patch gaps
        """
        gaps = []

        if applications is None:
            applications = [app async for app in NormalizedApplication.objects.prefetch_related("versions")]

        today = date.today()

        for app in applications:
            versions = [v async for v in app.versions.order_by("-is_current", "-version")]

            if not versions:
                continue

            current_version = next((v for v in versions if v.is_current), None)
            if not current_version:
                # Use version with most installs
                versions.sort(key=lambda v: v.install_count, reverse=True)
                current_version = versions[0] if versions else None

            if not current_version:
                continue

            # Check for EOL versions
            if current_version.end_of_life and current_version.end_of_life <= today:
                gaps.append(
                    PatchGapResult(
                        application=app,
                        current_version=current_version,
                        target_version=next((v for v in versions if v.is_current and v != current_version), None),
                        affected_devices=current_version.install_count,
                        gap_type=PatchGap.GapType.EOL_VERSION,
                        severity=PatchGap.Severity.CRITICAL,
                    )
                )
                continue

            # Check for missing security updates
            if not current_version.has_security_updates:
                gaps.append(
                    PatchGapResult(
                        application=app,
                        current_version=current_version,
                        target_version=next((v for v in versions if v.has_security_updates), None),
                        affected_devices=current_version.install_count,
                        gap_type=PatchGap.GapType.SECURITY_PATCH,
                        severity=PatchGap.Severity.HIGH,
                    )
                )
                continue

            # Check for major version upgrades
            for other_version in versions:
                if other_version.is_current and other_version != current_version:
                    current_major = current_version.version_major or 0
                    other_major = other_version.version_major or 0

                    if other_major > current_major:
                        gaps.append(
                            PatchGapResult(
                                application=app,
                                current_version=current_version,
                                target_version=other_version,
                                affected_devices=current_version.install_count,
                                gap_type=PatchGap.GapType.MAJOR_UPGRADE,
                                severity=PatchGap.Severity.MEDIUM,
                            )
                        )
                        break

        return gaps

    async def save_gaps(
        self,
        license_gaps: List[LicenseGapResult],
        patch_gaps: List[PatchGapResult],
    ) -> Dict[str, int]:
        """
        Save analyzed gaps to database.

        Args:
            license_gaps: License gaps to save
            patch_gaps: Patch gaps to save

        Returns:
            Dict with counts of saved gaps
        """
        license_saved = 0
        patch_saved = 0

        for gap in license_gaps:
            # Check if similar gap already exists
            existing = await LicenseGap.objects.filter(
                application=gap.application,
                gap_type=gap.gap_type,
                status__in=["open", "acknowledged"],
            ).afirst()

            if existing:
                # Update existing
                existing.detected_installs = gap.detected_installs
                existing.licensed_count = gap.licensed_count
                existing.gap_count = gap.gap_count
                existing.risk_level = gap.risk_level
                existing.estimated_cost = gap.estimated_cost
                await existing.asave()
            else:
                # Create new
                await LicenseGap.objects.acreate(
                    application=gap.application,
                    gap_type=gap.gap_type,
                    detected_installs=gap.detected_installs,
                    licensed_count=gap.licensed_count,
                    gap_count=gap.gap_count,
                    risk_level=gap.risk_level,
                    estimated_cost=gap.estimated_cost,
                )
                license_saved += 1

        for gap in patch_gaps:
            existing = await PatchGap.objects.filter(
                application=gap.application,
                current_version=gap.current_version,
                status__in=["open", "planned"],
            ).afirst()

            if existing:
                existing.affected_devices = gap.affected_devices
                existing.severity = gap.severity
                if gap.target_version:
                    existing.target_version = gap.target_version
                await existing.asave()
            else:
                await PatchGap.objects.acreate(
                    application=gap.application,
                    current_version=gap.current_version,
                    target_version=gap.target_version,
                    affected_devices=gap.affected_devices,
                    gap_type=gap.gap_type,
                    severity=gap.severity,
                    cve_ids=gap.cve_ids,
                )
                patch_saved += 1

        return {
            "license_gaps_created": license_saved,
            "patch_gaps_created": patch_saved,
        }

    def _calculate_risk_level(self, gap_count: int) -> str:
        """Calculate risk level based on gap count."""
        for level, threshold in self.RISK_THRESHOLDS.items():
            if gap_count > threshold:
                return level
        return "low"

    async def get_shadow_it_applications(
        self,
        min_installs: int = 5,
    ) -> List[NormalizedApplication]:
        """
        Get shadow IT applications (unmanaged, unapproved).

        Args:
            min_installs: Minimum install count to include

        Returns:
            List of shadow IT applications
        """
        apps = []
        async for app in NormalizedApplication.objects.filter(
            is_managed=False,
            is_approved=False,
            total_installs__gte=min_installs,
        ).order_by("-total_installs"):
            apps.append(app)
        return apps

    async def generate_risk_summary(self) -> Dict[str, Any]:
        """
        Generate risk summary across all gaps.

        Returns:
            Dict with risk summary statistics
        """
        # License gaps by risk
        license_by_risk = {}
        async for gap in LicenseGap.objects.filter(status="open"):
            level = gap.risk_level
            license_by_risk[level] = license_by_risk.get(level, 0) + 1

        # Patch gaps by severity
        patch_by_severity = {}
        async for gap in PatchGap.objects.filter(status="open"):
            level = gap.severity
            patch_by_severity[level] = patch_by_severity.get(level, 0) + 1

        # Total estimated cost
        total_cost = Decimal("0")
        async for gap in LicenseGap.objects.filter(status="open"):
            if gap.estimated_cost:
                total_cost += gap.estimated_cost

        return {
            "license_gaps": {
                "total": sum(license_by_risk.values()),
                "by_risk": license_by_risk,
            },
            "patch_gaps": {
                "total": sum(patch_by_severity.values()),
                "by_severity": patch_by_severity,
            },
            "estimated_license_cost": float(total_cost),
            "generated_at": timezone.now().isoformat(),
        }
