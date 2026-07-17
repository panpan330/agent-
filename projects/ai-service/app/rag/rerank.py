from collections import Counter
from collections.abc import Iterable, Sequence
from typing import Protocol

from pydantic import BaseModel, Field, field_validator

from app.rag.documents import Metadata, RetrievedChunk
from app.rag.hybrid import HybridSearchResult, KeywordSearchResult, extract_keyword_terms


DEFAULT_RERANK_TOP_K = 3
CONTENT_MATCH_WEIGHT = 0.55
TITLE_SECTION_MATCH_WEIGHT = 0.2
RETRIEVAL_SCORE_WEIGHT = 0.15
SOURCE_AGREEMENT_WEIGHT = 0.1


class RerankCandidate(BaseModel):
    chunk_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    metadata: Metadata = Field(default_factory=dict)
    retrieval_score: float | None = Field(default=None, ge=0)
    retrieval_sources: list[str] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)

    @field_validator("retrieval_score", mode="before")
    @classmethod
    def reject_bool_retrieval_score(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("retrieval_score must be a number")
        return value


class RerankScoreBreakdown(BaseModel):
    content_match_score: float = Field(ge=0, le=1)
    title_section_match_score: float = Field(ge=0, le=1)
    normalized_retrieval_score: float = Field(ge=0, le=1)
    source_agreement_score: float = Field(ge=0, le=1)


class RerankedChunk(BaseModel):
    chunk_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    metadata: Metadata = Field(default_factory=dict)
    retrieval_score: float | None = None
    rerank_score: float = Field(ge=0, le=1)
    original_rank: int = Field(ge=1)
    rerank_rank: int = Field(ge=1)
    score_breakdown: RerankScoreBreakdown
    retrieval_sources: list[str] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)


class Reranker(Protocol):
    def rerank(
        self,
        query: str,
        candidates: Sequence[RerankCandidate],
        *,
        top_k: int = DEFAULT_RERANK_TOP_K,
    ) -> list[RerankedChunk]:
        """Reorder already-retrieved candidates for a query."""


class RuleBasedReranker:
    def rerank(
        self,
        query: str,
        candidates: Sequence[RerankCandidate],
        *,
        top_k: int = DEFAULT_RERANK_TOP_K,
    ) -> list[RerankedChunk]:
        return rerank_candidates(query, candidates, top_k=top_k)


def make_rerank_candidates_from_retrieved_chunks(
    chunks: Sequence[RetrievedChunk],
) -> list[RerankCandidate]:
    return [
        RerankCandidate(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            metadata=chunk.metadata,
            retrieval_score=chunk.score,
            retrieval_sources=["vector"],
        )
        for chunk in chunks
    ]


def make_rerank_candidates_from_keyword_results(
    results: Sequence[KeywordSearchResult],
) -> list[RerankCandidate]:
    return [
        RerankCandidate(
            chunk_id=result.chunk_id,
            content=result.content,
            metadata=result.metadata,
            retrieval_score=result.score,
            retrieval_sources=["keyword"],
            matched_terms=result.matched_terms,
        )
        for result in results
    ]


def make_rerank_candidates_from_hybrid_results(
    results: Sequence[HybridSearchResult],
) -> list[RerankCandidate]:
    return [
        RerankCandidate(
            chunk_id=result.chunk_id,
            content=result.content,
            metadata=result.metadata,
            retrieval_score=result.hybrid_score,
            retrieval_sources=result.retrieval_sources,
            matched_terms=result.matched_terms,
        )
        for result in results
    ]


def rerank_candidates(
    query: str,
    candidates: Sequence[RerankCandidate],
    *,
    top_k: int = DEFAULT_RERANK_TOP_K,
) -> list[RerankedChunk]:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be blank")
    _validate_positive_top_k(top_k)

    query_terms = extract_keyword_terms(normalized_query)
    if not query_terms:
        raise ValueError("query must contain searchable terms")

    max_retrieval_score = max(
        (
            candidate.retrieval_score
            for candidate in candidates
            if candidate.retrieval_score is not None
        ),
        default=0.0,
    )

    scored_payloads: list[dict[str, object]] = []
    for original_rank, candidate in enumerate(candidates, start=1):
        breakdown = _build_score_breakdown(
            query_terms,
            candidate,
            max_retrieval_score=max_retrieval_score,
        )
        matched_terms = _merge_terms(
            candidate.matched_terms,
            _matched_terms(query_terms, extract_keyword_terms(candidate.content)),
            _matched_terms(query_terms, _title_section_terms(candidate.metadata)),
        )
        rerank_score = round(
            breakdown.content_match_score * CONTENT_MATCH_WEIGHT
            + breakdown.title_section_match_score * TITLE_SECTION_MATCH_WEIGHT
            + breakdown.normalized_retrieval_score * RETRIEVAL_SCORE_WEIGHT
            + breakdown.source_agreement_score * SOURCE_AGREEMENT_WEIGHT,
            6,
        )
        scored_payloads.append(
            {
                "chunk_id": candidate.chunk_id,
                "content": candidate.content,
                "metadata": candidate.metadata,
                "retrieval_score": candidate.retrieval_score,
                "rerank_score": rerank_score,
                "original_rank": original_rank,
                "score_breakdown": breakdown,
                "retrieval_sources": candidate.retrieval_sources,
                "matched_terms": matched_terms,
            }
        )

    sorted_payloads = sorted(
        scored_payloads,
        key=lambda payload: (
            -float(payload["rerank_score"]),
            -payload["score_breakdown"].content_match_score,
            -payload["score_breakdown"].title_section_match_score,
            int(payload["original_rank"]),
            str(payload["chunk_id"]),
        ),
    )[:top_k]

    return [
        RerankedChunk(
            **payload,
            rerank_rank=rerank_rank,
        )
        for rerank_rank, payload in enumerate(sorted_payloads, start=1)
    ]


def reranked_chunks_to_retrieved_chunks(
    chunks: Sequence[RerankedChunk],
) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            point_id=str(chunk.metadata.get("point_id", chunk.chunk_id)),
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            metadata=chunk.metadata,
            score=chunk.rerank_score,
        )
        for chunk in chunks
    ]


def format_reranked_chunks_for_debug(chunks: Sequence[RerankedChunk]) -> list[str]:
    lines: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        source = chunk.metadata.get("source", "unknown-source")
        section = chunk.metadata.get("section", "unknown-section")
        sources = ",".join(chunk.retrieval_sources) or "unknown"
        matched = ",".join(chunk.matched_terms[:6]) or "-"
        lines.append(
            (
                f"{index}. rerank_score={chunk.rerank_score:.4f} "
                f"original_rank={chunk.original_rank} "
                f"retrieval_score={_format_optional_score(chunk.retrieval_score)} "
                f"content_match={chunk.score_breakdown.content_match_score:.4f} "
                f"title_section_match={chunk.score_breakdown.title_section_match_score:.4f} "
                f"sources={sources} source={source} section={section} "
                f"chunk_id={chunk.chunk_id} matched={matched}"
            )
        )
    return lines


def _build_score_breakdown(
    query_terms: Sequence[str],
    candidate: RerankCandidate,
    *,
    max_retrieval_score: float,
) -> RerankScoreBreakdown:
    content_score = _weighted_overlap_score(
        query_terms,
        extract_keyword_terms(candidate.content),
    )
    title_section_score = _weighted_overlap_score(
        query_terms,
        _title_section_terms(candidate.metadata),
    )
    normalized_retrieval_score = _normalize_score(
        candidate.retrieval_score,
        max_retrieval_score,
    )
    return RerankScoreBreakdown(
        content_match_score=content_score,
        title_section_match_score=title_section_score,
        normalized_retrieval_score=normalized_retrieval_score,
        source_agreement_score=_source_agreement_score(candidate.retrieval_sources),
    )


def _title_section_terms(metadata: Metadata) -> list[str]:
    values = [
        value
        for key in ("title", "section")
        if isinstance((value := metadata.get(key)), str)
    ]
    return extract_keyword_terms("\n".join(values))


def _weighted_overlap_score(
    query_terms: Sequence[str],
    target_terms: Sequence[str],
) -> float:
    if not query_terms:
        return 0.0
    term_counts = Counter(target_terms)
    total_weight = sum(_term_weight(term) for term in query_terms)
    matched_weight = sum(
        _term_weight(term) * min(term_counts[term], 2)
        for term in query_terms
        if term_counts.get(term, 0) > 0
    )
    return round(min(matched_weight / total_weight, 1.0), 6)


def _matched_terms(
    query_terms: Sequence[str],
    target_terms: Sequence[str],
) -> list[str]:
    term_counts = Counter(target_terms)
    return [
        term
        for term in query_terms
        if term_counts.get(term, 0) > 0
    ]


def _normalize_score(score: float | None, max_score: float) -> float:
    if score is None or max_score <= 0:
        return 0.0
    return round(min(score / max_score, 1.0), 6)


def _source_agreement_score(retrieval_sources: Sequence[str]) -> float:
    unique_sources = set(retrieval_sources)
    return 1.0 if len(unique_sources) >= 2 else 0.0


def _term_weight(term: str) -> int:
    return max(len(term), 1)


def _validate_positive_top_k(top_k: int) -> None:
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")


def _merge_terms(*term_groups: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in term_groups:
        for term in group:
            if term in seen:
                continue
            merged.append(term)
            seen.add(term)
    return merged


def _format_optional_score(score: float | None) -> str:
    if score is None:
        return "none"
    return f"{score:.4f}"
