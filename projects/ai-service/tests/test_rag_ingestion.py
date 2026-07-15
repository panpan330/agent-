from pathlib import Path

from app.rag.embeddings import DeterministicHashEmbeddingModel, EmbeddedChunk
from app.rag.ingestion import ingest_directory_to_vector_store


KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"


class FakeVectorStore:
    collection_name = "fake_chunks"

    def __init__(self) -> None:
        self.vector_size: int | None = None
        self.distance: str | None = None
        self.embedded_chunks: list[EmbeddedChunk] = []

    def ensure_collection(self, *, vector_size: int, distance: str = "Cosine") -> None:
        self.vector_size = vector_size
        self.distance = distance

    def upsert_embedded_chunks(
        self,
        embedded_chunks,
        *,
        wait: bool = True,
    ) -> int:
        self.embedded_chunks = list(embedded_chunks)
        return len(self.embedded_chunks)


def test_ingest_directory_loads_splits_embeds_and_writes_chunks() -> None:
    embedding_model = DeterministicHashEmbeddingModel(dimension=4)
    vector_store = FakeVectorStore()

    result = ingest_directory_to_vector_store(
        KNOWLEDGE_BASE_DIR,
        embedding_model=embedding_model,
        vector_store=vector_store,
        chunk_size=220,
        chunk_overlap=40,
    )

    assert result.document_count >= 1
    assert result.chunk_count == len(vector_store.embedded_chunks)
    assert result.vector_count == len(vector_store.embedded_chunks)
    assert result.vector_dimension == 4
    assert result.collection_name == "fake_chunks"
    assert vector_store.vector_size == 4
    assert vector_store.distance == "Cosine"
    assert vector_store.embedded_chunks[0].metadata["chunk_id"]
