"""PawPal+ core system classes.

A small pet-care planner:
  Owner has many Pets, each Pet has many Tasks.
  The Scheduler is the controller that works across all of an owner's pets.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

# How many days must pass before a task of a given frequency is due again.
FREQUENCY_DAYS = {"daily": 1, "weekly": 7}


def time_to_minutes(clock: str) -> int:
    """Convert an 'HH:MM' clock string to minutes since midnight.

    >>> time_to_minutes("08:30")
    510
    """
    hours, minutes = clock.split(":")
    return int(hours) * 60 + int(minutes)


def minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight back to an 'HH:MM' clock string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Task:
    """A single pet care activity."""

    description: str                    # e.g. "Morning walk"
    time: int                           # how long it takes, in minutes
    frequency: str                      # e.g. "daily", "weekly"
    completed: bool = False             # completion status
    start_time: str | None = None       # scheduled clock time, e.g. "08:00"
    last_completed: date | None = None  # date this task was last finished
    due_date: date | None = None        # day this occurrence is scheduled for

    def mark_complete(self, on: date | None = None) -> None:
        """Mark this task as done, recording the date it was completed."""
        self.completed = True
        if on is not None:
            self.last_completed = on

    def next_occurrence(self, completed_on: date | None = None) -> "Task | None":
        """Build the next occurrence of a recurring task, or None if one-off.

        The new due date is the completion date plus one cycle: daily rolls
        forward 1 day, weekly 7. ``timedelta`` does the calendar math so month,
        year, and leap-year boundaries are handled correctly (e.g. Jul 31 + 1
        day becomes Aug 1, not an invalid Jul 32).
        """
        step = FREQUENCY_DAYS.get(self.frequency)
        if step is None:
            return None  # unknown / non-repeating frequency: nothing to schedule

        base = completed_on or self.last_completed
        if base is None:
            return None  # can't advance a task that was never completed

        return Task(
            description=self.description,
            time=self.time,
            frequency=self.frequency,
            completed=False,
            start_time=self.start_time,
            due_date=base + timedelta(days=step),
        )

    def mark_incomplete(self) -> None:
        """Reset this task back to not done."""
        self.completed = False

    def start_minute(self) -> int | None:
        """Return the scheduled start as minutes since midnight (or None)."""
        return None if self.start_time is None else time_to_minutes(self.start_time)

    def end_minute(self) -> int | None:
        """Return the scheduled end as minutes since midnight (or None)."""
        start = self.start_minute()
        return None if start is None else start + self.time

    def is_due(self, today: date) -> bool:
        """True if this recurring task needs doing on the given day.

        A task never completed is always due. Otherwise it is due once enough
        days have passed for its frequency (daily = 1, weekly = 7). Unknown
        frequencies default to always-due so nothing is silently dropped.
        """
        if self.last_completed is None:
            return True
        days_passed = (today - self.last_completed).days
        return days_passed >= FREQUENCY_DAYS.get(self.frequency, 0)


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

    # --- 1. Sorting by time --------------------------------------------------
    def sorted_by_time(self, ascending: bool = True) -> list[Task]:
        """Return all tasks ordered by how long they take.

        Ascending (default) puts quick wins first; descending front-loads the
        big jobs. Ties keep their original order (Python's sort is stable).
        """
        return sorted(self.get_all_tasks(), key=lambda t: t.time, reverse=not ascending)

    def sorted_by_start_time(self) -> list[Task]:
        """Return all tasks in the order they happen during the day.

        Scheduled tasks are ordered by their ``start_time`` (compared as real
        minutes-since-midnight, not as raw strings). Tasks without a start time
        have no place on the timeline, so they sink to the end.
        """
        # A huge sentinel key parks unscheduled tasks after every real time.
        return sorted(
            self.get_all_tasks(),
            key=lambda t: t.start_minute() if t.start_time is not None else 24 * 60,
        )

    # --- 2. Filtering by pet / status ---------------------------------------
    def filter_tasks(
        self,
        pet: "Pet | str | None" = None,
        completed: bool | None = None,
        frequency: str | None = None,
    ) -> list[Task]:
        """Return tasks narrowed by any combination of pet, status, frequency.

        Each argument left as ``None`` is ignored, so ``filter_tasks()`` with no
        arguments returns everything. ``pet`` may be either a ``Pet`` object or a
        pet-name string (case-insensitive, surrounding spaces ignored), so both
        of these work:
          - ``filter_tasks(pet=mochi, completed=False)``   -> Mochi's to-do list
          - ``filter_tasks("mochi", completed=False)``     -> same, by name
        An unknown pet name simply yields no tasks.
        """
        if isinstance(pet, str):
            wanted = pet.strip().lower()
            tasks = [
                task
                for p in self.owner.pets
                if p.name.strip().lower() == wanted
                for task in p.tasks
            ]
        elif pet is not None:
            tasks = list(pet.tasks)
        else:
            tasks = self.get_all_tasks()

        return [
            task
            for task in tasks
            if (completed is None or task.completed == completed)
            and (frequency is None or task.frequency == frequency)
        ]

    # --- 3. Recurring tasks --------------------------------------------------
    def complete_task(self, task: Task, on: date | None = None) -> Task | None:
        """Mark a task done and auto-schedule its next occurrence.

        For a recurring task (daily/weekly) this marks the current one complete
        and adds a fresh, uncompleted copy — due one cycle later — to the same
        pet, returning that new task. One-off tasks just get marked done and
        return None. The new instance lands with the pet that owns the original.
        """
        if on is None:
            on = date.today()
        task.mark_complete(on)

        upcoming = task.next_occurrence(completed_on=on)
        if upcoming is not None:
            pet = self.pet_of(task)
            if pet is not None:
                pet.add_task(upcoming)
        return upcoming

    def due_tasks(self, today: date | None = None) -> list[Task]:
        """Return the recurring tasks that are due on the given day.

        Defaults to today's date. Relies on each task's own ``is_due`` logic so
        a daily task reappears every day and a weekly one only once a week.
        """
        if today is None:
            today = date.today()
        return [task for task in self.get_all_tasks() if task.is_due(today)]

    # --- 4. Basic conflict detection ----------------------------------------
    def detect_conflicts(self) -> list[tuple[Task, Task]]:
        """Find pairs of scheduled tasks whose time windows overlap.

        Two tasks conflict when their windows overlap at all — including being
        set to the *exact same* start time — regardless of which pet they belong
        to, since one owner can't be in two places at once. Tasks without a
        start time, or with an unparseable one, are skipped rather than raising
        (lightweight: a bad value never crashes the schedule). Sorting by start
        lets the scan stop early once a later task begins after the current ends.
        """
        # Parse each start time once, pairing it with its task, then sort by it.
        timed: list[tuple[int, Task]] = []
        for task in self.get_all_tasks():
            start = self._start_minute(task)
            if start is not None:
                timed.append((start, task))
        timed.sort(key=lambda pair: pair[0])

        conflicts: list[tuple[Task, Task]] = []
        for i, (start, current) in enumerate(timed):
            current_end = start + current.time
            for other_start, other in timed[i + 1:]:
                if other_start >= current_end:
                    break  # later tasks start even later — no overlap possible
                conflicts.append((current, other))
        return conflicts

    @staticmethod
    def _start_minute(task: Task) -> int | None:
        """Parse a task's start time to minutes, or None if missing/malformed.

        Defensive on purpose: a typo like '8am' is skipped, not fatal.
        """
        if task.start_time is None:
            return None
        try:
            return time_to_minutes(task.start_time)
        except (ValueError, AttributeError):
            return None

    def grouped_conflicts(self) -> list[tuple[Task, list[Task]]]:
        """Group overlaps under a single anchor task for readable reporting.

        ``detect_conflicts`` returns one pair per overlap, so a task that clashes
        with several others shows up on several lines. This collapses those into
        ``(anchor, [tasks it overlaps])`` while preserving time order.
        """
        grouped: dict[int, tuple[Task, list[Task]]] = {}
        order: list[int] = []
        for anchor, other in self.detect_conflicts():
            key = id(anchor)
            if key not in grouped:
                grouped[key] = (anchor, [])
                order.append(key)
            grouped[key][1].append(other)
        return [grouped[key] for key in order]

    def pet_of(self, task: Task) -> Pet | None:
        """Return the pet a task belongs to (by identity), or None if unowned.

        Uses ``is`` rather than ``==`` so two pets with an identical task (e.g.
        both have a "Feeding") aren't confused for one another.
        """
        for pet in self.owner.pets:
            if any(t is task for t in pet.tasks):
                return pet
        return None

    def describe_task(self, task: Task) -> str:
        """Label a task as 'Pet: Description (HH:MM)' for messages."""
        pet = self.pet_of(task)
        who = f"{pet.name}: " if pet else ""
        when = f" ({task.start_time})" if task.start_time else ""
        return f"{who}{task.description}{when}"

    def conflict_warnings(self) -> list[str]:
        """Return friendly warning strings for overlapping tasks.

        Lightweight by design: returns an empty list when the day is clear and
        never raises, so callers can print/show the result directly instead of
        guarding against a crash. Each message names the pets involved so the
        owner can tell same-pet clashes from cross-pet ones.
        """
        warnings: list[str] = []
        for anchor, others in self.grouped_conflicts():
            overlaps = ", ".join(self.describe_task(o) for o in others)
            warnings.append(
                f"⚠️ {self.describe_task(anchor)} is scheduled at the same time as {overlaps}"
            )
        return warnings
