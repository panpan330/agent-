from argparse import ArgumentParser
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.documents import RetrievedChunk
from app.rag.evaluation import (
    evaluate_retrieval_results,
    format_retrieval_bad_cases,
    format_retrieval_eval_summary,
    load_retrieval_eval_cases,
)
from app.rag.hybrid import KeywordSearchResult, SimpleKeywordRetriever
from app.rag.loaders import load_documents_from_directory
from app.rag.splitters import split_documents_into_chunks


KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "data" / "knowledge_base"
EVAL_CASES_PATH = PROJECT_ROOT / "data" / "rag_eval" / "retrieval_cases.json"
DEFAULT_EVAL_TOP_K = 3
DEFAULT_KEYWORD_MIN_SCORE = 0.2


def main() -> None:
    parser = ArgumentParser(description="Run a local RAG retrieval evaluation smoke.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_EVAL_TOP_K)
    parser.add_argument(
        "--keyword-min-score",
        type=float,
        default=DEFAULT_KEYWORD_MIN_SCORE,
    )
    args = parser.parse_args()

    cases = load_retrieval_eval_cases(EVAL_CASES_PATH)
    documents = load_documents_from_directory(KNOWLEDGE_BASE_DIR)
    chunks = split_documents_into_chunks(documents)
    keyword_retriever = SimpleKeywordRetriever(chunks)

    retrievals_by_case_id: dict[str, list[RetrievedChunk]] = {}
    for eval_case in cases:
        keyword_results = keyword_retriever.search(
            eval_case.query,
            top_k=args.top_k,
            min_score=args.keyword_min_score,
            permission_group=eval_case.permission_group,
            business_domain=eval_case.business_domain,
            doc_type=eval_case.doc_type,
            source=eval_case.source,
        )
        retrievals_by_case_id[eval_case.id] = [
            _keyword_result_to_retrieved_chunk(result)
            for result in keyword_results
        ]

    summary = evaluate_retrieval_results(
        cases,
        retrievals_by_case_id,
        top_k=args.top_k,
    )

    for line in format_retrieval_eval_summary(summary):
        print(line)
    print()
    for line in format_retrieval_bad_cases(summary):
        print(line)


def _keyword_result_to_retrieved_chunk(
    result: KeywordSearchResult,
) -> RetrievedChunk:
    return RetrievedChunk(
        point_id=result.chunk_id,
        chunk_id=result.chunk_id,
        content=result.content,
        metadata=result.metadata,
        score=result.score,
    )


if __name__ == "__main__":
    main()
