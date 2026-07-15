import pytest

from app.rag.documents import RagChunk
from app.rag.embeddings import DeterministicHashEmbeddingModel, embed_chunks


def test_hash_embedding_model_returns_stable_vectors() -> None:
    model = DeterministicHashEmbeddingModel(dimension=4)

    first = model.embed_texts(["shipping policy"])
    second = model.embed_texts(["shipping policy"])

    assert first == second
    assert len(first[0]) == 4
    assert all(0 <= value <= 1 for value in first[0])


def test_hash_embedding_model_rejects_invalid_dimension() -> None:
    with pytest.raises(ValueError, match="dimension"):
        DeterministicHashEmbeddingModel(dimension=0)


def test_hash_embedding_model_rejects_blank_text() -> None:
    model = DeterministicHashEmbeddingModel(dimension=4)

    with pytest.raises(ValueError, match="must not be blank"):
        model.embed_texts(["   "])


def test_embed_chunks_preserves_chunk_content_metadata_and_vector() -> None:
    model = DeterministicHashEmbeddingModel(dimension=4)
    chunk = RagChunk(
        chunk_id="shipping_chunk_0001",
        content="Orders ship within 24 hours.",
        metadata={"source": "shipping.md", "chunk_index": 1},
    )

    embedded_chunks = embed_chunks([chunk], embedding_model=model)

    assert len(embedded_chunks) == 1
    embedded = embedded_chunks[0]
    assert embedded.chunk_id == "shipping_chunk_0001"
    assert embedded.content == "Orders ship within 24 hours."
    assert embedded.metadata["source"] == "shipping.md"
    assert len(embedded.vector) == 4


def test_embed_chunks_rejects_vector_count_mismatch() -> None:
    class BadCountEmbeddingModel:
        dimension = 4

        def embed_texts(self, texts):
            return []

    chunk = RagChunk(
        chunk_id="chunk_0001",
        content="content",
        metadata={"source": "demo.md"},
    )

    with pytest.raises(ValueError, match="result count"):
        embed_chunks([chunk], embedding_model=BadCountEmbeddingModel())


def test_embed_chunks_rejects_vector_dimension_mismatch() -> None:
    class BadDimensionEmbeddingModel:
        dimension = 4

        def embed_texts(self, texts):
            return [[0.1, 0.2]]

    chunk = RagChunk(
        chunk_id="chunk_0001",
        content="content",
        metadata={"source": "demo.md"},
    )

    with pytest.raises(ValueError, match="vector size"):
        embed_chunks([chunk], embedding_model=BadDimensionEmbeddingModel())
