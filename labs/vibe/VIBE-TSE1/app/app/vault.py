"""taskvault: a tiny in-memory task store used for the Vibe Code live demo.

Reference solution: the search(keyword) feature (see FEATURE.md) is implemented
and covered by tests/test_search.py. In the live demo you produce this by
driving Vibe Code, not by typing it yourself.
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

    def search(self, keyword: str) -> list[Task]:
        """Return tasks whose title contains keyword, case-insensitively.

        An empty or whitespace-only keyword returns no tasks.
        """
        if not keyword or not keyword.strip():
            return []
        needle = keyword.strip().lower()
        return [t for t in self._tasks if needle in t.title.lower()]
