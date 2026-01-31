# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Document text extraction service.
"""
import io
from typing import Tuple

import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from docx import Document as DocxDocument


class DocumentExtractor:
    """Extract text from various document formats."""

    @staticmethod
    def extract_text(file_content: bytes, file_type: str) -> Tuple[str, list]:
        """
        Extract text from document.

        Returns:
            Tuple of (text_content, headings_list)
        """
        if file_type == "pdf":
            return DocumentExtractor._extract_pdf(file_content)
        elif file_type in ["docx", "doc"]:
            return DocumentExtractor._extract_docx(file_content)
        elif file_type in ["html", "htm"]:
            return DocumentExtractor._extract_html(file_content)
        elif file_type in ["txt", "md"]:
            return DocumentExtractor._extract_text_plain(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _extract_pdf(content: bytes) -> Tuple[str, list]:
        """Extract text from PDF."""
        doc = fitz.open(stream=content, filetype="pdf")
        text_parts = []
        headings = []

        for page_num, page in enumerate(doc):
            text = page.get_text()
            text_parts.append(text)

            # Try to extract headings (text with larger font)
            blocks = page.get_text("dict")
            for block in blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            font_size = span.get("size", 0)
                            if font_size > 12:  # Heuristic for headings
                                text_content = span.get("text", "").strip()
                                if text_content and len(text_content) < 100:
                                    headings.append(text_content)

        doc.close()
        return "\n\n".join(text_parts), headings

    @staticmethod
    def _extract_docx(content: bytes) -> Tuple[str, list]:
        """Extract text from DOCX."""
        doc = DocxDocument(io.BytesIO(content))
        text_parts = []
        headings = []

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                text_parts.append(text)
                # Check if it's a heading style
                if paragraph.style.name.startswith("Heading"):
                    headings.append(text)

        return "\n\n".join(text_parts), headings

    @staticmethod
    def _extract_html(content: bytes) -> Tuple[str, list]:
        """Extract text from HTML."""
        soup = BeautifulSoup(content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract headings
        headings = [h.get_text().strip() for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])]

        # Extract text
        text = soup.get_text(separator="\n\n")

        return text, headings

    @staticmethod
    def _extract_text_plain(content: bytes) -> Tuple[str, list]:
        """Extract text from plain text files."""
        text = content.decode("utf-8", errors="ignore")
        # Simple heading detection: lines that are short and end with colon or are all caps
        lines = text.split("\n")
        headings = []
        for line in lines[:50]:  # Check first 50 lines
            stripped = line.strip()
            if (
                stripped
                and len(stripped) < 80
                and (stripped.endswith(":") or stripped.isupper())
                and len(stripped.split()) < 10
            ):
                headings.append(stripped)

        return text, headings
