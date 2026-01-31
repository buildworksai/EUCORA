# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for Discovery Agent.
"""
import pytest

from apps.discovery_agent.models import DiscoveredApplication, DiscoveryRun, DiscoverySource, NormalizedApplication
from apps.discovery_agent.services.normalization import ApplicationNormalizer


@pytest.fixture
def discovery_source(db):
    """Create test discovery source."""
    return DiscoverySource.objects.create(
        name="Test Source",
        source_type="sccm",
        connection_config={},
    )


@pytest.fixture
def discovery_run(db, discovery_source):
    """Create test discovery run."""
    return DiscoveryRun.objects.create(
        source=discovery_source,
        run_type="full",
        status="running",
    )


class TestApplicationNormalizer:
    """Tests for ApplicationNormalizer."""

    def test_normalize_name_removes_version(self):
        """Test version number removal."""
        normalizer = ApplicationNormalizer()

        cases = [
            ("Microsoft Office 16.0.14326", "Microsoft Office"),
            ("Adobe Reader v2024.001", "Adobe Reader"),
            ("Chrome 120.0.6099.109", "Chrome"),
            ("Zoom 5.17.5", "Zoom"),
            ("Slack - 4.35.126", "Slack"),
        ]

        for raw, expected in cases:
            result = normalizer.normalize_name(raw)
            assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_normalize_name_removes_architecture(self):
        """Test architecture suffix removal."""
        normalizer = ApplicationNormalizer()

        cases = [
            ("Visual Studio Code (x64)", "Visual Studio Code"),
            ("7-Zip (x86)", "7-Zip"),
            ("Python 3.12 (64-bit)", "Python 3.12"),
        ]

        for raw, expected in cases:
            result = normalizer.normalize_name(raw)
            assert expected in result

    def test_normalize_publisher(self):
        """Test publisher normalization."""
        normalizer = ApplicationNormalizer()

        cases = [
            ("Microsoft Corporation", "Microsoft"),
            ("MICROSOFT CORP", "Microsoft"),
            ("Adobe Systems Incorporated", "Adobe"),
            ("Google LLC", "Google"),
            ("Apple Inc.", "Apple"),
        ]

        for raw, expected in cases:
            result = normalizer.normalize_publisher(raw)
            assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_calculate_similarity(self):
        """Test similarity calculation."""
        normalizer = ApplicationNormalizer()

        # Same name should be 1.0
        assert normalizer.calculate_similarity("Test App", "Test App") == 1.0

        # Similar names
        score = normalizer.calculate_similarity("Microsoft Office", "Microsoft Office 365")
        assert score > 0.7

        # Very different names
        score = normalizer.calculate_similarity("Chrome", "Firefox")
        assert score < 0.5

    def test_parse_version(self):
        """Test version parsing."""
        cases = [
            ("1.2.3", (1, 2, 3)),
            ("v2.0.0", (2, 0, 0)),
            ("16.0.14326", (16, 0, 14326)),
            ("2024.001", (2024, 1, None)),
            ("", (None, None, None)),
            ("invalid", (None, None, None)),
        ]

        for version_str, expected in cases:
            result = ApplicationNormalizer.parse_version(version_str)
            assert result == expected, f"For '{version_str}': expected {expected}, got {result}"

    @pytest.mark.asyncio
    async def test_normalize_creates_new_app(self, db, discovery_run):
        """Test normalizing creates new normalized app."""
        discovered = DiscoveredApplication.objects.create(
            discovery_run=discovery_run,
            source_id="test-1",
            source_type="sccm",
            raw_name="Brand New App v1.0",
            raw_publisher="New Publisher Inc.",
            raw_version="1.0",
        )

        normalizer = ApplicationNormalizer()
        result = await normalizer.normalize(discovered)

        assert result.is_new is True
        assert result.normalized_app is not None
        assert result.normalized_app.name == "Brand New App"
        assert result.confidence == 1.0
        assert result.method == "new"

    @pytest.mark.asyncio
    async def test_normalize_matches_existing(self, db, discovery_run):
        """Test normalizing matches existing app."""
        # Create existing normalized app
        existing = NormalizedApplication.objects.create(
            name="Existing App",
            publisher="Publisher",
            fingerprint=NormalizedApplication.generate_fingerprint("Existing App", "Publisher"),
        )

        discovered = DiscoveredApplication.objects.create(
            discovery_run=discovery_run,
            source_id="test-2",
            source_type="sccm",
            raw_name="Existing App v2.0",
            raw_publisher="Publisher Inc.",
            raw_version="2.0",
        )

        normalizer = ApplicationNormalizer()
        result = await normalizer.normalize(discovered)

        assert result.is_new is False
        assert result.normalized_app == existing
        assert result.method == "fingerprint"
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_normalize_fuzzy_match(self, db, discovery_run):
        """Test fuzzy matching."""
        # Create existing app with slightly different name
        NormalizedApplication.objects.create(
            name="Microsoft Office 365",
            publisher="Microsoft",
            fingerprint=NormalizedApplication.generate_fingerprint("Microsoft Office 365", "Microsoft"),
        )

        discovered = DiscoveredApplication.objects.create(
            discovery_run=discovery_run,
            source_id="test-3",
            source_type="intune",
            raw_name="Microsoft Office 365 ProPlus",
            raw_publisher="Microsoft Corporation",
            raw_version="16.0",
        )

        normalizer = ApplicationNormalizer(fuzzy_threshold=0.7)
        result = await normalizer.normalize(discovered)

        # Should match via fuzzy matching
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_find_matches(self, db, discovery_run):
        """Test finding potential matches."""
        # Create some normalized apps
        NormalizedApplication.objects.create(
            name="Chrome",
            publisher="Google",
            fingerprint=NormalizedApplication.generate_fingerprint("Chrome", "Google"),
        )
        NormalizedApplication.objects.create(
            name="Firefox",
            publisher="Mozilla",
            fingerprint=NormalizedApplication.generate_fingerprint("Firefox", "Mozilla"),
        )

        discovered = DiscoveredApplication.objects.create(
            discovery_run=discovery_run,
            source_id="test-4",
            source_type="sccm",
            raw_name="Google Chrome",
            raw_publisher="Google",
        )

        normalizer = ApplicationNormalizer()
        matches = await normalizer.find_matches(discovered, limit=5)

        # Should find Chrome as a potential match
        assert len(matches) >= 1
        app_names = [m[0].name for m in matches]
        assert "Chrome" in app_names
