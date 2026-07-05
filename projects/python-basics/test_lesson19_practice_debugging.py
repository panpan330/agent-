import pytest

from lesson19_practice_debugging import (
    calculate_average,
    get_required_field,
    normalize_user,
    parse_positive_int,
    safe_run,
)


def test_parse_positive_int_success() -> None:
    assert parse_positive_int("25") == 25


@pytest.mark.parametrize("value", ["abc", 0, -1, None])
def test_parse_positive_int_error(value: object) -> None:
    with pytest.raises(ValueError):
        parse_positive_int(value)


def test_get_required_field_success() -> None:
    assert get_required_field({"name": "Panpan"}, "name") == "Panpan"


def test_get_required_field_error() -> None:
    with pytest.raises(KeyError):
        get_required_field({"age": 25}, "name")


def test_calculate_average_success() -> None:
    assert calculate_average([0.8, 0.9, 1.0]) == pytest.approx(0.9)


def test_calculate_average_error() -> None:
    with pytest.raises(ValueError):
        calculate_average([])


def test_normalize_user_success() -> None:
    assert normalize_user({"name": " Panpan ", "age": "25"}) == {
        "name": "Panpan",
        "age": 25,
    }


def test_safe_run_success() -> None:
    result = safe_run("ok case", lambda: normalize_user({"name": "Panpan", "age": 25}))

    assert result["ok"] is True
    assert result["result"] == {"name": "Panpan", "age": 25}


def test_safe_run_error() -> None:
    result = safe_run("bad case", lambda: normalize_user({"age": "abc"}))

    assert result["ok"] is False
    assert result["error_type"] == "KeyError"
