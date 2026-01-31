# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Documentation generator.

Generates OpenAPI specs, README files, Mermaid diagrams, and other documentation.
"""
from typing import Any

from apps.documentation_agent.models import CodeAnalysis, DocumentedModule


class DocGenerator:
    """Generates documentation from code analysis."""

    def generate_api_docs(self, analysis: CodeAnalysis) -> str:
        """
        Generate OpenAPI/Swagger documentation.

        Args:
            analysis: CodeAnalysis instance

        Returns:
            OpenAPI YAML content
        """
        modules = analysis.modules.filter(module_type=DocumentedModule.ModuleType.ENDPOINT)
        endpoints = []

        for module in modules:
            endpoint_data = {
                "path": module.metadata.get("path", ""),
                "method": module.metadata.get("method", "GET"),
                "summary": module.docstring or module.name,
            }
            endpoints.append(endpoint_data)

        # Generate OpenAPI spec
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": f"{analysis.repository.name} API",
                "version": "1.0.0",
            },
            "paths": {},
        }

        for endpoint in endpoints:
            path = endpoint["path"]
            method = endpoint["method"].lower()
            if path not in openapi_spec["paths"]:
                openapi_spec["paths"][path] = {}
            openapi_spec["paths"][path][method] = {
                "summary": endpoint["summary"],
                "responses": {"200": {"description": "Success"}},
            }

        # Convert to YAML (simplified - would use yaml library in production)
        yaml_content = self._dict_to_yaml(openapi_spec)
        return yaml_content

    def generate_readme(self, analysis: CodeAnalysis) -> str:
        """
        Generate README.md documentation.

        Args:
            analysis: CodeAnalysis instance

        Returns:
            Markdown content
        """
        summary = analysis.summary or {}
        modules = analysis.modules.all()

        readme_lines = [
            f"# {analysis.repository.name}",
            "",
            "## Overview",
            "",
            f"This repository contains {summary.get('modules', 0)} modules, "
            f"{summary.get('classes', 0)} classes, and {summary.get('functions', 0)} functions.",
            "",
            "## Structure",
            "",
        ]

        # Group modules by type
        modules_by_type: dict[str, list[DocumentedModule]] = {}
        for module in modules:
            module_type = module.module_type
            if module_type not in modules_by_type:
                modules_by_type[module_type] = []
            modules_by_type[module_type].append(module)

        for module_type, module_list in modules_by_type.items():
            readme_lines.append(f"### {module_type.title()}s")
            readme_lines.append("")
            for module in module_list:
                readme_lines.append(f"- **{module.name}** - {module.module_path}")
                if module.docstring:
                    readme_lines.append(f"  - {module.docstring[:100]}...")
            readme_lines.append("")

        return "\n".join(readme_lines)

    def generate_mermaid_diagram(self, analysis: CodeAnalysis) -> str:
        """
        Generate Mermaid architecture diagram.

        Args:
            analysis: CodeAnalysis instance

        Returns:
            Mermaid diagram content
        """
        modules = analysis.modules.all()
        diagram_lines = ["graph TB"]

        # Add nodes
        for module in modules:
            node_id = module.name.replace(" ", "").replace("-", "")
            diagram_lines.append(f'    {node_id}["{module.name}"]')

        # Add relationships (simplified)
        for module in modules:
            if module.dependencies:
                node_id = module.name.replace(" ", "").replace("-", "")
                for dep in module.dependencies:
                    dep_id = dep.replace(" ", "").replace("-", "")
                    diagram_lines.append(f"    {node_id} --> {dep_id}")

        return "\n".join(diagram_lines)

    def _dict_to_yaml(self, data: dict[str, Any], indent: int = 0) -> str:
        """Convert dict to YAML string (simplified)."""
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(" " * indent + f"{key}:")
                lines.append(self._dict_to_yaml(value, indent + 2))
            elif isinstance(value, list):
                lines.append(" " * indent + f"{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(" " * (indent + 2) + "-")
                        lines.append(self._dict_to_yaml(item, indent + 4))
                    else:
                        lines.append(" " * (indent + 2) + f"- {item}")
            else:
                lines.append(" " * indent + f"{key}: {value}")
        return "\n".join(lines)
