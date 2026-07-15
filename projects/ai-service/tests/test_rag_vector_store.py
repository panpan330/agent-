import json
from uuid import UUID

import httpx
import pytest

from app.core.config import Settings
from app.rag.embeddings import EmbeddedChunk
from app.rag.vector_store import (
    QdrantCollectionConfigError,
    QdrantVectorStore,
    QdrantVectorStoreError,
    build_qdrant_point,
    build_qdrant_point_id,
)


def make_embedded_chunk(**overrides) -> EmbeddedChunk:
    payload = {
        "chunk_id": "shipping_chunk_0001",
        "content": "Orders ship within 24 hours.",
        "metadata": {
            "source": "shipping.md",
            "title": "Shipping Policy",
            "file_name": "shipping.md",
            "file_extension": ".md",
            "doc_type": "policy",
            "business_domain": "order",
            "permission_group": "customer_service",
            "chunk_id": "shipping_chunk_0001",
            "chunk_index": 1,
            "chunk_count": 1,
            "chunk_size_chars": 29,
        },
        "vector": [0.1, 0.2, 0.3, 0.4],
    }
    payload.update(overrides)
    return EmbeddedChunk(**payload)


def make_store(handler) -> QdrantVectorStore:
    return QdrantVectorStore(
        base_url="http://qdrant.test",
        collection_name="learning_chunks",
        timeout_seconds=1.0,
        api_key="test-api-key",
        transport=httpx.MockTransport(handler),
    )


def test_build_qdrant_point_id_returns_stable_uuid() -> None:
    first = build_qdrant_point_id("shipping_chunk_0001")
    second = build_qdrant_point_id("shipping_chunk_0001")

    assert first == second
    assert UUID(first)


def test_build_qdrant_point_keeps_content_and_metadata_in_payload() -> None:
    embedded = make_embedded_chunk()

    point = build_qdrant_point(embedded)

    assert point["id"] == build_qdrant_point_id("shipping_chunk_0001")
    assert point["vector"] == [0.1, 0.2, 0.3, 0.4]
    assert point["payload"]["chunk_id"] == "shipping_chunk_0001"
    assert point["payload"]["content"] == "Orders ship within 24 hours."
    assert point["payload"]["source"] == "shipping.md"
    assert point["payload"]["permission_group"] == "customer_service"


def test_qdrant_store_creates_collection_when_missing() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(404, json={"status": "error"}, request=request)
        body = json.loads(request.content.decode("utf-8"))
        assert request.method == "PUT"
        assert body == {"vectors": {"size": 4, "distance": "Cosine"}}
        assert request.headers["api-key"] == "test-api-key"
        return httpx.Response(200, json={"status": "ok", "result": True}, request=request)

    store = make_store(handler)

    store.ensure_collection(vector_size=4)

    assert [request.method for request in requests] == ["GET", "PUT"]
    assert requests[0].url.path == "/collections/learning_chunks"


def test_qdrant_store_accepts_existing_matching_collection() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "result": {
                    "config": {
                        "params": {
                            "vectors": {"size": 4, "distance": "Cosine"},
                        }
                    }
                },
            },
            request=request,
        )

    store = make_store(handler)

    store.ensure_collection(vector_size=4)

    assert [request.method for request in requests] == ["GET"]


def test_qdrant_store_rejects_existing_collection_with_different_vector_size() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "result": {
                    "config": {
                        "params": {
                            "vectors": {"size": 8, "distance": "Cosine"},
                        }
                    }
                },
            },
            request=request,
        )

    store = make_store(handler)

    with pytest.raises(QdrantCollectionConfigError, match="does not match"):
        store.ensure_collection(vector_size=4)


def test_qdrant_store_upserts_embedded_chunks() -> None:
    captured_body: dict | None = None
    captured_url: httpx.URL | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body, captured_url
        captured_url = request.url
        captured_body = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "result": {"status": "acknowledged", "operation_id": 1},
            },
            request=request,
        )

    store = make_store(handler)

    count = store.upsert_embedded_chunks([make_embedded_chunk()], wait=True)

    assert count == 1
    assert captured_url is not None
    assert captured_url.path == "/collections/learning_chunks/points"
    assert captured_url.params["wait"] == "true"
    assert captured_body is not None
    assert captured_body["points"][0]["payload"]["chunk_id"] == "shipping_chunk_0001"
    assert captured_body["points"][0]["payload"]["content"] == "Orders ship within 24 hours."


def test_qdrant_store_returns_zero_when_no_chunks_need_upsert() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("empty upsert should not call Qdrant")

    store = make_store(handler)

    assert store.upsert_embedded_chunks([]) == 0


def test_qdrant_store_rejects_mismatched_vector_sizes_before_upsert() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("invalid vectors should not call Qdrant")

    store = make_store(handler)
    first = make_embedded_chunk(chunk_id="chunk_0001", vector=[0.1, 0.2])
    second = make_embedded_chunk(chunk_id="chunk_0002", vector=[0.1, 0.2, 0.3])

    with pytest.raises(ValueError, match="same size"):
        store.upsert_embedded_chunks([first, second])


def test_qdrant_store_maps_http_error_to_vector_store_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"status": "error"}, request=request)

    store = make_store(handler)

    with pytest.raises(QdrantVectorStoreError, match="status 500"):
        store.upsert_embedded_chunks([make_embedded_chunk()])


def test_qdrant_store_validates_payload_metadata_before_upsert() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("invalid payload should not call Qdrant")

    store = make_store(handler)
    embedded_chunk = make_embedded_chunk(
        metadata={
            "source": "shipping.md",
            "title": "Shipping Policy",
        }
    )

    with pytest.raises(ValueError, match="file_name"):
        store.upsert_embedded_chunks([embedded_chunk])


def test_qdrant_store_from_settings_uses_qdrant_config() -> None:
    settings = Settings(
        qdrant_base_url=" http://localhost:6333/ ",
        qdrant_collection_name="demo_chunks",
        qdrant_timeout_seconds=2.5,
        qdrant_api_key="secret",
        _env_file=None,
    )

    store = QdrantVectorStore.from_settings(settings)

    assert store.base_url == "http://localhost:6333"
    assert store.collection_name == "demo_chunks"
    assert store.timeout_seconds == 2.5
    assert store.api_key == "secret"
