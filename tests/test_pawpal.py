"""Simple tests for the PawPal+ system."""

import os
import sys

# Make sure the project root is importable when running pytest from anywhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task


def test_mark_complete_updates_status():
    """mark_complete() should flip a task from not done to done."""
    task = Task("Morning walk", 30, "daily")
    assert task.completed is False      # starts incomplete

    task.mark_complete()

    assert task.completed is True       # now complete


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its number of tasks."""
    pet = Pet("Biscuit", "dog")
    assert len(pet.tasks) == 0          # no tasks yet

    pet.add_task(Task("Feeding", 10, "daily"))

    assert len(pet.tasks) == 1          # one task after adding
