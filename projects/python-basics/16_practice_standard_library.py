from collections import Counter, defaultdict
from datetime import datetime, timezone
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


def get_project_paths(root: Path) -> dict[str, Path]:
    data_dir = root / "data"

    return {
        "root": root,
        "data_dir": data_dir,
        "tasks_file": data_dir / "tasks.json",
    }


def load_json_list(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        return []

    result = []
    for item in data:
        if isinstance(item, dict):
            result.append(item)

    return result


def count_task_status(tasks: list[dict[str, object]]) -> Counter[str]:
    counter: Counter[str] = Counter()

    for task in tasks:
        done = task.get("done", False)
        status = "done" if done else "todo"
        counter[status] += 1

    return counter


def group_tasks_by_topic(tasks: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    groups: defaultdict[str, list[dict[str, object]]] = defaultdict(list)

    for task in tasks:
        topic = task.get("topic", "未分类")
        if not isinstance(topic, str) or not topic:
            topic = "未分类"
        groups[topic].append(task)

    return dict(groups)


def build_run_info() -> dict[str, object]:
    return {
        "app_env": os.getenv("APP_ENV", "local"),
        "python_version": sys.version.split()[0],
        "run_at": datetime.now(timezone.utc).isoformat(),
    }


def log_summary(tasks: list[dict[str, object]], elapsed_seconds: float) -> None:
    logging.info("任务数量: %s", len(tasks))
    logging.info("处理耗时: %.6f 秒", elapsed_seconds)


def main() -> None:
    setup_logging()

    start = time.perf_counter()

    paths = get_project_paths(Path.cwd())
    print("路径信息:", paths)

    tasks = load_json_list(paths["tasks_file"])
    print("任务:", tasks)

    status_counter = count_task_status(tasks)
    print("状态统计:", status_counter)

    topic_groups = group_tasks_by_topic(tasks)
    print("按主题分组:", topic_groups)

    run_info = build_run_info()
    print("运行信息:", run_info)

    elapsed_seconds = time.perf_counter() - start
    log_summary(tasks, elapsed_seconds)

    report = {
        "run_info": run_info,
        "status_count": dict(status_counter),
        "topic_count": {topic: len(topic_tasks) for topic, topic_tasks in topic_groups.items()},
    }
    print("报告:", report)


if __name__ == "__main__":
    main()
