import pytest

from app.rag.hybrid import HybridSearchResult, KeywordSearchResult
from app.rag.rerank import (
    RerankCandidate,
    RuleBasedReranker,
    format_reranked_chunks_for_debug,
    make_rerank_candidates_from_hybrid_results,
    make_rerank_candidates_from_keyword_results,
    make_rerank_candidates_from_retrieved_chunks,
    rerank_candidates,
    reranked_chunks_to_retrieved_chunks,
)
from tests.rag_fakes import make_retrieved_chunk


def make_candidate(**overrides) -> RerankCandidate:
    payload = {
        "chunk_id": "refund_arrival_chunk",
        "content": "退货商品入库并审核通过后，退款通常会在 1 到 3 个工作日内原路退回。",
        "metadata": {
            "source": "refund-return-policy.md",
            "title": "退款退货规则",
            "section": "退款到账时间",
            "permission_group": "customer_service",
        },
        "retrieval_score": 0.7,
        "retrieval_sources": ["vector"],
    }
    payload.update(overrides)
    return RerankCandidate(**payload)


def test_rerank_candidates_moves_more_relevant_chunk_to_top() -> None:
    candidates = [
        make_candidate(
            chunk_id="logistics_refund_chunk",
            content="物流异常不能直接退款，需要先确认订单状态和异常原因。",
            metadata={"source": "logistics.txt", "section": "物流异常可以直接退款吗"},
            retrieval_score=0.99,
        ),
        make_candidate(
            chunk_id="refund_arrival_chunk",
            content="退货商品入库并审核通过后，退款通常会在 1 到 3 个工作日内原路退回。如果超过 3 个工作日仍未到账，客服需要核查退款流水状态。",
            metadata={
                "source": "refund-return-policy.md",
                "title": "退款退货规则",
                "section": "退款到账时间",
            },
            retrieval_score=0.72,
        ),
    ]

    results = rerank_candidates("退款多久到账？", candidates, top_k=2)

    assert [result.chunk_id for result in results] == [
        "refund_arrival_chunk",
        "logistics_refund_chunk",
    ]
    assert results[0].original_rank == 2
    assert results[0].rerank_rank == 1
    assert "到账" in results[0].matched_terms


def test_rerank_candidates_records_score_breakdown() -> None:
    results = rerank_candidates(
        "退款到账",
        [
            make_candidate(
                retrieval_score=0.5,
                retrieval_sources=["vector", "keyword"],
                matched_terms=["退款"],
            )
        ],
        top_k=1,
    )

    result = results[0]

    assert result.score_breakdown.content_match_score > 0
    assert result.score_breakdown.title_section_match_score > 0
    assert result.score_breakdown.normalized_retrieval_score == 1
    assert result.score_breakdown.source_agreement_score == 1
    assert result.retrieval_sources == ["vector", "keyword"]
    assert "退款" in result.matched_terms


def test_rerank_candidates_limits_top_k_and_uses_stable_tie_breaker() -> None:
    candidates = [
        make_candidate(chunk_id="chunk-b", retrieval_score=0.5),
        make_candidate(chunk_id="chunk-a", retrieval_score=0.5),
    ]

    results = rerank_candidates("退款到账", candidates, top_k=1)

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-b"


def test_rerank_candidates_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="query"):
        rerank_candidates("   ", [make_candidate()])

    with pytest.raises(ValueError, match="top_k"):
        rerank_candidates("退款", [make_candidate()], top_k=0)

    with pytest.raises(ValueError, match="retrieval_score"):
        RerankCandidate(
            chunk_id="bad",
            content="退款到账",
            retrieval_score=True,
        )


def test_make_rerank_candidates_from_retrieved_chunks() -> None:
    chunks = [
        make_retrieved_chunk(
            chunk_id="chunk-1",
            content="订单通常 48 小时内发货。",
            score=0.88,
            metadata={"source": "shipping.md", "point_id": "point-1"},
        )
    ]

    candidates = make_rerank_candidates_from_retrieved_chunks(chunks)

    assert candidates[0].chunk_id == "chunk-1"
    assert candidates[0].retrieval_score == 0.88
    assert candidates[0].retrieval_sources == ["vector"]


def test_make_rerank_candidates_from_keyword_results() -> None:
    results = [
        KeywordSearchResult(
            chunk_id="chunk-keyword",
            content="退款通常 1 到 3 个工作日到账。",
            metadata={"source": "refund.md"},
            score=0.6,
            matched_terms=["退款", "到账"],
        )
    ]

    candidates = make_rerank_candidates_from_keyword_results(results)

    assert candidates[0].retrieval_score == 0.6
    assert candidates[0].retrieval_sources == ["keyword"]
    assert candidates[0].matched_terms == ["退款", "到账"]


def test_make_rerank_candidates_from_hybrid_results() -> None:
    results = [
        HybridSearchResult(
            chunk_id="chunk-hybrid",
            content="退款通常 1 到 3 个工作日到账。",
            metadata={"source": "refund.md"},
            hybrid_score=0.77,
            vector_score=0.8,
            keyword_score=0.6,
            retrieval_sources=["vector", "keyword"],
            matched_terms=["退款"],
        )
    ]

    candidates = make_rerank_candidates_from_hybrid_results(results)

    assert candidates[0].retrieval_score == 0.77
    assert candidates[0].retrieval_sources == ["vector", "keyword"]


def test_rule_based_reranker_delegates_to_rerank_candidates() -> None:
    reranker = RuleBasedReranker()

    results = reranker.rerank("退款到账", [make_candidate()], top_k=1)

    assert results[0].chunk_id == "refund_arrival_chunk"
    assert results[0].rerank_rank == 1


def test_reranked_chunks_to_retrieved_chunks_uses_rerank_score() -> None:
    reranked = rerank_candidates("退款到账", [make_candidate()], top_k=1)

    chunks = reranked_chunks_to_retrieved_chunks(reranked)

    assert chunks[0].chunk_id == "refund_arrival_chunk"
    assert chunks[0].score == reranked[0].rerank_score
    assert chunks[0].point_id == "refund_arrival_chunk"


def test_format_reranked_chunks_for_debug() -> None:
    reranked = rerank_candidates("退款到账", [make_candidate()], top_k=1)

    lines = format_reranked_chunks_for_debug(reranked)

    assert lines[0].startswith("1. rerank_score=")
    assert "original_rank=1" in lines[0]
    assert "chunk_id=refund_arrival_chunk" in lines[0]
