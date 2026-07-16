from collections.abc import Mapping
from typing import Any, TypeAlias


PayloadFilter: TypeAlias = dict[str, list[dict[str, Any]]]

FILTERABLE_METADATA_KEYS = (
    "permission_group",
    "business_domain",
    "doc_type",
    "source",
)


def build_payload_filter(
    *,
    permission_group: str | None = None,
    business_domain: str | None = None,
    doc_type: str | None = None,
    source: str | None = None,
) -> PayloadFilter | None:
    conditions: list[dict[str, Any]] = []
    for key, value in (
        ("permission_group", permission_group),
        ("business_domain", business_domain),
        ("doc_type", doc_type),
        ("source", source),
    ):
        condition = build_match_condition(key, value)
        if condition is not None:
            conditions.append(condition)

    if not conditions:
        return None
    return {"must": conditions}


def build_match_condition(
    key: str,
    value: str | None,
) -> dict[str, Any] | None:
    if value is None:
        return None

    normalized_key = key.strip()
    normalized_value = value.strip()
    if not normalized_key:
        raise ValueError("filter key must not be blank")
    if not normalized_value:
        raise ValueError(f"{normalized_key} filter value must not be blank")

    return {
        "key": normalized_key,
        "match": {
            "value": normalized_value,
        },
    }


def normalize_payload_filter(
    payload_filter: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if payload_filter is None:
        return None
    if not payload_filter:
        raise ValueError("payload_filter must not be empty")
    return dict(payload_filter)
