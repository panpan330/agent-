from pathlib import Path

import pytest

from app.rag.loaders import load_documents_from_directory
from app.rag.tuning import (
    ChunkTuningCase,
    RetrievalTuningCase,
    build_chunk_tuning_report,
    build_retrieval_tuning_cases,
    build_retrieval_tuning_report,
    compare_chunk_tuning_cases,
    compare_retrieval_tuning_cases,
)
from tests.rag_fakes import (
    FakeEmbeddingModel,
    FakeVectorStoreReader,
    make_retrieved_chunk,
)


KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"


def test_build_chunk_tuning_report_summarizes_split_distribution() -> None:
    documents = load_documents_from_directory(KNOWLEDGE_BASE_DIR)

    report = build_chunk_tuning_report(
        documents,
        chunk_size=220,
        chunk_overlap=40,
    )

    assert report.chunk_size == 220
    assert report.chunk_overlap == 40
    assert report.document_count == len(documents)
    assert report.chunk_count > report.document_count
    assert report.min_chunk_chars > 0
    assert report.max_chunk_chars <= 220
    assert report.average_chunk_chars > 0
    assert report.source_count == len(documents)


def test_compare_chunk_tuning_cases_shows_parameter_impact() -> None:
    documents = load_documents_from_directory(KNOWLEDGE_BASE_DIR)

    reports = compare_chunk_tuning_cases(
        documents,
        [
            ChunkTuningCase(chunk_size=160, chunk_overlap=20),
            ChunkTuningCase(chunk_size=320, chunk_overlap=20),
        ],
    )

    assert reports[0].chunk_size == 160
    assert reports[1].chunk_size == 320
    assert reports[0].chunk_count >= reports[1].chunk_count


def test_chunk_tuning_case_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError, match="smaller than chunk_size"):
        ChunkTuningCase(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError, match="integers"):
        ChunkTuningCase(chunk_size=True, chunk_overlap=10)


def test_build_retrieval_tuning_cases_builds_grid() -> None:
    cases = build_retrieval_tuning_cases(
        top_ks=[1, 3],
        score_thresholds=[None, 0.8],
    )

    assert cases == [
        RetrievalTuningCase(top_k=1, score_threshold=None),
        RetrievalTuningCase(top_k=1, score_threshold=0.8),
        RetrievalTuningCase(top_k=3, score_threshold=None),
        RetrievalTuningCase(top_k=3, score_threshold=0.8),
    ]


def test_retrieval_tuning_case_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="top_k"):
        RetrievalTuningCase(top_k=True)

    with pytest.raises(ValueError, match="score_threshold"):
        RetrievalTuningCase(top_k=3, score_threshold=True)


def test_build_retrieval_tuning_report_summarizes_chunks() -> None:
    chunks = [
        make_retrieved_chunk(
            chunk_id="shipping_chunk_0001",
            metadata={"source": "shipping.md", "section": "发货"},
            score=0.92,
        ),
        make_retrieved_chunk(
            chunk_id="refund_chunk_0001",
            metadata={"source": "refund.md", "section": "退款"},
            score=0.81,
        ),
    ]

    report = build_retrieval_tuning_report(
        "  订单多久发货？  ",
        chunks,
        top_k=3,
        score_threshold=0.8,
    )

    assert report.query == "订单多久发货？"
    assert report.top_k == 3
    assert report.score_threshold == 0.8
    assert report.result_count == 2
    assert report.source_count == 2
    assert report.top_score == 0.92
    assert report.bottom_score == 0.81
    assert report.sources == ["shipping.md", "refund.md"]
    assert report.chunk_ids == ["shipping_chunk_0001", "refund_chunk_0001"]
    assert report.debug_lines[0].startswith("1. score=0.9200")


def test_compare_retrieval_tuning_cases_runs_retriever_for_each_case() -> None:
    embedding_model = FakeEmbeddingModel(dimension=4)
    vector_store = FakeVectorStoreReader(
        chunks=[
            make_retrieved_chunk(chunk_id="chunk-high", score=0.95),
            make_retrieved_chunk(chunk_id="chunk-mid", score=0.82),
            make_retrieved_chunk(chunk_id="chunk-low", score=0.41),
        ]
    )

    reports = compare_retrieval_tuning_cases(
        "订单多久发货？",
        embedding_model=embedding_model,
        vector_store=vector_store,
        cases=[
            RetrievalTuningCase(top_k=1, score_threshold=None),
            RetrievalTuningCase(top_k=3, score_threshold=0.8),
        ],
        permission_group="customer_service",
    )

    assert [report.result_count for report in reports] == [1, 2]
    assert reports[0].chunk_ids == ["chunk-high"]
    assert reports[1].chunk_ids == ["chunk-high", "chunk-mid"]
    assert len(embedding_model.calls) == 2
    assert len(vector_store.calls) == 2
    assert vector_store.calls[0]["payload_filter"] == {
        "must": [
            {"key": "permission_group", "match": {"value": "customer_service"}},
        ]
    }


def test_compare_retrieval_tuning_cases_rejects_blank_query() -> None:
    with pytest.raises(ValueError, match="query"):
        compare_retrieval_tuning_cases(
            "   ",
            embedding_model=FakeEmbeddingModel(dimension=4),
            vector_store=FakeVectorStoreReader(),
            cases=[RetrievalTuningCase(top_k=1)],
        )
