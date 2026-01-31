# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
TypeScript/React code analyzer.

Analyzes React/TypeScript applications to extract components, hooks, and types.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ComponentInfo:
    """Information about a React component."""

    name: str
    file_path: str
    props: list[dict[str, Any]]
    hooks_used: list[str]
    docstring: str | None = None


@dataclass
class HookInfo:
    """Information about a React hook."""

    name: str
    file_path: str
    parameters: list[str]
    return_type: str | None = None
    docstring: str | None = None


@dataclass
class TypeInfo:
    """Information about a TypeScript type/interface."""

    name: str
    file_path: str
    fields: list[dict[str, Any]]
    docstring: str | None = None


@dataclass
class RouteInfo:
    """Information about a route definition."""

    path: str
    component: str
    file_path: str


class ReactCodeAnalyzer:
    """Analyzes React/TypeScript applications."""

    def __init__(self, base_path: str | Path):
        """
        Initialize analyzer.

        Args:
            base_path: Base path to the React project
        """
        self.base_path = Path(base_path)

    def analyze_components(self, dir_path: str) -> list[ComponentInfo]:
        """
        Extract React component definitions.

        Args:
            dir_path: Directory path to search for components

        Returns:
            List of ComponentInfo objects
        """
        components = []
        search_path = self.base_path / dir_path

        if not search_path.exists():
            return components

        for file_path in search_path.rglob("*.tsx"):
            if file_path.is_file():
                component = self._extract_component(file_path)
                if component:
                    components.append(component)

        return components

    def analyze_hooks(self, dir_path: str) -> list[HookInfo]:
        """
        Extract custom hooks.

        Args:
            dir_path: Directory path to search for hooks

        Returns:
            List of HookInfo objects
        """
        hooks = []
        search_path = self.base_path / dir_path

        if not search_path.exists():
            return hooks

        for file_path in search_path.rglob("*.ts"):
            if file_path.is_file():
                hook = self._extract_hook(file_path)
                if hook:
                    hooks.append(hook)

        return hooks

    def analyze_types(self, dir_path: str) -> list[TypeInfo]:
        """
        Extract TypeScript type definitions.

        Args:
            dir_path: Directory path to search for types

        Returns:
            List of TypeInfo objects
        """
        types = []
        search_path = self.base_path / dir_path

        if not search_path.exists():
            return types

        for file_path in search_path.rglob("*.ts"):
            if file_path.is_file():
                file_types = self._extract_types(file_path)
                types.extend(file_types)

        return types

    def extract_routes(self, app_path: str) -> list[RouteInfo]:
        """
        Extract route definitions.

        Args:
            app_path: Path to App.tsx or routes file

        Returns:
            List of RouteInfo objects
        """
        routes = []
        file_path = self.base_path / app_path

        if not file_path.exists():
            return routes

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for Route components
            route_pattern = r'<Route\s+path=["\']([^"\']+)["\']\s+element=\{<(\w+)\s*/>\}'
            matches = re.finditer(route_pattern, content)

            for match in matches:
                routes.append(
                    RouteInfo(
                        path=match.group(1),
                        component=match.group(2),
                        file_path=str(file_path.relative_to(self.base_path)),
                    )
                )
        except Exception as e:
            print(f"Error extracting routes from {app_path}: {e}")

        return routes

    def _extract_component(self, file_path: Path) -> ComponentInfo | None:
        """Extract component information from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for function/const component definitions
            component_pattern = r"(?:export\s+)?(?:function|const)\s+(\w+)\s*[=:]?\s*(?:\([^)]*\)\s*[:=]?\s*)?(?:React\.)?(?:FC|Component)"  # noqa: E501
            match = re.search(component_pattern, content)

            if not match:
                return None

            component_name = match.group(1)
            props = self._extract_props(content)
            hooks_used = self._extract_hooks_used(content)
            docstring = self._extract_docstring(content)

            return ComponentInfo(
                name=component_name,
                file_path=str(file_path.relative_to(self.base_path)),
                props=props,
                hooks_used=hooks_used,
                docstring=docstring,
            )
        except Exception as e:
            print(f"Error extracting component from {file_path}: {e}")
            return None

    def _extract_hook(self, file_path: Path) -> HookInfo | None:
        """Extract hook information from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for use* hook definitions
            hook_pattern = r"(?:export\s+)?(?:function|const)\s+(use\w+)\s*=\s*(?:\([^)]*\)\s*[:=]?\s*)?"
            match = re.search(hook_pattern, content)

            if not match:
                return None

            hook_name = match.group(1)
            parameters = self._extract_parameters(content, hook_name)
            return_type = self._extract_return_type(content, hook_name)
            docstring = self._extract_docstring(content)

            return HookInfo(
                name=hook_name,
                file_path=str(file_path.relative_to(self.base_path)),
                parameters=parameters,
                return_type=return_type,
                docstring=docstring,
            )
        except Exception as e:
            print(f"Error extracting hook from {file_path}: {e}")
            return None

    def _extract_types(self, file_path: Path) -> list[TypeInfo]:
        """Extract type/interface definitions from file."""
        types = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for interface/type definitions
            interface_pattern = r"(?:export\s+)?interface\s+(\w+)\s*\{([^}]+)\}"
            type_pattern = r"(?:export\s+)?type\s+(\w+)\s*=\s*\{([^}]+)\}"

            for pattern in [interface_pattern, type_pattern]:
                matches = re.finditer(pattern, content, re.DOTALL)
                for match in matches:
                    type_name = match.group(1)
                    fields = self._extract_type_fields(match.group(2))
                    docstring = self._extract_docstring(content, before_text=match.group(0))

                    types.append(
                        TypeInfo(
                            name=type_name,
                            file_path=str(file_path.relative_to(self.base_path)),
                            fields=fields,
                            docstring=docstring,
                        )
                    )
        except Exception as e:
            print(f"Error extracting types from {file_path}: {e}")

        return types

    def _extract_props(self, content: str) -> list[dict[str, Any]]:
        """Extract props from component."""
        props = []
        # Simplified - would need more sophisticated parsing
        return props

    def _extract_hooks_used(self, content: str) -> list[str]:
        """Extract React hooks used in component."""
        hooks = []
        hook_pattern = r"(use\w+)\s*\("
        matches = re.finditer(hook_pattern, content)
        for match in matches:
            hook_name = match.group(1)
            if hook_name not in hooks:
                hooks.append(hook_name)
        return hooks

    def _extract_parameters(self, content: str, function_name: str) -> list[str]:
        """Extract function parameters."""
        params = []
        pattern = rf"{function_name}\s*=\s*(?:\(([^)]+)\)|([^=]+))"
        match = re.search(pattern, content)
        if match:
            param_str = match.group(1) or match.group(2)
            if param_str:
                params = [p.strip().split(":")[0] for p in param_str.split(",")]
        return params

    def _extract_return_type(self, content: str, function_name: str) -> str | None:
        """Extract function return type."""
        pattern = rf"{function_name}\s*[:=]\s*\([^)]*\)\s*:\s*(\w+)"
        match = re.search(pattern, content)
        return match.group(1) if match else None

    def _extract_type_fields(self, fields_content: str) -> list[dict[str, Any]]:
        """Extract fields from type/interface definition."""
        fields = []
        for line in fields_content.split("\n"):
            line = line.strip()
            if line and not line.startswith("//"):
                # Extract field name and type
                if ":" in line:
                    parts = line.split(":", 1)
                    field_name = parts[0].strip()
                    field_type = parts[1].strip().rstrip(";")
                    fields.append({"name": field_name, "type": field_type})
        return fields

    def _extract_docstring(self, content: str, before_text: str | None = None) -> str | None:
        """Extract JSDoc comment."""
        # Look for /** ... */ comments
        doc_pattern = r"/\*\*([^*]*(?:\*(?!/)[^*]*)*)\*/"
        matches = list(re.finditer(doc_pattern, content))
        if matches:
            return matches[0].group(1).strip()
        return None
