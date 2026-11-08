import re

from app.models.domain import RoleChunk


class TextChunker:
    def __init__(self, chunk_size: int = 250, chunk_overlap: int = 50):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._word_pattern = re.compile(r"\S+")

    def split_into_words(self, text: str) -> list[str]:
        return self._word_pattern.findall(text)

    def chunk_text(self, text: str) -> list[str]:
        words = self.split_into_words(text)
        if not words:
            return []

        if len(words) <= self.chunk_size:
            return [" ".join(words)]

        chunks: list[str] = []
        step = self.chunk_size - self.chunk_overlap
        start = 0
        total_words = len(words)

        while start < total_words:
            end = min(start + self.chunk_size, total_words)
            chunk_slice = words[start:end]
            chunks.append(" ".join(chunk_slice))
            if end >= total_words:
                break
            start += step

        return chunks

    def chunk_role(self, role_number: str, description: str) -> list[RoleChunk]:
        raw_chunks = self.chunk_text(description)
        return [
            RoleChunk(
                chunk_id=f"{role_number}_chunk{idx}",
                role_number=role_number,
                chunk_index=idx,
                text=chunk_text,
            )
            for idx, chunk_text in enumerate(raw_chunks)
        ]
