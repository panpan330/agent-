from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class LearningTask:
    task_id: str
    title: str
    topic: str
    done: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        self.topic = self.topic.strip()

        if not self.task_id.strip():
            raise ValueError("task_id is required")

        if not self.title:
            raise ValueError("title is required")

        if not self.topic:
            raise ValueError("topic is required")

        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def mark_done(self) -> None:
        self.done = True

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "topic": self.topic,
            "done": self.done,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "LearningTask":
        task_id = data.get("task_id", "")
        title = data.get("title", "")
        topic = data.get("topic", "")
        done = data.get("done", False)
        created_at = data.get("created_at", "")

        if not isinstance(task_id, str):
            raise ValueError("task_id must be a string")

        if not isinstance(title, str):
            raise ValueError("title must be a string")

        if not isinstance(topic, str):
            raise ValueError("topic must be a string")

        if not isinstance(done, bool):
            raise ValueError("done must be a bool")

        if not isinstance(created_at, str):
            raise ValueError("created_at must be a string")

        return cls(
            task_id=task_id,
            title=title,
            topic=topic,
            done=done,
            created_at=created_at,
        )


@dataclass(frozen=True)
class QuestionAnalysis:
    question: str
    category: str
    order_ids: tuple[str, ...]
    keywords: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "question": self.question,
            "category": self.category,
            "order_ids": list(self.order_ids),
            "keywords": list(self.keywords),
        }
