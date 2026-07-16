import pytest

from app.rag.documents import RetrievedChunk
from app.rag.embeddings import DeterministicHashEmbeddingModel
from app.rag.retriever import format_retrieved_chunks_for_debug, retrieve_top_k


class FakeVectorStoreReader:
    def __init__(self) -> None:
        self.query_vector: list[float] | None = None
        self.top_k: int | None = None
        self.payload_filter: dict | None = None
        self.score_threshold: float | None = None
        self.with_payload: bool | None = None
        self.with_vector: bool | None = None

    def query_similar(
        self,
        query_vector: list[float],
        *,
        top_k: int,
        payload_filter: dict | None = None,
        score_threshold: float | None = None,
        with_payload: bool = True,
        with_vector: bool = False,
    ) -> list[RetrievedChunk]:
        self.query_vector = query_vector
        self.top_k = top_k
        self.payload_filter = payload_filter
        self.score_threshold = score_threshold
        self.with_payload = with_payload
        self.with_vector = with_vector
        return [
            RetrievedChunk(
                point_id="point-1",
                chunk_id="order_shipping_policy_chunk_0001",
                content="订单付款后 24 小时内发货。",
                metadata={
                    "source": "order-shipping-policy.md",
                    "section": "正常发货时效",
                    "chunk_id": "order_shipping_policy_chunk_0001",
                },
                score=0.91,
            )
        ]


def test_retrieve_top_k_embeds_query_and_calls_vector_store() -> None:
    embedding_model = DeterministicHashEmbeddingModel(dimension=4)
    vector_store = FakeVectorStoreReader()

    chunks = retrieve_top_k(
        "  订单多久发货？  ",
        embedding_model=embedding_model,
        vector_store=vector_store,
        top_k=3,
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "order_shipping_policy_chunk_0001"
    assert vector_store.query_vector is not None
    assert len(vector_store.query_vector) == 4
    assert vector_store.top_k == 3
    assert vector_store.payload_filter is None
    assert vector_store.score_threshold is None
    assert vector_store.with_payload is True
    assert vector_store.with_vector is False


def test_retrieve_top_k_rejects_blank_query() -> None:
    embedding_model = DeterministicHashEmbeddingModel(dimension=4)
    vector_store = FakeVectorStoreReader()

    with pytest.raises(ValueError, match="query"):
        retrieve_top_k(
            "   ",
            embedding_model=embedding_model,
            vector_store=vector_store,
        )


def test_retrieve_top_k_rejects_invalid_top_k() -> None:
    embedding_model = DeterministicHashEmbeddingModel(dimension=4)
    vector_store = FakeVectorStoreReader()

    with pytest.raises(ValueError, match="top_k"):
        retrieve_top_k(
            "订单多久发货？",
            embedding_model=embedding_model,
            vector_store=vector_store,
            top_k=0,
        )


def test_retrieve_top_k_passes_payload_filter_to_vector_store() -> None:
    embedding_model = DeterministicHashEmbeddingModel(dimension=4)
    vector_store = FakeVectorStoreReader()

    retrieve_top_k(
        "订单多久发货？",
        embedding_model=embedding_model,
        vector_store=vector_store,
        top_k=3,
        permission_group="customer_service",
        business_domain="order",
        doc_type="policy",
        source="order-shipping-policy.md",
    )

    assert vector_store.payload_filter == {
        "must": [
            {"key": "permission_group", "match": {"value": "customer_service"}},
            {"key": "business_domain", "match": {"value": "order"}},
            {"key": "doc_type", "match": {"value": "policy"}},
            {"key": "source", "match": {"value": "order-shipping-policy.md"}},
        ]
    }


def test_retrieve_top_k_passes_score_threshold_to_vector_store() -> None:
    embedding_model = DeterministicHashEmbeddingModel(dimension=4)
    vector_store = FakeVectorStoreReader()

    retrieve_top_k(
        "订单多久发货？",
        embedding_model=embedding_model,
        vector_store=vector_store,
        score_threshold=0.78,
    )

    assert vector_store.score_threshold == 0.78


def test_retrieve_top_k_rejects_blank_filter_value() -> None:
    embedding_model = DeterministicHashEmbeddingModel(dimension=4)
    vector_store = FakeVectorStoreReader()

    with pytest.raises(ValueError, match="business_domain"):
        retrieve_top_k(
            "订单多久发货？",
            embedding_model=embedding_model,
            vector_store=vector_store,
            business_domain="   ",
        )


def test_retrieve_top_k_rejects_invalid_score_threshold() -> None:
    embedding_model = DeterministicHashEmbeddingModel(dimension=4)
    vector_store = FakeVectorStoreReader()

    with pytest.raises(ValueError, match="score_threshold"):
        retrieve_top_k(
            "订单多久发货？",
            embedding_model=embedding_model,
            vector_store=vector_store,
            score_threshold=True,
        )


def test_retrieve_top_k_rejects_bad_embedding_count() -> None:
    class BadCountEmbeddingModel:
        dimension = 4

        def embed_texts(self, texts):
            return []

    with pytest.raises(ValueError, match="result count"):
        retrieve_top_k(
            "订单多久发货？",
            embedding_model=BadCountEmbeddingModel(),
            vector_store=FakeVectorStoreReader(),
        )


def test_retrieve_top_k_rejects_bad_embedding_dimension() -> None:
    class BadDimensionEmbeddingModel:
        dimension = 4

        def embed_texts(self, texts):
            return [[0.1, 0.2]]

    with pytest.raises(ValueError, match="vector size"):
        retrieve_top_k(
            "订单多久发货？",
            embedding_model=BadDimensionEmbeddingModel(),
            vector_store=FakeVectorStoreReader(),
        )


def test_format_retrieved_chunks_for_debug() -> None:
    lines = format_retrieved_chunks_for_debug(
        [
            RetrievedChunk(
                point_id="point-1",
                chunk_id="order_shipping_policy_chunk_0001",
                content="订单付款后 24 小时内发货。",
                metadata={
                    "source": "order-shipping-policy.md",
                    "section": "正常发货时效",
                },
                score=0.91234,
            )
        ]
    )

    assert lines == [
        "1. score=0.9123 source=order-shipping-policy.md section=正常发货时效 chunk_id=order_shipping_policy_chunk_0001"
    ]
