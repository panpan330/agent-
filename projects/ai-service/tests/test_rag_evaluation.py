import json

import pytest

from app.rag.evaluation import (
    RetrievalEvalCase,
    evaluate_retrieval_case,
    evaluate_retrieval_results,
    format_retrieval_bad_cases,
    format_retrieval_eval_summary,
    load_retrieval_eval_cases,
)
from tests.rag_fakes import make_retrieved_chunk


def make_case(**overrides) -> RetrievalEvalCase:
    payload = {
        "id": "refund_shipping_fee_001",
        "query": "退货运费谁承担？",
        "expected_sources": ["refund-return-policy.md"],
        "expected_sections": ["运费处理"],
        "expected_chunk_ids": ["refund_return_policy_chunk_0005"],
        "permission_group": "customer_service",
        "business_domain": "refund",
    }
    payload.update(overrides)
    return RetrievalEvalCase(**payload)


def test_evaluate_retrieval_case_calculates_hit_recall_precision_and_mrr() -> None:
    eval_case = make_case()
    chunks = [
        make_retrieved_chunk(
            chunk_id="refund_return_policy_chunk_0002",
            metadata={
                "source": "refund-return-policy.md",
                "section": "七天无理由退货",
            },
            score=0.95,
        ),
        make_retrieved_chunk(
            chunk_id="refund_return_policy_chunk_0005",
            metadata={
                "source": "refund-return-policy.md",
                "section": "运费处理",
            },
            score=0.88,
        ),
        make_retrieved_chunk(
            chunk_id="order_shipping_policy_chunk_0002",
            metadata={
                "source": "order-shipping-policy.md",
                "section": "正常发货时效",
            },
            score=0.5,
        ),
    ]

    result = evaluate_retrieval_case(eval_case, chunks, top_k=3)

    assert result.match_level == "chunk_id"
    assert result.hit is True
    assert result.first_relevant_rank == 2
    assert result.matched_expected_count == 1
    assert result.relevant_retrieved_count == 1
    assert result.recall_at_k == 1.0
    assert result.precision_at_k == 0.333333
    assert result.reciprocal_rank == 0.5
    assert result.passed is True
    assert [item.relevant for item in result.retrieved_items] == [
        False,
        True,
        False,
    ]


def test_evaluate_retrieval_case_can_match_section_when_chunk_id_is_not_expected() -> None:
    eval_case = make_case(
        expected_chunk_ids=[],
        expected_sections=["运费处理"],
    )
    chunks = [
        make_retrieved_chunk(
            chunk_id="new_chunk_id_after_resplit",
            metadata={
                "source": "refund-return-policy.md",
                "section": "运费处理",
            },
            score=0.8,
        )
    ]

    result = evaluate_retrieval_case(eval_case, chunks, top_k=3)

    assert result.match_level == "section"
    assert result.passed is True
    assert result.recall_at_k == 1.0
    assert result.precision_at_k == 0.333333


def test_evaluate_retrieval_case_handles_no_result_expectation() -> None:
    eval_case = RetrievalEvalCase(
        id="no_context_membership_points_001",
        query="会员积分怎么兑换？",
        expect_no_results=True,
    )

    passed = evaluate_retrieval_case(eval_case, [], top_k=3)
    failed = evaluate_retrieval_case(
        eval_case,
        [make_retrieved_chunk()],
        top_k=3,
    )

    assert passed.metric_applicable is False
    assert passed.passed is True
    assert passed.precision_at_k == 1.0
    assert failed.passed is False
    assert failed.failed_reason == "expected no results but retrieved chunks"


def test_evaluate_retrieval_results_summarizes_metrics_and_bad_cases() -> None:
    passing_case = make_case(id="passing")
    failing_case = make_case(id="failing")
    no_result_case = RetrievalEvalCase(
        id="no_result",
        query="会员积分怎么兑换？",
        expect_no_results=True,
    )

    summary = evaluate_retrieval_results(
        [passing_case, failing_case, no_result_case],
        {
            "passing": [
                make_retrieved_chunk(
                    chunk_id="refund_return_policy_chunk_0005",
                    metadata={
                        "source": "refund-return-policy.md",
                        "section": "运费处理",
                    },
                    score=0.9,
                )
            ],
            "failing": [
                make_retrieved_chunk(
                    chunk_id="order_shipping_policy_chunk_0002",
                    metadata={
                        "source": "order-shipping-policy.md",
                        "section": "正常发货时效",
                    },
                    score=0.7,
                )
            ],
            "no_result": [],
        },
        top_k=3,
    )

    assert summary.case_count == 3
    assert summary.evaluated_case_count == 2
    assert summary.no_result_case_count == 1
    assert summary.passed_case_count == 2
    assert summary.failed_case_count == 1
    assert summary.hit_rate_at_k == 0.5
    assert summary.recall_at_k == 0.5
    assert summary.precision_at_k == pytest.approx(0.166666)
    assert summary.mrr_at_k == 0.5
    assert summary.no_result_success_rate == 1.0

    summary_lines = format_retrieval_eval_summary(summary)
    bad_case_lines = format_retrieval_bad_cases(summary)

    assert "hit_rate@3: 0.5000" in summary_lines
    assert any("failing" in line for line in bad_case_lines)


def test_load_retrieval_eval_cases_validates_json_file(tmp_path) -> None:
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "id": "case_1",
                    "query": "退货运费谁承担？",
                    "expected_sources": ["refund-return-policy.md"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    cases = load_retrieval_eval_cases(cases_path)

    assert len(cases) == 1
    assert cases[0].id == "case_1"
    assert cases[0].expected_sources == ["refund-return-policy.md"]


def test_retrieval_eval_case_rejects_missing_targets_and_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="expected targets"):
        RetrievalEvalCase(id="missing", query="退货运费谁承担？")

    with pytest.raises(ValueError, match="no-result"):
        RetrievalEvalCase(
            id="conflict",
            query="会员积分怎么兑换？",
            expect_no_results=True,
            expected_sources=["refund-return-policy.md"],
        )

    with pytest.raises(ValueError, match="unique"):
        evaluate_retrieval_results(
            [
                make_case(id="duplicate"),
                make_case(id="duplicate"),
            ],
            {},
            top_k=3,
        )


def test_evaluate_retrieval_case_rejects_invalid_top_k() -> None:
    with pytest.raises(ValueError, match="top_k"):
        evaluate_retrieval_case(make_case(), [], top_k=0)
