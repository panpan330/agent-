import asyncio
from collections.abc import Awaitable
from typing import Any


async def fake_get_json(name: str, delay: float = 0.1) -> dict[str, object]:
    await asyncio.sleep(delay)
    return {
        "name": name,
        "ok": True,
    }


async def fetch_user_profile(user_id: int) -> dict[str, object]:
    data = await fake_get_json(f"user:{user_id}")
    return {
        "user_id": user_id,
        "name": "Panpan",
        "source": data["name"],
    }


async def fetch_user_permissions(user_id: int) -> set[str]:
    await asyncio.sleep(0.1)

    if user_id == 330:
        return {"read:docs", "call:ai", "create:ticket"}

    return {"read:docs"}


async def fetch_user_orders(user_id: int) -> list[dict[str, object]]:
    await asyncio.sleep(0.1)
    return [
        {"order_id": "ORD-20260705-001", "status": "paid", "user_id": user_id},
        {"order_id": "ORD-20260705-002", "status": "refunding", "user_id": user_id},
    ]


async def build_user_context(user_id: int) -> dict[str, object]:
    profile, permissions, orders = await asyncio.gather(
        fetch_user_profile(user_id),
        fetch_user_permissions(user_id),
        fetch_user_orders(user_id),
    )

    return {
        "profile": profile,
        "permissions": sorted(permissions),
        "orders": orders,
    }


async def classify_question_async(question: str) -> dict[str, str]:
    await asyncio.sleep(0.05)

    if "退款" in question:
        category = "refund"
    elif "物流" in question or "快递" in question:
        category = "shipping"
    elif "发票" in question:
        category = "invoice"
    else:
        category = "other"

    return {
        "question": question,
        "category": category,
    }


async def batch_classify_questions(questions: list[str]) -> list[dict[str, str]]:
    tasks = [classify_question_async(question) for question in questions]
    return await asyncio.gather(*tasks)


async def run_with_timeout(awaitable: Awaitable[Any], timeout: float) -> dict[str, object]:
    try:
        result = await asyncio.wait_for(awaitable, timeout=timeout)
    except TimeoutError:
        return {
            "ok": False,
            "reason": "timeout",
        }

    return {
        "ok": True,
        "result": result,
    }


async def main_async() -> None:
    context = await build_user_context(330)
    print("用户上下文:", context)

    questions = [
        "我的订单怎么退款？",
        "快递什么时候到？",
        "可以开发票吗？",
        "Python 怎么学？",
    ]
    print("问题分类:", await batch_classify_questions(questions))

    fast_result = await run_with_timeout(fake_get_json("fast", delay=0.05), timeout=1)
    slow_result = await run_with_timeout(fake_get_json("slow", delay=1), timeout=0.05)
    print("快速请求:", fast_result)
    print("超时请求:", slow_result)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
