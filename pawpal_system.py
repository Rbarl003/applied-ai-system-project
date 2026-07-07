"""PawPal+ core system classes.

A small pet-care planner:
  Owner has many Pets, each Pet has many Tasks.
  The Scheduler is the controller that works across all of an owner's pets.
"""

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care activity."""

    description: str          # e.g. "Morning walk"
    time: int                 # how long it takes, in minutes
    frequency: str            # e.g. "daily", "weekly"
    completed: bool = False   # completion status

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset this task back to not done."""
        self.completed = False


@dataclass
class Pet:
    """A pet and the list of care tasks that belong to it."""

    name: str
    species: str                              # "dog", "cat", or "other"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self.tasks.append(task)

    def describe(self) -> str:
        """Return a short label like 'Mochi (cat)'."""
        return f"{self.name} ({self.species})"


@dataclass
class Owner:
    """The person who manages one or more pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet for this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Collect every task across all of the owner's pets."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


class Scheduler:
    """Main controller: retrieves and organizes tasks across all pets."""

    def __init__(self, owner: Owner):
        """Create a scheduler that works over the given owner's pets and tasks."""
        self.owner = owner

    def get_all_tasks(self) -> list[Task]:
        """Ask the owner for every task across their pets."""
        return self.owner.get_all_tasks()

    def pending_tasks(self) -> list[Task]:
        """Return only the tasks that still need to be done."""
        return [task for task in self.get_all_tasks() if not task.completed]

    def completed_tasks(self) -> list[Task]:
        """Return only the tasks that are already done."""
        return [task for task in self.get_all_tasks() if task.completed]

    def tasks_by_frequency(self, frequency: str) -> list[Task]:
        """Return tasks that match a given frequency (e.g. 'daily')."""
        return [task for task in self.get_all_tasks() if task.frequency == frequency]
