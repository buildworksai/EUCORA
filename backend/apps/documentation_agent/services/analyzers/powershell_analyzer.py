# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
PowerShell script analyzer.

Analyzes PowerShell scripts to extract functions, cmdlets, and parameters.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FunctionInfo:
    """Information about a PowerShell function."""

    name: str
    file_path: str
    parameters: list[dict[str, Any]]
    comment_help: str | None = None


@dataclass
class CmdletInfo:
    """Information about a PowerShell cmdlet usage."""

    name: str
    file_path: str
    parameters: list[str]


class PowerShellAnalyzer:
    """Analyzes PowerShell scripts."""

    def __init__(self, base_path: str | Path):
        """
        Initialize analyzer.

        Args:
            base_path: Base path to PowerShell scripts directory
        """
        self.base_path = Path(base_path)

    def analyze_functions(self, file_path: str) -> list[FunctionInfo]:
        """
        Extract function definitions from PowerShell script.

        Args:
            file_path: Path to .ps1 file

        Returns:
            List of FunctionInfo objects
        """
        functions = []
        full_path = self.base_path / file_path

        if not full_path.exists() or not full_path.suffix == ".ps1":
            return functions

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for function definitions
            function_pattern = r"function\s+([\w-]+)\s*(?:\(([^)]*)\))?\s*\{"
            matches = re.finditer(function_pattern, content, re.MULTILINE)

            for match in matches:
                func_name = match.group(1)
                param_str = match.group(2) if match.group(2) else ""
                parameters = self._parse_parameters(param_str)
                comment_help = self._extract_comment_help(content, match.start())

                functions.append(
                    FunctionInfo(
                        name=func_name,
                        file_path=str(full_path.relative_to(self.base_path)),
                        parameters=parameters,
                        comment_help=comment_help,
                    )
                )
        except Exception as e:
            print(f"Error analyzing PowerShell functions in {file_path}: {e}")

        return functions

    def analyze_cmdlets(self, file_path: str) -> list[CmdletInfo]:
        """
        Extract cmdlet usage from PowerShell script.

        Args:
            file_path: Path to .ps1 file

        Returns:
            List of CmdletInfo objects
        """
        cmdlets = []
        full_path = self.base_path / file_path

        if not full_path.exists():
            return cmdlets

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for cmdlet calls (Verb-Noun pattern)
            cmdlet_pattern = r"([A-Z][a-z]+-[A-Z][a-zA-Z]+)\s+"
            matches = re.finditer(cmdlet_pattern, content)

            seen_cmdlets = {}
            for match in matches:
                cmdlet_name = match.group(1)
                if cmdlet_name not in seen_cmdlets:
                    # Extract parameters from the line
                    line_start = content.rfind("\n", 0, match.start()) + 1
                    line_end = content.find("\n", match.end())
                    line = content[line_start:line_end] if line_end != -1 else content[line_start:]
                    parameters = self._extract_cmdlet_parameters(line, cmdlet_name)

                    cmdlets.append(
                        CmdletInfo(
                            name=cmdlet_name,
                            file_path=str(full_path.relative_to(self.base_path)),
                            parameters=parameters,
                        )
                    )
                    seen_cmdlets[cmdlet_name] = True
        except Exception as e:
            print(f"Error analyzing PowerShell cmdlets in {file_path}: {e}")

        return cmdlets

    def _parse_parameters(self, param_str: str) -> list[dict[str, Any]]:  # noqa: C901
        """Parse PowerShell parameter string."""
        parameters = []
        if not param_str.strip():
            return parameters

        # Split by comma, but respect nested brackets
        param_parts = []
        current = ""
        depth = 0

        for char in param_str:
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
            elif char == "," and depth == 0:
                if current.strip():
                    param_parts.append(current.strip())
                current = ""
                continue
            current += char

        if current.strip():
            param_parts.append(current.strip())

        for part in param_parts:
            part = part.strip()
            if not part:
                continue

            # Extract parameter name and type
            if "[" in part and "]" in part:
                type_match = re.search(r"\[([^\]]+)\]", part)
                param_type = type_match.group(1) if type_match else "object"
                param_name = re.sub(r"\[[^\]]+\]", "", part).strip("$").strip()
            else:
                param_type = "object"
                param_name = part.strip("$").strip()

            if param_name:
                parameters.append({"name": param_name, "type": param_type})

        return parameters

    def _extract_comment_help(self, content: str, function_start: int) -> str | None:
        """Extract comment-based help before function."""
        # Look backwards for <# ... #> comment block
        before_content = content[:function_start]
        comment_pattern = r"<#([^#]+)#>"
        matches = list(re.finditer(comment_pattern, before_content, re.DOTALL))
        if matches:
            return matches[-1].group(1).strip()
        return None

    def _extract_cmdlet_parameters(self, line: str, cmdlet_name: str) -> list[str]:
        """Extract parameters from cmdlet call line."""
        parameters = []
        # Look for -ParameterName patterns
        param_pattern = r"-([A-Za-z]+)"
        matches = re.finditer(param_pattern, line)
        for match in matches:
            param_name = match.group(1)
            if param_name not in parameters:
                parameters.append(param_name)
        return parameters
