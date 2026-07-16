import pytest

from app.rag.filters import (
    build_match_condition,
    build_payload_filter,
    normalize_payload_filter,
)


def test_build_match_condition_uses_qdrant_match_value_shape() -> None:
    condition = build_match_condition("permission_group", " customer_service ")

    assert condition == {
        "key": "permission_group",
        "match": {
            "value": "customer_service",
        },
    }


def test_build_match_condition_returns_none_for_missing_value() -> None:
    assert build_match_condition("permission_group", None) is None


def test_build_match_condition_rejects_blank_value() -> None:
    with pytest.raises(ValueError, match="permission_group"):
        build_match_condition("permission_group", "   ")


def test_build_payload_filter_returns_none_when_no_filters_requested() -> None:
    assert build_payload_filter() is None


def test_build_payload_filter_combines_conditions_with_must() -> None:
    payload_filter = build_payload_filter(
        permission_group="customer_service",
        business_domain="order",
        doc_type="policy",
        source="order-shipping-policy.md",
    )

    assert payload_filter == {
        "must": [
            {
                "key": "permission_group",
                "match": {"value": "customer_service"},
            },
            {
                "key": "business_domain",
                "match": {"value": "order"},
            },
            {
                "key": "doc_type",
                "match": {"value": "policy"},
            },
            {
                "key": "source",
                "match": {"value": "order-shipping-policy.md"},
            },
        ]
    }


def test_normalize_payload_filter_rejects_empty_filter() -> None:
    with pytest.raises(ValueError, match="payload_filter"):
        normalize_payload_filter({})
