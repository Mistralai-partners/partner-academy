"""taskvault: a tiny in-memory task store used for the Vibe Code live demo.

This is the miniature "customer repo" you drive Vibe Code against while the
customer watches. It has a small, honest surface: add a task, list tasks. The
feature the customer asked for (search) is deliberately missing so the room can
watch Vibe Code plan, implement, and test it in one loop. See FEATURE.md.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Task:
    """A single task in the vault."""

    id: int
    title: str
    done: bool = False


class Vault:
    """An in-memory collection of tasks, kept in insertion order."""

    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._next_id: int = 1

    def add(self, title: str) -> Task:
        """Add a task by title and return it.

        Raises:
            ValueError: if the title is empty or whitespace only.
        """
        if not title or not title.strip():
            raise ValueError("title must not be empty")
        task = Task(self._next_id, title.strip())
        self._tasks.append(task)
        self._next_id += 1
        return task

    def all(self) -> list[Task]:
        """Return all tasks in insertion order."""
        return list(self._tasks)

    # FEATURE REQUESTED (see FEATURE.md): a search(keyword) method.
    # This is the change you have Vibe Code implement, live, in front of the
    # customer. Do not hand-write it here in the demo - drive the agent.
