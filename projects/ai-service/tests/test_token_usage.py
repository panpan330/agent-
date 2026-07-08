import pytest

from app.core.token_usage import build_token_budget, estimate_text_tokens_roughly


def test_estimate_text_tokens_roughly_returns_zero_for_blank_text() -> None:
    assert estimate_text_tokens_roughly("") == 0
    assert estimate_text_tokens_roughly("   ") == 0


def test_estimate_text_tokens_roughly_estimates_english_text() -> None:
    assert estimate_text_tokens_roughly("abcdefghijkl") == 3


def test_estimate_text_tokens_roughly_counts_non_ascii_more_conservatively() -> None:
    assert estimate_text_tokens_roughly("你好世界") == 4


def test_estimate_text_tokens_roughly_estimates_mixed_text() -> None:
    assert estimate_text_tokens_roughly("hello 你好") == 4


def test_build_token_budget_combines_input_estimate_and_output_limit() -> None:
    budget = build_token_budget("abcdefghijkl", max_output_tokens=100)

    assert budget.estimated_input_tokens == 3
    assert budget.max_output_tokens == 100
    assert budget.total_reserved_tokens == 103


def test_build_token_budget_rejects_invalid_output_limit() -> None:
    with pytest.raises(ValueError, match="max_output_tokens"):
        build_token_budget("hello", max_output_tokens=0)
