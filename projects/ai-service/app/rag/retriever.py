from collections.abc import Sequence
from typing import Protocol

from app.rag.documents import RetrievedChunk
from app.rag.embeddings import EmbeddingModel, Vector
from app.rag.filters import PayloadFilter, build_payload_filter


DEFAULT_TOP_K = 5


class VectorStoreReader(Protocol):
    def query_similar(
        self,
        query_vector: Vector,
        *,
        top_k: int,
        payload_filter: PayloadFilter | None = None,
        score_threshold: float | None = None,
        with_payload: bool = True,
        with_vector: bool = False,
    ) -> list[RetrievedChunk]:
        """Return the most similar chunks for a query vector."""


def retrieve_top_k(
    query: str,
    *,
    embedding_model: EmbeddingModel,
    vector_store: VectorStoreReader,
    top_k: int = DEFAULT_TOP_K,
    permission_group: str | None = None,
    business_domain: str | None = None,
    doc_type: str | None = None,
    source: str | None = None,
    score_threshold: float | None = None,
) -> list[RetrievedChunk]:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be blank")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")
    _validate_score_threshold(score_threshold)

    vectors = embedding_model.embed_texts([normalized_query])
    if len(vectors) != 1:
        raise ValueError("query embedding result count must be 1")

    query_vector = vectors[0]
    if len(query_vector) != embedding_model.dimension:
        raise ValueError("query embedding vector size must match model dimension")

    payload_filter = build_payload_filter(
        permission_group=permission_group,
        business_domain=business_domain,
        doc_type=doc_type,
        source=source,
    )

    return vector_store.query_similar(
        query_vector,
        top_k=top_k,
        payload_filter=payload_filter,
        score_threshold=score_threshold,
        with_payload=True,
        with_vector=False,
    )


def format_retrieved_chunks_for_debug(chunks: Sequence[RetrievedChunk]) -> list[str]:
    lines: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        source = chunk.metadata.get("source", "unknown-source")
        section = chunk.metadata.get("section", "unknown-section")
        lines.append(
            f"{index}. score={chunk.score:.4f} source={source} section={section} chunk_id={chunk.chunk_id}"
        )
    return lines


def _validate_score_threshold(score_threshold: float | None) -> None:
    if score_threshold is None:
        return
    if not isinstance(score_threshold, int | float) or isinstance(score_threshold, bool):
        raise ValueError("score_threshold must be a number")
