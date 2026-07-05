import json

import pytest

from lesson20_practice_http_api import (
    build_auth_headers,
    build_create_ticket_body,
    build_order_url,
    build_search_url,
    classify_status_code,
    parse_query_params,
    prepare_json_post,
)


def test_build_order_url() -> None:
    assert (
        build_order_url("https://api.example.com/", "ORD-20260705-001")
        == "https://api.example.com/orders/ORD-20260705-001"
    )


def test_build_search_url_and_parse_query() -> None:
    url = build_search_url(
        "https://api.example.com",
        keyword="python 课程",
        status="paid",
        page=2,
    )

    assert url.startswith("https://api.example.com/orders/search?")
    assert parse_query_params(url) == {
        "keyword": "python 课程",
        "status": "paid",
        "page": "2",
    }


def test_build_auth_headers() -> None:
    assert build_auth_headers("abc123") == {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer abc123",
    }


def test_build_create_ticket_body() -> None:
    assert build_create_ticket_body(
        user_id=330,
        title="  订单退款问题  ",
        content="  用户想查询退款进度  ",
        category="refund",
    ) == {
        "user_id": 330,
        "title": "订单退款问题",
        "content": "用户想查询退款进度",
        "category": "refund",
    }


@pytest.mark.parametrize(
    ("field", "kwargs"),
    [
        ("title", {"title": "", "content": "content", "category": "refund"}),
        ("content", {"title": "title", "content": "", "category": "refund"}),
        ("category", {"title": "title", "content": "content", "category": ""}),
    ],
)
def test_build_create_ticket_body_requires_fields(
    field: str,
    kwargs: dict[str, str],
) -> None:
    with pytest.raises(ValueError, match=field):
        build_create_ticket_body(user_id=330, **kwargs)


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (200, "success"),
        (201, "success"),
        (400, "client_error"),
        (401, "client_error"),
        (404, "client_error"),
        (500, "server_error"),
        (999, "other"),
    ],
)
def test_classify_status_code(status_code: int, expected: str) -> None:
    assert classify_status_code(status_code) == expected


def test_prepare_json_post() -> None:
    body = {
        "user_id": 330,
        "title": "订单退款问题",
        "content": "用户想查询退款进度",
        "category": "refund",
    }
    prepared = prepare_json_post("https://api.example.com/tickets", body, token="abc123")

    assert prepared["method"] == "POST"
    assert prepared["url"] == "https://api.example.com/tickets"
    assert isinstance(prepared["headers"], dict)
    assert prepared["headers"]["Authorization"] == "Bearer abc123"
    assert json.loads(str(prepared["body"])) == body
