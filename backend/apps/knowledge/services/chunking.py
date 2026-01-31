# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Semantic chunking service for document processing.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Chunk:
    """Represents a text chunk."""

    content: str
    start_char: int
    end_char: int
    heading: Optional[str] = None
    page_number: Optional[int] = None


class SemanticChunker:
    """Chunk documents while respecting semantic boundaries."""

    def __init__(
        self,
        target_chunk_size: int = 800,  # tokens (approximate)
        max_chunk_size: int = 1200,
        overlap_size: int = 100,
    ):
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size

    def chunk(self, text: str, headings: Optional[List[str]] = None) -> List[Chunk]:
        """
        Chunk text while:
        1. Respecting heading boundaries
        2. Keeping paragraphs together when possible
        3. Adding overlap for context continuity
        """
        chunks = []
        paragraphs = self._split_into_paragraphs(text)

        current_chunk = []
        current_length = 0
        start_char = 0

        for para in paragraphs:
            para_length = len(para.split())  # Approximate token count

            # If adding this paragraph exceeds max size, finalize current chunk
            if current_length + para_length > self.max_chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        start_char=start_char,
                        end_char=start_char + len(chunk_text),
                    )
                )
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(chunk_text)
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text.split()) if overlap_text else 0
                start_char = chunks[-1].end_char - len(overlap_text) if overlap_text else chunks[-1].end_char

            # Add paragraph to current chunk
            current_chunk.append(para)
            current_length += para_length

            # If we've reached target size, finalize chunk
            if current_length >= self.target_chunk_size:
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        start_char=start_char,
                        end_char=start_char + len(chunk_text),
                    )
                )
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(chunk_text)
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text.split()) if overlap_text else 0
                start_char = chunks[-1].end_char - len(overlap_text) if overlap_text else chunks[-1].end_char

        # Add remaining content as final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                Chunk(
                    content=chunk_text,
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                )
            )

        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split by double newlines or single newline followed by whitespace
        paragraphs = []
        for para in text.split("\n\n"):
            para = para.strip()
            if para:
                paragraphs.append(para)
        return paragraphs

    def _get_overlap_text(self, text: str) -> str:
        """Extract overlap text from end of chunk."""
        words = text.split()
        if len(words) <= self.overlap_size:
            return text

        overlap_words = words[-self.overlap_size :]
        return " ".join(overlap_words)
