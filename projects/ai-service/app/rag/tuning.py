from collections.abc import Iterable, Sequence

from pydantic import BaseModel, Field, field_validator, model_validator

from app.rag.documents import RagDocument, RetrievedChunk
from app.rag.embeddings import EmbeddingModel
from app.rag.retriever import (
    DEFAULT_TOP_K,
    VectorStoreReader,
    format_retrieved_chunks_for_debug,
    retrieve_top_k,
)
from app.rag.splitters import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    split_documents_into_chunks,
)


class ChunkTuningCase(BaseModel):
    chunk_size: int = Field(default=DEFAULT_CHUNK_SIZE, gt=0)
    chunk_overlap: int = Field(default=DEFAULT_CHUNK_OVERLAP, ge=0)

    @field_validator("chunk_size", "chunk_overlap", mode="before")
    @classmethod
    def reject_bool_ints(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("chunk tuning values must be integers")
        return value

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkTuningCase":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self


class ChunkTuningReport(BaseModel):
    chunk_size: int = Field(gt=0)
    chunk_overlap: int = Field(ge=0)
    document_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    min_chunk_chars: int = Field(ge=0)
    max_chunk_chars: int = Field(ge=0)
    average_chunk_chars: float = Field(ge=0)
    source_count: int = Field(ge=0)


class RetrievalTuningCase(BaseModel):
    top_k: int = Field(default=DEFAULT_TOP_K, gt=0)
    score_threshold: float | None = None

    @field_validator("top_k", mode="before")
    @classmethod
    def reject_bool_top_k(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("top_k must be an integer")
        return value

    @field_validator("score_threshold", mode="before")
    @classmethod
    def validate_score_threshold(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("score_threshold must be a number")
        return value


class RetrievalTuningReport(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(gt=0)
    score_threshold: float | None = None
    result_count: int = Field(ge=0)
    source_count: int = Field(ge=0)
    top_score: float | None = None
    bottom_score: float | None = None
    sources: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)
    debug_lines: list[str] = Field(default_factory=list)


def compare_chunk_tuning_cases(
    documents: Sequence[RagDocument],
    cases: Sequence[ChunkTuningCase],
) -> list[ChunkTuningReport]:
    return [
        build_chunk_tuning_report(
            documents,
            chunk_size=case.chunk_size,
            chunk_overlap=case.chunk_overlap,
        )
        for case in cases
    ]


def build_chunk_tuning_report(
    documents: Sequence[RagDocument],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> ChunkTuningReport:
    case = ChunkTuningCase(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = split_documents_into_chunks(
        list(documents),
        chunk_size=case.chunk_size,
        chunk_overlap=case.chunk_overlap,
    )
    chunk_lengths = [len(chunk.content) for chunk in chunks]
    sources = {
        source
        for chunk in chunks
        if isinstance((source := chunk.metadata.get("source")), str)
    }

    return ChunkTuningReport(
        chunk_size=case.chunk_size,
        chunk_overlap=case.chunk_overlap,
        document_count=len(documents),
        chunk_count=len(chunks),
        min_chunk_chars=min(chunk_lengths, default=0),
        max_chunk_chars=max(chunk_lengths, default=0),
        average_chunk_chars=_average(chunk_lengths),
        source_count=len(sources),
    )


def build_retrieval_tuning_cases(
    *,
    top_ks: Sequence[int],
    score_thresholds: Sequence[float | None],
) -> list[RetrievalTuningCase]:
    return [
        RetrievalTuningCase(top_k=top_k, score_threshold=score_threshold)
        for top_k in top_ks
        for score_threshold in score_thresholds
    ]


def compare_retrieval_tuning_cases(
    query: str,
    *,
    embedding_model: EmbeddingModel,
    vector_store: VectorStoreReader,
    cases: Sequence[RetrievalTuningCase],
    permission_group: str | None = None,
    business_domain: str | None = None,
    doc_type: str | None = None,
    source: str | None = None,
) -> list[RetrievalTuningReport]:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be blank")

    reports: list[RetrievalTuningReport] = []
    for case in cases:
        chunks = retrieve_top_k(
            normalized_query,
            embedding_model=embedding_model,
            vector_store=vector_store,
            top_k=case.top_k,
            permission_group=permission_group,
            business_domain=business_domain,
            doc_type=doc_type,
            source=source,
            score_threshold=case.score_threshold,
        )
        reports.append(
            build_retrieval_tuning_report(
                normalized_query,
                chunks,
                top_k=case.top_k,
                score_threshold=case.score_threshold,
            )
        )
    return reports


def build_retrieval_tuning_report(
    query: str,
    chunks: Sequence[RetrievedChunk],
    *,
    top_k: int,
    score_threshold: float | None = None,
) -> RetrievalTuningReport:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be blank")
    case = RetrievalTuningCase(top_k=top_k, score_threshold=score_threshold)
    scores = [chunk.score for chunk in chunks]
    sources = _unique_strings(
        chunk.metadata.get("source")
        for chunk in chunks
        if isinstance(chunk.metadata.get("source"), str)
    )

    return RetrievalTuningReport(
        query=normalized_query,
        top_k=case.top_k,
        score_threshold=case.score_threshold,
        result_count=len(chunks),
        source_count=len(sources),
        top_score=max(scores, default=None),
        bottom_score=min(scores, default=None),
        sources=sources,
        chunk_ids=[chunk.chunk_id for chunk in chunks],
        debug_lines=format_retrieved_chunks_for_debug(chunks),
    )


def _average(values: Sequence[int]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _unique_strings(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        unique.append(value)
        seen.add(value)
    return unique
