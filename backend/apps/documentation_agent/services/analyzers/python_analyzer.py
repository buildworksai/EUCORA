# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Python/Django code analyzer.

Analyzes Django applications to extract models, views, serializers, and API endpoints.
"""
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ModelInfo:
    """Information about a Django model."""

    name: str
    module_path: str
    fields: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    docstring: str | None = None


@dataclass
class ViewInfo:
    """Information about a Django view/viewset."""

    name: str
    module_path: str
    view_type: str  # ViewSet, APIView, FunctionView
    methods: list[str]
    docstring: str | None = None


@dataclass
class SerializerInfo:
    """Information about a DRF serializer."""

    name: str
    module_path: str
    fields: list[dict[str, Any]]
    docstring: str | None = None


@dataclass
class EndpointInfo:
    """Information about an API endpoint."""

    path: str
    method: str
    view_name: str
    docstring: str | None = None


class DjangoCodeAnalyzer:
    """Analyzes Django applications."""

    def __init__(self, base_path: str | Path):
        """
        Initialize analyzer.

        Args:
            base_path: Base path to the Django project/app
        """
        self.base_path = Path(base_path)

    def analyze_models(self, module_path: str) -> list[ModelInfo]:
        """
        Extract model definitions with fields and relationships.

        Args:
            module_path: Path to models.py file

        Returns:
            List of ModelInfo objects
        """
        models = []
        file_path = self.base_path / module_path

        if not file_path.exists():
            return models

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a Django model (inherits from models.Model)
                    if self._is_django_model(node, tree):
                        model_info = self._extract_model_info(node, module_path)
                        if model_info:
                            models.append(model_info)
        except Exception as e:
            # Log error but continue
            print(f"Error analyzing models in {module_path}: {e}")

        return models

    def analyze_views(self, module_path: str) -> list[ViewInfo]:
        """
        Extract view/viewset definitions with endpoints.

        Args:
            module_path: Path to views.py file

        Returns:
            List of ViewInfo objects
        """
        views = []
        file_path = self.base_path / module_path

        if not file_path.exists():
            return views

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if self._is_viewset(node, tree):
                        view_info = self._extract_view_info(node, module_path)
                        if view_info:
                            views.append(view_info)
        except Exception as e:
            print(f"Error analyzing views in {module_path}: {e}")

        return views

    def analyze_serializers(self, module_path: str) -> list[SerializerInfo]:
        """
        Extract serializer definitions with fields.

        Args:
            module_path: Path to serializers.py file

        Returns:
            List of SerializerInfo objects
        """
        serializers = []
        file_path = self.base_path / module_path

        if not file_path.exists():
            return serializers

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if self._is_serializer(node, tree):
                        serializer_info = self._extract_serializer_info(node, module_path)
                        if serializer_info:
                            serializers.append(serializer_info)
        except Exception as e:
            print(f"Error analyzing serializers in {module_path}: {e}")

        return serializers

    def extract_api_endpoints(self, urls_path: str) -> list[EndpointInfo]:  # noqa: C901
        """
        Extract API endpoints from URL configuration.

        Args:
            urls_path: Path to urls.py file

        Returns:
            List of EndpointInfo objects
        """
        endpoints = []
        file_path = self.base_path / urls_path

        if not file_path.exists():
            return endpoints

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            # Look for urlpatterns assignments
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "urlpatterns":
                            # Extract URL patterns
                            if isinstance(node.value, ast.List):
                                for pattern in node.value.elts:
                                    endpoint = self._extract_url_pattern(pattern)
                                    if endpoint:
                                        endpoints.append(endpoint)
        except Exception as e:
            print(f"Error extracting endpoints from {urls_path}: {e}")

        return endpoints

    def _is_django_model(self, node: ast.ClassDef, tree: ast.AST) -> bool:
        """Check if class inherits from models.Model."""
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                if base.attr == "Model":
                    return True
            elif isinstance(base, ast.Name):
                # Could be Model imported directly
                return True
        return False

    def _is_viewset(self, node: ast.ClassDef, tree: ast.AST) -> bool:
        """Check if class is a ViewSet."""
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                if "ViewSet" in base.attr or "APIView" in base.attr:
                    return True
            elif isinstance(base, ast.Name):
                if "ViewSet" in base.id or "APIView" in base.id:
                    return True
        return False

    def _is_serializer(self, node: ast.ClassDef, tree: ast.AST) -> bool:
        """Check if class is a Serializer."""
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                if "Serializer" in base.attr:
                    return True
            elif isinstance(base, ast.Name):
                if "Serializer" in base.id:
                    return True
        return False

    def _extract_model_info(self, node: ast.ClassDef, module_path: str) -> ModelInfo | None:
        """Extract model information from AST node."""
        docstring = ast.get_docstring(node)
        fields = []
        relationships = []

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        field_name = target.id
                        # Check if it's a model field
                        if isinstance(item.value, ast.Call):
                            func = item.value.func
                            if isinstance(func, ast.Attribute) or isinstance(func, ast.Name):
                                field_type = self._get_field_type(func)
                                fields.append({"name": field_name, "type": field_type})
                                if field_type in ["ForeignKey", "ManyToManyField", "OneToOneField"]:
                                    relationships.append({"name": field_name, "type": field_type})

        return ModelInfo(
            name=node.name,
            module_path=module_path,
            fields=fields,
            relationships=relationships,
            docstring=docstring,
        )

    def _extract_view_info(self, node: ast.ClassDef, module_path: str) -> ViewInfo | None:
        """Extract view information from AST node."""
        docstring = ast.get_docstring(node)
        view_type = "ViewSet"
        methods = []

        for base in node.bases:
            if isinstance(base, ast.Attribute):
                view_type = base.attr
            elif isinstance(base, ast.Name):
                view_type = base.id

        # Extract HTTP methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.lower() in ["get", "post", "put", "patch", "delete"]:
                    methods.append(item.name.upper())

        return ViewInfo(
            name=node.name,
            module_path=module_path,
            view_type=view_type,
            methods=methods,
            docstring=docstring,
        )

    def _extract_serializer_info(self, node: ast.ClassDef, module_path: str) -> SerializerInfo | None:
        """Extract serializer information from AST node."""
        docstring = ast.get_docstring(node)
        fields = []

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        fields.append({"name": target.id, "type": "unknown"})

        return SerializerInfo(
            name=node.name,
            module_path=module_path,
            fields=fields,
            docstring=docstring,
        )

    def _extract_url_pattern(self, pattern: ast.expr) -> EndpointInfo | None:
        """Extract endpoint information from URL pattern."""
        # Simplified extraction - would need more sophisticated parsing
        return None

    def _get_field_type(self, func: ast.expr) -> str:
        """Get Django field type name."""
        if isinstance(func, ast.Attribute):
            return func.attr
        elif isinstance(func, ast.Name):
            return func.id
        return "Unknown"
