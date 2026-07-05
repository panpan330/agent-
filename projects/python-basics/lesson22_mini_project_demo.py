import asyncio
import logging
from pathlib import Path

from learning_task_assistant.async_service import build_user_context
from learning_task_assistant.service import LearningTaskAssistant


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


async def main_async() -> None:
    setup_logging()

    storage_path = Path("data") / "learning_task_assistant_tasks.json"
    assistant = LearningTaskAssistant(storage_path)

    if assistant.find_task("py-001") is None:
        assistant.add_task("py-001", "复习 pytest 测试基础", "Python")

    if assistant.find_task("py-002") is None:
        assistant.add_task("py-002", "完成 Python 综合项目", "Python")

    assistant.mark_done("py-001")

    analysis = assistant.analyze_question(
        "  我想查询订单 ORD-20260705-001 的退款进度，也想继续学习 pytest  "
    )
    context = await build_user_context(330)

    assistant.save()

    print("任务统计:", assistant.summarize_tasks())
    print("问题分析:", analysis.to_dict())
    print("异步用户上下文:", context)
    print("数据已保存到:", storage_path)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
