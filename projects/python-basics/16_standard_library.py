from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import logging
import os
import sys
import time


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def load_json(path: Path) -> object:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_tasks(path: Path) -> list[dict[str, object]]:
    data = load_json(path)

    if not isinstance(data, list):
        return []

    tasks = []
    for item in data:
        if isinstance(item, dict):
            tasks.append(item)

    return tasks


def group_tasks_by_status(tasks: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    groups: defaultdict[str, list[dict[str, object]]] = defaultdict(list)

    for task in tasks:
        done = task.get("done", False)
        status = "done" if done else "todo"
        groups[status].append(task)

    return dict(groups)


def count_words(text: str) -> Counter[str]:
    words = text.lower().split()
    return Counter(words)


def main() -> None:
    setup_logging()

    print("=== 1. pathlib：处理路径 ===")
    project_dir = Path.cwd()
    data_dir = project_dir / "data"
    tasks_file = data_dir / "tasks.json"

    print("当前目录:", project_dir)
    print("data 目录:", data_dir)
    print("tasks 文件:", tasks_file)
    print("文件名:", tasks_file.name)
    print("文件后缀:", tasks_file.suffix)
    print("文件是否存在:", tasks_file.exists())

    print("\n=== 2. pathlib + json：读取任务文件 ===")
    tasks = load_tasks(tasks_file)
    print("任务数量:", len(tasks))
    print("前 2 个任务:", tasks[:2])

    print("\n=== 3. datetime：处理时间 ===")
    now = datetime.now()
    utc_now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)

    print("本地当前时间:", now.strftime("%Y-%m-%d %H:%M:%S"))
    print("UTC 当前时间:", utc_now.isoformat())
    print("明天:", tomorrow.strftime("%Y-%m-%d"))

    print("\n=== 4. time：计算耗时 ===")
    start = time.perf_counter()
    sorted_tasks = sorted(tasks, key=lambda task: str(task.get("name", "")))
    elapsed = time.perf_counter() - start
    print("排序后的任务数量:", len(sorted_tasks))
    print(f"排序耗时: {elapsed:.6f} 秒")

    print("\n=== 5. collections.Counter：统计词频 ===")
    text = "python ai python java python ai"
    word_counter = count_words(text)
    print(word_counter)
    print("出现最多的 2 个词:", word_counter.most_common(2))

    print("\n=== 6. collections.defaultdict：分组 ===")
    task_groups = group_tasks_by_status(tasks)
    print("已完成任务:", task_groups.get("done", []))
    print("未完成任务:", task_groups.get("todo", []))

    print("\n=== 7. logging：真实项目里替代 print 的日志工具 ===")
    logging.info("任务文件路径: %s", tasks_file)
    logging.info("任务数量: %s", len(tasks))
    logging.warning("这是 warning 级别日志，用来提醒可能需要关注的问题")

    print("\n=== 8. os：读取环境变量 ===")
    app_env = os.getenv("APP_ENV", "local")
    print("APP_ENV:", app_env)

    print("\n=== 9. sys：查看 Python 运行信息 ===")
    print("Python 版本:", sys.version.split()[0])
    print("命令行参数:", sys.argv)


if __name__ == "__main__":
    main()
