from collections.abc import Mapping, Sequence
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.rag.documents import RetrievedChunk


RetrievalMatchLevel = Literal["chunk_id", "section", "source", "none"]


class RetrievalEvalCase(BaseModel):
    id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    expected_sources: list[str] = Field(default_factory=list)
    expected_sections: list[str] = Field(default_factory=list)
    expected_chunk_ids: list[str] = Field(default_factory=list)
    expect_no_results: bool = False
    permission_group: str | None = None
    business_domain: str | None = None
    doc_type: str | None = None
    source: str | None = None
    notes: str = ""

    @field_validator("id", "query", mode="before")
    @classmethod
    def normalize_required_string(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator(
        "expected_sources",
        "expected_sections",
        "expected_chunk_ids",
        mode="before",
    )
    @classmethod
    def normalize_expected_values(cls, value: object) -> object:
        if value is None:
            return []
        if isinstance(value, str) or not isinstance(value, Sequence):
            raise ValueError("expected values must be a list of strings")
        normalized_values: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("expected values must contain non-blank strings")
            normalized = item.strip()
            if normalized not in normalized_values:
                normalized_values.append(normalized)
        return normalized_values

    @field_validator("permission_group", "business_domain", "doc_type", "source", mode="before")
    @classmethod
    def normalize_optional_filter(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_notes(cls, value: object) -> object:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def validate_expectations(self) -> "RetrievalEvalCase":
        has_expected_targets = any(
            (
                self.expected_sources,
                self.expected_sections,
                self.expected_chunk_ids,
            )
        )
        if self.expect_no_results:
            if has_expected_targets:
                raise ValueError(
                    "no-result cases must not define expected retrieval targets"
                )
            return self
        if not has_expected_targets:
            raise ValueError("retrieval eval case must define expected targets")
        return self


class RetrievalEvalItem(BaseModel):
    rank: int = Field(ge=1)
    chunk_id: str = Field(min_length=1)
    source: str | None = None
    section: str | None = None
    score: float
    relevant: bool


class RetrievalEvalCaseResult(BaseModel):
    case_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    top_k: int = Field(gt=0)
    match_level: RetrievalMatchLevel
    metric_applicable: bool
    expected_count: int = Field(ge=0)
    retrieved_count: int = Field(ge=0)
    relevant_retrieved_count: int = Field(ge=0)
    matched_expected_count: int = Field(ge=0)
    hit: bool
    first_relevant_rank: int | None = None
    precision_at_k: float = Field(ge=0, le=1)
    recall_at_k: float = Field(ge=0, le=1)
    reciprocal_rank: float = Field(ge=0, le=1)
    passed: bool
    failed_reason: str | None = None
    retrieved_items: list[RetrievalEvalItem] = Field(default_factory=list)


class RetrievalEvalSummary(BaseModel):
    top_k: int = Field(gt=0)
    case_count: int = Field(ge=0)
    evaluated_case_count: int = Field(ge=0)
    no_result_case_count: int = Field(ge=0)
    passed_case_count: int = Field(ge=0)
    failed_case_count: int = Field(ge=0)
    hit_rate_at_k: float = Field(ge=0, le=1)
    recall_at_k: float = Field(ge=0, le=1)
    precision_at_k: float = Field(ge=0, le=1)
    mrr_at_k: float = Field(ge=0, le=1)
    no_result_success_rate: float | None = Field(default=None, ge=0, le=1)
    results: list[RetrievalEvalCaseResult] = Field(default_factory=list)


def load_retrieval_eval_cases(path: Path | str) -> list[RetrievalEvalCase]:
    raw_text = Path(path).read_text(encoding="utf-8")
    raw_cases = json.loads(raw_text)
    if not isinstance(raw_cases, list):
        raise ValueError("retrieval eval cases file must contain a JSON list")
    cases = [RetrievalEvalCase.model_validate(raw_case) for raw_case in raw_cases]
    _validate_unique_case_ids(cases)
    return cases


def evaluate_retrieval_case(
    eval_case: RetrievalEvalCase,
    retrieved_chunks: Sequence[RetrievedChunk],
    *,
    top_k: int,
) -> RetrievalEvalCaseResult:
    _validate_top_k(top_k)
    top_chunks = list(retrieved_chunks)[:top_k]

    if eval_case.expect_no_results:
        passed = not top_chunks
        return RetrievalEvalCaseResult(
            case_id=eval_case.id,
            query=eval_case.query,
            top_k=top_k,
            match_level="none",
            metric_applicable=False,
            expected_count=0,
            retrieved_count=len(top_chunks),
            relevant_retrieved_count=0,
            matched_expected_count=0,
            hit=passed,
            precision_at_k=1.0 if passed else 0.0,
            recall_at_k=1.0 if passed else 0.0,
            reciprocal_rank=1.0 if passed else 0.0,
            passed=passed,
            failed_reason=None if passed else "expected no results but retrieved chunks",
            retrieved_items=[
                _build_eval_item(
                    rank=index,
                    chunk=chunk,
                    relevant=False,
                )
                for index, chunk in enumerate(top_chunks, start=1)
            ],
        )

    matcher = _ExpectedMatcher.from_case(eval_case)
    retrieved_items: list[RetrievalEvalItem] = []
    matched_expected_keys: set[str] = set()
    first_relevant_rank: int | None = None
    relevant_retrieved_count = 0

    for rank, chunk in enumerate(top_chunks, start=1):
        matched_key = matcher.match(chunk)
        relevant = matched_key is not None
        if relevant:
            relevant_retrieved_count += 1
            matched_expected_keys.add(matched_key)
            if first_relevant_rank is None:
                first_relevant_rank = rank
        retrieved_items.append(
            _build_eval_item(
                rank=rank,
                chunk=chunk,
                relevant=relevant,
            )
        )

    matched_expected_count = len(matched_expected_keys)
    expected_count = matcher.expected_count
    hit = first_relevant_rank is not None
    recall_at_k = matched_expected_count / expected_count
    precision_at_k = relevant_retrieved_count / top_k
    reciprocal_rank = 0.0 if first_relevant_rank is None else 1 / first_relevant_rank
    passed = matched_expected_count == expected_count

    return RetrievalEvalCaseResult(
        case_id=eval_case.id,
        query=eval_case.query,
        top_k=top_k,
        match_level=matcher.match_level,
        metric_applicable=True,
        expected_count=expected_count,
        retrieved_count=len(top_chunks),
        relevant_retrieved_count=relevant_retrieved_count,
        matched_expected_count=matched_expected_count,
        hit=hit,
        first_relevant_rank=first_relevant_rank,
        precision_at_k=round(precision_at_k, 6),
        recall_at_k=round(recall_at_k, 6),
        reciprocal_rank=round(reciprocal_rank, 6),
        passed=passed,
        failed_reason=None if passed else "missing expected retrieval targets",
        retrieved_items=retrieved_items,
    )


def evaluate_retrieval_results(
    cases: Sequence[RetrievalEvalCase],
    retrievals_by_case_id: Mapping[str, Sequence[RetrievedChunk]],
    *,
    top_k: int,
) -> RetrievalEvalSummary:
    _validate_top_k(top_k)
    _validate_unique_case_ids(cases)
    results = [
        evaluate_retrieval_case(
            eval_case,
            retrievals_by_case_id.get(eval_case.id, []),
            top_k=top_k,
        )
        for eval_case in cases
    ]
    evaluated_results = [result for result in results if result.metric_applicable]
    no_result_results = [result for result in results if not result.metric_applicable]
    no_result_success_rate = (
        _average([1.0 if result.passed else 0.0 for result in no_result_results])
        if no_result_results
        else None
    )

    return RetrievalEvalSummary(
        top_k=top_k,
        case_count=len(results),
        evaluated_case_count=len(evaluated_results),
        no_result_case_count=len(no_result_results),
        passed_case_count=sum(1 for result in results if result.passed),
        failed_case_count=sum(1 for result in results if not result.passed),
        hit_rate_at_k=_average([1.0 if result.hit else 0.0 for result in evaluated_results]),
        recall_at_k=_average([result.recall_at_k for result in evaluated_results]),
        precision_at_k=_average([result.precision_at_k for result in evaluated_results]),
        mrr_at_k=_average([result.reciprocal_rank for result in evaluated_results]),
        no_result_success_rate=no_result_success_rate,
        results=results,
    )


def format_retrieval_eval_summary(summary: RetrievalEvalSummary) -> list[str]:
    lines = [
        "RAG retrieval evaluation summary",
        f"top_k: {summary.top_k}",
        f"cases: {summary.case_count}",
        f"evaluated_cases: {summary.evaluated_case_count}",
        f"no_result_cases: {summary.no_result_case_count}",
        f"passed_cases: {summary.passed_case_count}",
        f"failed_cases: {summary.failed_case_count}",
        f"hit_rate@{summary.top_k}: {summary.hit_rate_at_k:.4f}",
        f"recall@{summary.top_k}: {summary.recall_at_k:.4f}",
        f"precision@{summary.top_k}: {summary.precision_at_k:.4f}",
        f"mrr@{summary.top_k}: {summary.mrr_at_k:.4f}",
    ]
    if summary.no_result_success_rate is not None:
        lines.append(
            f"no_result_success_rate: {summary.no_result_success_rate:.4f}"
        )
    return lines


def format_retrieval_bad_cases(summary: RetrievalEvalSummary) -> list[str]:
    bad_cases = [result for result in summary.results if not result.passed]
    if not bad_cases:
        return ["No bad cases."]

    lines = ["Bad cases:"]
    for result in bad_cases:
        lines.append(
            f"- {result.case_id}: recall@{result.top_k}={result.recall_at_k:.4f} "
            f"mrr@{result.top_k}={result.reciprocal_rank:.4f} "
            f"reason={result.failed_reason}"
        )
        for item in result.retrieved_items:
            marker = "relevant" if item.relevant else "noise"
            lines.append(
                f"  {item.rank}. {marker} score={item.score:.4f} "
                f"source={item.source or '-'} section={item.section or '-'} "
                f"chunk_id={item.chunk_id}"
            )
    return lines


class _ExpectedMatcher:
    def __init__(
        self,
        *,
        match_level: RetrievalMatchLevel,
        expected_keys: set[str],
        expected_sources: set[str],
    ) -> None:
        self.match_level = match_level
        self.expected_keys = expected_keys
        self.expected_sources = expected_sources

    @classmethod
    def from_case(cls, eval_case: RetrievalEvalCase) -> "_ExpectedMatcher":
        if eval_case.expected_chunk_ids:
            return cls(
                match_level="chunk_id",
                expected_keys=set(eval_case.expected_chunk_ids),
                expected_sources=set(eval_case.expected_sources),
            )
        if eval_case.expected_sections:
            return cls(
                match_level="section",
                expected_keys=set(eval_case.expected_sections),
                expected_sources=set(eval_case.expected_sources),
            )
        return cls(
            match_level="source",
            expected_keys=set(eval_case.expected_sources),
            expected_sources=set(eval_case.expected_sources),
        )

    @property
    def expected_count(self) -> int:
        return len(self.expected_keys)

    def match(self, chunk: RetrievedChunk) -> str | None:
        source = _metadata_string(chunk.metadata, "source")
        if self.expected_sources and source not in self.expected_sources:
            return None

        if self.match_level == "chunk_id":
            return chunk.chunk_id if chunk.chunk_id in self.expected_keys else None
        if self.match_level == "section":
            section = _metadata_string(chunk.metadata, "section")
            return section if section in self.expected_keys else None
        if self.match_level == "source":
            return source if source in self.expected_keys else None
        return None


def _build_eval_item(
    *,
    rank: int,
    chunk: RetrievedChunk,
    relevant: bool,
) -> RetrievalEvalItem:
    return RetrievalEvalItem(
        rank=rank,
        chunk_id=chunk.chunk_id,
        source=_metadata_string(chunk.metadata, "source"),
        section=_metadata_string(chunk.metadata, "section"),
        score=chunk.score,
        relevant=relevant,
    )


def _metadata_string(metadata: Mapping[str, object], key: str) -> str | None:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _validate_top_k(top_k: int) -> None:
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")


def _validate_unique_case_ids(cases: Sequence[RetrievalEvalCase]) -> None:
    seen: set[str] = set()
    for eval_case in cases:
        if eval_case.id in seen:
            raise ValueError("retrieval eval case ids must be unique")
        seen.add(eval_case.id)


def _average(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 6)
