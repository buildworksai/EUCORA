# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Documentation quality scorer.

Calculates quality scores for generated documentation.
"""
from typing import Any

from apps.documentation_agent.models import CodeAnalysis


class QualityScorer:
    """Calculates documentation quality metrics."""

    def calculate_quality_score(self, analysis: CodeAnalysis) -> dict[str, Any]:
        """
        Calculate overall quality score for documentation.

        Args:
            analysis: CodeAnalysis instance

        Returns:
            Dictionary with quality metrics
        """
        modules = analysis.modules.all()
        documents = analysis.documents.all()

        # Calculate coverage (modules with documentation)
        total_modules = modules.count()
        documented_modules = modules.exclude(docstring__isnull=True).exclude(docstring="").count()
        coverage = (documented_modules / total_modules * 100) if total_modules > 0 else 0

        # Calculate completeness (documents with content)
        total_docs = documents.count()
        complete_docs = documents.exclude(content__isnull=True).exclude(content="").count()
        completeness = (complete_docs / total_docs * 100) if total_docs > 0 else 0

        # Calculate average docstring length
        docstrings = [m.docstring for m in modules if m.docstring]
        avg_docstring_length = sum(len(d) for d in docstrings) / len(docstrings) if docstrings else 0

        # Overall score (weighted average)
        overall_score = (coverage * 0.4) + (completeness * 0.4) + (min(avg_docstring_length / 100, 1.0) * 20)

        return {
            "overall_score": round(overall_score, 2),
            "coverage": round(coverage, 2),
            "completeness": round(completeness, 2),
            "avg_docstring_length": round(avg_docstring_length, 2),
            "total_modules": total_modules,
            "documented_modules": documented_modules,
            "total_documents": total_docs,
            "complete_documents": complete_docs,
        }
