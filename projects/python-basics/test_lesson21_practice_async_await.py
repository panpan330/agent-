import asyncio

from lesson21_practice_async_await import (
    batch_classify_questions,
    build_user_context,
    fake_get_json,
    run_with_timeout,
)


def test_fake_get_json() -> None:
    result = asyncio.run(fake_get_json("test", delay=0))

    assert result == {
        "name": "test",
        "ok": True,
    }


def test_build_user_context() -> None:
    context = asyncio.run(build_user_context(330))

    assert context["profile"] == {
        "user_id": 330,
        "name": "Panpan",
        "source": "user:330",
    }
    assert context["permissions"] == ["call:ai", "create:ticket", "read:docs"]
    assert len(context["orders"]) == 2


def test_batch_classify_questions() -> None:
    result = asyncio.run(
        batch_classify_questions(
            [
                "我的订单怎么退款？",
                "快递什么时候到？",
                "可以开发票吗？",
                "Python 怎么学？",
            ]
        )
    )

    assert [item["category"] for item in result] == [
        "refund",
        "shipping",
        "invoice",
        "other",
    ]


def test_run_with_timeout_success() -> None:
    result = asyncio.run(run_with_timeout(fake_get_json("fast", delay=0), timeout=1))

    assert result["ok"] is True
    assert result["result"] == {
        "name": "fast",
        "ok": True,
    }


def test_run_with_timeout_timeout() -> None:
    result = asyncio.run(run_with_timeout(fake_get_json("slow", delay=0.2), timeout=0.01))

    assert result == {
        "ok": False,
        "reason": "timeout",
    }
