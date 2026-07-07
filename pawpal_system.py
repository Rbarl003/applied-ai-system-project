"""PawPal+ core system classes (skeleton).

Generated from the UML draft in diagrams/uml_draft.mmd.
Method bodies are stubs to be implemented next.
"""

from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", or "other"

    def describe(self) -> str:
        """Return a short label like 'Mochi (cat)'."""
        ...


@dataclass
class Task:
    title: str
    duration: int  # minutes
    priority: str  # "low", "medium", or "high"

    def priority_score(self) -> int:
        """Convert priority into a number so tasks can be sorted."""
        ...


@dataclass
class Owner:
    name: str
    available_minutes: int  # time free for pet care today

    def get_available_minutes(self) -> int:
        """Return how much time the owner has for tasks today."""
        ...


class Scheduler:
    def __init__(self, tasks: list[Task], available_time: int):
        self.tasks = tasks
        self.available_time = available_time

    def build_plan(self) -> list[Task]:
        """Pick and order tasks by priority and available time."""
        ...

    def explain(self) -> str:
        """Explain why each task was chosen and when it happens."""
        ...
