import logging
from collections import Counter
from pathlib import Path

from learning_task_assistant.models import LearningTask, QuestionAnalysis
from learning_task_assistant.rules import (
    classify_question,
    extract_keywords,
    extract_order_ids,
    normalize_text,
)
from learning_task_assistant.storage import load_tasks, save_tasks


class LearningTaskAssistant:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.tasks = load_tasks(storage_path)

    def add_task(self, task_id: str, title: str, topic: str) -> LearningTask:
        if self.find_task(task_id) is not None:
            raise ValueError(f"task already exists: {task_id}")

        task = LearningTask(task_id=task_id, title=title, topic=topic)
        self.tasks.append(task)
        logging.info("added task: %s", task_id)
        return task

    def find_task(self, task_id: str) -> LearningTask | None:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def mark_done(self, task_id: str) -> LearningTask:
        task = self.find_task(task_id)

        if task is None:
            raise KeyError(f"task not found: {task_id}")

        task.mark_done()
        logging.info("marked task done: %s", task_id)
        return task

    def analyze_question(self, question: str) -> QuestionAnalysis:
        normalized_question = normalize_text(question)

        if not normalized_question:
            raise ValueError("question is required")

        return QuestionAnalysis(
            question=normalized_question,
            category=classify_question(normalized_question),
            order_ids=extract_order_ids(normalized_question),
            keywords=extract_keywords(normalized_question),
        )

    def summarize_tasks(self) -> dict[str, object]:
        status_counter: Counter[str] = Counter()
        topic_counter: Counter[str] = Counter()

        for task in self.tasks:
            status = "done" if task.done else "todo"
            status_counter[status] += 1
            topic_counter[task.topic] += 1

        return {
            "total": len(self.tasks),
            "status": dict(status_counter),
            "topics": dict(topic_counter),
        }

    def save(self) -> None:
        save_tasks(self.storage_path, self.tasks)
        logging.info("saved tasks to: %s", self.storage_path)
