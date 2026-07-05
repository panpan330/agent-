import asyncio


async def fake_fetch_user(user_id: int, delay: float = 0.05) -> dict[str, object]:
    await asyncio.sleep(delay)
    return {
        "user_id": user_id,
        "name": "Panpan",
    }


async def fake_fetch_permissions(user_id: int, delay: float = 0.05) -> set[str]:
    await asyncio.sleep(delay)

    if user_id == 330:
        return {"read:tasks", "write:tasks", "call:ai"}

    return {"read:tasks"}


async def build_user_context(user_id: int) -> dict[str, object]:
    user, permissions = await asyncio.gather(
        fake_fetch_user(user_id),
        fake_fetch_permissions(user_id),
    )

    return {
        "user": user,
        "permissions": sorted(permissions),
    }
