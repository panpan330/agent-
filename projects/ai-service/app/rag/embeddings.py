from collections.abc import Sequence
import hashlib
from typing import Protocol

from pydantic import BaseModel, Field

from app.rag.documents import Metadata, RagChunk


Vector = list[float]


class EmbeddingModel(Protocol):
    @property
    def dimension(self) -> int:
        """Number of float values returned for each text."""

    def embed_texts(self, texts: Sequence[str]) -> list[Vector]:
        """Convert each input text into one vector."""


class EmbeddedChunk(BaseModel):
    chunk_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    metadata: Metadata = Field(default_factory=dict)
    vector: Vector = Field(min_length=1)


class DeterministicHashEmbeddingModel:
    """Deterministic placeholder embedding model used before real embedding APIs."""

    def __init__(self, *, dimension: int = 8) -> None:
        if dimension <= 0:
            raise ValueError("embedding dimension must be greater than 0")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: Sequence[str]) -> list[Vector]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> Vector:
        if not text.strip():
            raise ValueError("text to embed must not be blank")

        vector: Vector = []
        for index in range(self.dimension):
            seed = f"{index}:{text}".encode("utf-8")
            digest = hashlib.sha256(seed).digest()
            raw_value = int.from_bytes(digest[:8], byteorder="big", signed=False)
            vector.append(round(raw_value / 2**64, 6))
        return vector


def embed_chunks(
    chunks: Sequence[RagChunk],
    *,
    embedding_model: EmbeddingModel,
) -> list[EmbeddedChunk]:
    texts = [chunk.content for chunk in chunks]
    vectors = embedding_model.embed_texts(texts)

    if len(vectors) != len(chunks):
        raise ValueError("embedding result count must match chunk count")

    embedded_chunks: list[EmbeddedChunk] = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        if len(vector) != embedding_model.dimension:
            raise ValueError("embedding vector size must match model dimension")
        embedded_chunks.append(
            EmbeddedChunk(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                metadata=chunk.metadata,
                vector=vector,
            )
        )
    return embedded_chunks
