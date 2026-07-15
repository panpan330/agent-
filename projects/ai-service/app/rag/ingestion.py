from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from app.rag.embeddings import EmbeddingModel, embed_chunks
from app.rag.loaders import load_documents_from_directory
from app.rag.splitters import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    split_documents_into_chunks,
)


class VectorStoreWriter(Protocol):
    collection_name: str

    def ensure_collection(self, *, vector_size: int, distance: str = "Cosine") -> None:
        """Create or validate the target vector collection."""

    def upsert_embedded_chunks(self, embedded_chunks, *, wait: bool = True) -> int:
        """Write embedded chunks to the vector store."""


class RagIngestionResult(BaseModel):
    document_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    vector_count: int = Field(ge=0)
    vector_dimension: int = Field(gt=0)
    collection_name: str = Field(min_length=1)


def ingest_directory_to_vector_store(
    directory: Path | str,
    *,
    embedding_model: EmbeddingModel,
    vector_store: VectorStoreWriter,
    include_readme: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    distance: str = "Cosine",
    wait: bool = True,
) -> RagIngestionResult:
    documents = load_documents_from_directory(directory, include_readme=include_readme)
    chunks = split_documents_into_chunks(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    embedded_chunks = embed_chunks(chunks, embedding_model=embedding_model)

    vector_store.ensure_collection(
        vector_size=embedding_model.dimension,
        distance=distance,
    )
    vector_count = vector_store.upsert_embedded_chunks(embedded_chunks, wait=wait)

    return RagIngestionResult(
        document_count=len(documents),
        chunk_count=len(chunks),
        vector_count=vector_count,
        vector_dimension=embedding_model.dimension,
        collection_name=vector_store.collection_name,
    )
