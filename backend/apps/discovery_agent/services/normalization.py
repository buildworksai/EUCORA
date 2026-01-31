# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Application Normalization Service.

Normalizes discovered application names to canonical forms
for aggregation and deduplication.
"""
import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from ..models import DiscoveredApplication, NormalizedApplication

logger = logging.getLogger(__name__)


@dataclass
class NormalizationResult:
    """Result of normalization attempt."""

    normalized_app: Optional[NormalizedApplication]
    confidence: float
    method: str
    is_new: bool
    match_details: Dict[str, Any]


class ApplicationNormalizer:
    """
    Normalizes discovered application names.

    Uses multiple matching strategies:
    1. Exact fingerprint match
    2. Fuzzy name matching
    3. Publisher + name matching
    4. Embedding similarity (if available)
    """

    # Common version pattern
    VERSION_PATTERN = re.compile(
        r"[\s_\-]*(v?\d+[\.\d]+[\.\d]*[\w]*)[\s_\-]*(\(.*?\))?" r"|[\s_\-]*\d+[\.\d]+[\.\d]*[\s_\-]*$",
        re.IGNORECASE,
    )

    # Common suffixes to remove
    SUFFIXES_TO_REMOVE = [
        r"\s*\(x64\)",
        r"\s*\(x86\)",
        r"\s*\(64-bit\)",
        r"\s*\(32-bit\)",
        r"\s*-\s*x64",
        r"\s*-\s*x86",
        r"\s*English",
        r"\s*\[.*?\]",
        r"\s*Edition",
        r"\s*Update\s*\d*",
    ]

    # Publisher normalizations
    PUBLISHER_NORMALIZATIONS = {
        "microsoft corporation": "microsoft",
        "microsoft corp": "microsoft",
        "microsoft corp.": "microsoft",
        "adobe systems incorporated": "adobe",
        "adobe systems": "adobe",
        "oracle corporation": "oracle",
        "oracle america, inc.": "oracle",
        "google inc.": "google",
        "google llc": "google",
        "apple inc.": "apple",
    }

    def __init__(self, fuzzy_threshold: float = 0.85):
        """
        Initialize normalizer.

        Args:
            fuzzy_threshold: Minimum similarity for fuzzy matching (0-1)
        """
        self.fuzzy_threshold = fuzzy_threshold

    def normalize_name(self, raw_name: str) -> str:
        """
        Normalize application name.

        Args:
            raw_name: Raw application name from source

        Returns:
            Normalized name
        """
        name = raw_name.strip()

        # Remove version numbers
        name = self.VERSION_PATTERN.sub("", name)

        # Remove common suffixes
        for suffix in self.SUFFIXES_TO_REMOVE:
            name = re.sub(suffix, "", name, flags=re.IGNORECASE)

        # Normalize whitespace
        name = " ".join(name.split())

        return name.strip()

    def normalize_publisher(self, raw_publisher: str) -> str:
        """
        Normalize publisher name.

        Args:
            raw_publisher: Raw publisher name

        Returns:
            Normalized publisher
        """
        publisher = raw_publisher.strip().lower()

        # Apply known normalizations
        if publisher in self.PUBLISHER_NORMALIZATIONS:
            return self.PUBLISHER_NORMALIZATIONS[publisher]

        # Remove common suffixes
        publisher = re.sub(r"\s*(inc\.?|corp\.?|ltd\.?|llc\.?|gmbh)$", "", publisher, flags=re.IGNORECASE)

        return publisher.strip().title()

    def calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names.

        Args:
            name1: First name
            name2: Second name

        Returns:
            Similarity score (0-1)
        """
        # Normalize both names
        n1 = self.normalize_name(name1).lower()
        n2 = self.normalize_name(name2).lower()

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, n1, n2).ratio()

    async def normalize(
        self,
        discovered: DiscoveredApplication,
    ) -> NormalizationResult:
        """
        Normalize a discovered application.

        Args:
            discovered: Discovered application to normalize

        Returns:
            NormalizationResult with match information
        """
        # Step 1: Generate fingerprint and check for exact match
        normalized_name = self.normalize_name(discovered.raw_name)
        normalized_publisher = self.normalize_publisher(discovered.raw_publisher or "")
        fingerprint = NormalizedApplication.generate_fingerprint(normalized_name, normalized_publisher)

        existing = await NormalizedApplication.objects.filter(fingerprint=fingerprint).afirst()
        if existing:
            return NormalizationResult(
                normalized_app=existing,
                confidence=1.0,
                method="fingerprint",
                is_new=False,
                match_details={"fingerprint": fingerprint},
            )

        # Step 2: Try fuzzy matching against existing normalized apps
        best_match: Optional[NormalizedApplication] = None
        best_score = 0.0

        async for candidate in NormalizedApplication.objects.all()[:1000]:  # Limit for performance
            # Match on name
            name_score = self.calculate_similarity(discovered.raw_name, candidate.name)

            # Match on publisher if available
            publisher_score = 0.0
            if discovered.raw_publisher and candidate.publisher:
                publisher_score = self.calculate_similarity(discovered.raw_publisher, candidate.publisher)

            # Combined score (weighted)
            combined_score = (name_score * 0.7) + (publisher_score * 0.3)

            if combined_score > best_score and combined_score >= self.fuzzy_threshold:
                best_score = combined_score
                best_match = candidate

        if best_match:
            return NormalizationResult(
                normalized_app=best_match,
                confidence=best_score,
                method="fuzzy",
                is_new=False,
                match_details={
                    "matched_name": best_match.name,
                    "matched_publisher": best_match.publisher,
                    "score": best_score,
                },
            )

        # Step 3: Create new normalized application
        new_app = await NormalizedApplication.objects.acreate(
            name=normalized_name,
            publisher=normalized_publisher,
            fingerprint=fingerprint,
            is_managed=False,
            is_approved=False,
            total_installs=discovered.install_count,
            first_discovered=discovered.created_at,
            last_discovered=discovered.created_at,
        )

        return NormalizationResult(
            normalized_app=new_app,
            confidence=1.0,
            method="new",
            is_new=True,
            match_details={"fingerprint": fingerprint},
        )

    async def find_matches(
        self,
        discovered: DiscoveredApplication,
        limit: int = 5,
    ) -> List[Tuple[NormalizedApplication, float]]:
        """
        Find potential matches for a discovered app.

        Args:
            discovered: Discovered application
            limit: Maximum matches to return

        Returns:
            List of (NormalizedApplication, score) tuples
        """
        matches = []

        async for candidate in NormalizedApplication.objects.all()[:500]:
            name_score = self.calculate_similarity(discovered.raw_name, candidate.name)

            if name_score >= 0.5:  # Lower threshold for suggestions
                matches.append((candidate, name_score))

        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]

    @staticmethod
    def parse_version(version_str: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        Parse version string into components.

        Args:
            version_str: Version string (e.g., "1.2.3")

        Returns:
            Tuple of (major, minor, patch)
        """
        if not version_str:
            return None, None, None

        # Remove leading 'v' or 'V'
        version_str = re.sub(r"^[vV]", "", version_str.strip())

        parts = re.split(r"[\.\-_]", version_str)
        result = [None, None, None]

        for i, part in enumerate(parts[:3]):
            try:
                result[i] = int(re.match(r"\d+", part).group())
            except (AttributeError, ValueError):
                pass

        return tuple(result)
