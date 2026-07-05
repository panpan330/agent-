import asyncio
import time
from collections.abc import Awaitable
from typing import Any


async def fetch_user(user_id: int, delay: float = 0.3) -> dict[str, object]:
    await asyncio.sleep(delay)
    return {
        "user_id": user_id,
        "name": "Panpan",
    }


async def fetch_permissions(user_id: int, delay: float = 0.3) -> set[str]:
    await asyncio.sleep(delay)
    return {"read:docs", "call:ai"} if user_id == 330 else {"read:docs"}


async def fetch_recent_orders(user_id: int, delay: float = 0.3) -> list[dict[str, object]]:
    await asyncio.sleep(delay)
    return [
        {"order_id": "ORD-20260705-001", "status": "paid", "user_id": user_id},
        {"order_id": "ORD-20260705-002", "status": "refunding", "user_id": user_id},
    ]


async def build_user_context_sequential(user_id: int) -> dict[str, object]:
    user = await fetch_user(user_id)
    permissions = await fetch_permissions(user_id)
    orders = await fetch_recent_orders(user_id)

    return {
        "user": user,
        "permissions": sorted(permissions),
        "orders": orders,
    }


async def build_user_context_concurrent(user_id: int) -> dict[str, object]:
    user, permissions, orders = await asyncio.gather(
        fetch_user(user_id),
        fetch_permissions(user_id),
        fetch_recent_orders(user_id),
    )

    return {
        "user": user,
        "permissions": sorted(permissions),
        "orders": orders,
    }


async def answer_question(question: str) -> dict[str, object]:
    await asyncio.sleep(0.1)

    if "退款" in question:
        category = "refund"
    elif "物流" in question or "快递" in question:
        category = "shipping"
    else:
        category = "other"

    return {
        "question": question,
        "category": category,
    }


async def batch_answer_questions(questions: list[str]) -> list[dict[str, object]]:
    tasks = [answer_question(question) for question in questions]
    return await asyncio.gather(*tasks)


async def run_with_timeout(awaitable: Awaitable[Any], timeout: float) -> object:
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout)
    except TimeoutError:
        return {
            "ok": False,
            "reason": "timeout",
        }


async def demo_create_task() -> None:
    task = asyncio.create_task(fetch_user(330, delay=0.2))
    print("task 创建后，协程已经交给事件循环调度")

    user = await task
    print("task 结果:", user)


async def main_async() -> None:
    print("=== 1. async def 和 await ===")
    user = await fetch_user(330, delay=0.1)
    print(user)

    print("\n=== 2. 顺序执行：一个等完再执行下一个 ===")
    start = time.perf_counter()
    sequential_context = await build_user_context_sequential(330)
    sequential_elapsed = time.perf_counter() - start
    print(sequential_context)
    print(f"顺序耗时: {sequential_elapsed:.3f} 秒")

    print("\n=== 3. 并发执行：多个等待任务一起进行 ===")
    start = time.perf_counter()
    concurrent_context = await build_user_context_concurrent(330)
    concurrent_elapsed = time.perf_counter() - start
    print(concurrent_context)
    print(f"并发耗时: {concurrent_elapsed:.3f} 秒")

    print("\n=== 4. gather：批量等待多个协程 ===")
    questions = [
        "我的订单怎么退款？",
        "快递什么时候到？",
        "Python 怎么学？",
    ]
    print(await batch_answer_questions(questions))

    print("\n=== 5. wait_for：超时控制 ===")
    fast_result = await run_with_timeout(fetch_user(330, delay=0.1), timeout=1)
    slow_result = await run_with_timeout(fetch_user(330, delay=1), timeout=0.1)
    print("快速任务:", fast_result)
    print("超时任务:", slow_result)

    print("\n=== 6. create_task：先创建任务，后等待结果 ===")
    await demo_create_task()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
