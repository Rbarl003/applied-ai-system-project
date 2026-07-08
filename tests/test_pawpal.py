"""Simple tests for the PawPal+ system."""

import os
import sys

# Make sure the project root is importable when running pytest from anywhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Task, Scheduler


def _owner_with_tasks():
    """Build an owner with two pets and a mix of tasks for scheduler tests."""
    owner = Owner("Jordan")
    biscuit = Pet("Biscuit", "dog")
    mochi = Pet("Mochi", "cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    biscuit.add_task(Task("Morning walk", 30, "daily", start_time="08:00"))
    biscuit.add_task(Task("Feeding", 10, "daily", start_time="08:15"))
    mochi.add_task(Task("Feeding", 5, "daily", completed=True))
    mochi.add_task(Task("Vet visit", 60, "weekly", start_time="09:00"))
    return owner, biscuit, mochi


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


# --- 1. Sorting by time ------------------------------------------------------
def test_sorted_by_time_orders_shortest_first():
    owner, _, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)

    durations = [t.time for t in scheduler.sorted_by_time()]

    assert durations == sorted(durations)      # ascending by default
    assert durations[0] == 5                   # shortest task leads


def test_sorted_by_time_descending():
    owner, _, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)

    durations = [t.time for t in scheduler.sorted_by_time(ascending=False)]

    assert durations == [60, 30, 10, 5]        # longest task leads


def test_sorted_by_start_time_orders_the_day():
    owner, _, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)

    order = [t.description for t in scheduler.sorted_by_start_time()]

    # Morning walk 08:00, Feeding 08:15, Vet 09:00; Mochi's Feeding has no time.
    assert order[:3] == ["Morning walk", "Feeding", "Vet visit"]
    assert order[-1] == "Feeding"          # unscheduled task sinks to the end


def test_sorted_by_start_time_uses_clock_order_not_string_order():
    owner = Owner("Jordan")
    pet = Pet("Biscuit", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Late", 10, "daily", start_time="10:15"))
    pet.add_task(Task("Early", 10, "daily", start_time="9:30"))   # not zero-padded
    scheduler = Scheduler(owner)

    order = [t.description for t in scheduler.sorted_by_start_time()]

    # As strings "10:15" < "9:30", but 9:30 really comes first in the day.
    assert order == ["Early", "Late"]


# --- 2. Filtering by pet / status -------------------------------------------
def test_filter_by_pet():
    owner, biscuit, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)

    biscuit_tasks = scheduler.filter_tasks(pet=biscuit)

    assert {t.description for t in biscuit_tasks} == {"Morning walk", "Feeding"}


def test_filter_by_status():
    owner, _, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)

    done = scheduler.filter_tasks(completed=True)

    assert len(done) == 1 and done[0].description == "Feeding"


def test_filter_combines_pet_and_status():
    owner, _, mochi = _owner_with_tasks()
    scheduler = Scheduler(owner)

    pending_for_mochi = scheduler.filter_tasks(pet=mochi, completed=False)

    assert [t.description for t in pending_for_mochi] == ["Vet visit"]


def test_filter_by_pet_name_is_case_insensitive():
    owner, _, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)

    tasks = scheduler.filter_tasks(" mochi ")          # messy casing + spaces

    assert {t.description for t in tasks} == {"Feeding", "Vet visit"}


def test_filter_by_pet_name_combines_with_status():
    owner, _, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)

    pending = scheduler.filter_tasks("Mochi", completed=False)

    assert [t.description for t in pending] == ["Vet visit"]


def test_filter_by_unknown_pet_name_returns_empty():
    owner, _, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)

    assert scheduler.filter_tasks("Rex") == []


# --- 3. Recurring tasks ------------------------------------------------------
def test_never_completed_task_is_due():
    task = Task("Morning walk", 30, "daily")
    assert task.is_due(date(2026, 7, 7)) is True


def test_daily_task_due_next_day_but_not_same_day():
    today = date(2026, 7, 7)
    task = Task("Feeding", 10, "daily", last_completed=today)

    assert task.is_due(today) is False
    assert task.is_due(today + timedelta(days=1)) is True


def test_weekly_task_waits_seven_days():
    today = date(2026, 7, 7)
    task = Task("Vet visit", 60, "weekly", last_completed=today)

    assert task.is_due(today + timedelta(days=3)) is False
    assert task.is_due(today + timedelta(days=7)) is True


def test_next_occurrence_daily_is_one_day_later():
    today = date(2026, 7, 7)
    task = Task("Feeding", 10, "daily", start_time="08:00")

    nxt = task.next_occurrence(completed_on=today)

    assert nxt is not None
    assert nxt.due_date == date(2026, 7, 8)     # today + 1 day
    assert nxt.completed is False
    assert nxt.start_time == "08:00"            # keeps the scheduled time


def test_next_occurrence_weekly_is_seven_days_later():
    task = Task("Vet visit", 60, "weekly")

    nxt = task.next_occurrence(completed_on=date(2026, 7, 7))

    assert nxt.due_date == date(2026, 7, 14)    # today + 7 days


def test_next_occurrence_handles_month_boundary():
    task = Task("Feeding", 10, "daily")

    nxt = task.next_occurrence(completed_on=date(2026, 7, 31))

    assert nxt.due_date == date(2026, 8, 1)     # timedelta rolls the month over


def test_one_off_frequency_does_not_repeat():
    task = Task("Adopt", 30, "once")            # unknown / non-repeating

    assert task.next_occurrence(completed_on=date(2026, 7, 7)) is None


def test_complete_task_spawns_next_instance_on_same_pet():
    owner, biscuit, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)
    walk = biscuit.tasks[0]                      # daily Morning walk
    before = len(biscuit.tasks)

    new_task = scheduler.complete_task(walk, on=date(2026, 7, 7))

    assert walk.completed is True                       # original is done
    assert len(biscuit.tasks) == before + 1             # a new one appeared
    assert new_task in biscuit.tasks                    # on the same pet
    assert new_task.completed is False
    assert new_task.due_date == date(2026, 7, 8)


def test_complete_task_one_off_adds_nothing():
    owner = Owner("Jordan")
    pet = Pet("Biscuit", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Adopt", 30, "once"))
    scheduler = Scheduler(owner)

    result = scheduler.complete_task(pet.tasks[0], on=date(2026, 7, 7))

    assert result is None
    assert len(pet.tasks) == 1                   # no repeat scheduled


def test_due_tasks_skips_recently_done():
    owner, biscuit, _ = _owner_with_tasks()
    today = date(2026, 7, 7)
    biscuit.tasks[0].mark_complete(on=today)      # walk done today
    scheduler = Scheduler(owner)

    due = scheduler.due_tasks(today)

    assert "Morning walk" not in {t.description for t in due}


# --- 4. Conflict detection ---------------------------------------------------
def test_detect_conflicts_finds_overlap():
    owner, _, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)

    conflicts = scheduler.detect_conflicts()

    # Walk 08:00-08:30 overlaps Feeding 08:15-08:25; Vet 09:00 is clear.
    assert len(conflicts) == 1
    descriptions = {conflicts[0][0].description, conflicts[0][1].description}
    assert descriptions == {"Morning walk", "Feeding"}


def test_grouped_conflicts_collapses_shared_anchor():
    owner, _, _ = _owner_with_tasks()
    scheduler = Scheduler(owner)

    groups = scheduler.grouped_conflicts()

    # In this fixture only Biscuit's Feeding (08:15) has a start time, so
    # Morning walk (08:00-08:30) anchors a single grouped overlap.
    assert len(groups) == 1
    anchor, others = groups[0]
    assert anchor.description == "Morning walk"
    assert [t.description for t in others] == ["Feeding"]


def test_grouped_conflicts_merges_multiple_overlaps_into_one_line():
    owner = Owner("Jordan")
    pet = Pet("Biscuit", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "daily", start_time="08:00"))    # 08:00-08:30
    pet.add_task(Task("Feed", 5, "daily", start_time="08:10"))     # inside walk
    pet.add_task(Task("Brush", 5, "daily", start_time="08:20"))    # inside walk
    scheduler = Scheduler(owner)

    groups = scheduler.grouped_conflicts()

    # Walk clashes with both Feed and Brush, but collapses to ONE anchor line.
    assert len(groups) == 1
    anchor, others = groups[0]
    assert anchor.description == "Walk"
    assert [t.description for t in others] == ["Feed", "Brush"]


def test_pet_of_finds_owner_by_identity():
    owner, biscuit, mochi = _owner_with_tasks()
    scheduler = Scheduler(owner)

    walk = biscuit.tasks[0]          # Biscuit's Morning walk
    vet = mochi.tasks[1]             # Mochi's Vet visit

    assert scheduler.pet_of(walk) is biscuit
    assert scheduler.pet_of(vet) is mochi
    assert scheduler.pet_of(Task("Ghost", 1, "daily")) is None


def test_same_start_time_is_a_conflict_across_pets():
    owner = Owner("Jordan")
    dog = Pet("Biscuit", "dog")
    cat = Pet("Mochi", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task("Walk", 30, "daily", start_time="08:00"))
    cat.add_task(Task("Medication", 10, "daily", start_time="08:00"))  # same time
    scheduler = Scheduler(owner)

    assert len(scheduler.detect_conflicts()) == 1


def test_conflict_warnings_returns_readable_message():
    owner = Owner("Jordan")
    dog = Pet("Biscuit", "dog")
    cat = Pet("Mochi", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task("Walk", 30, "daily", start_time="08:00"))
    cat.add_task(Task("Medication", 10, "daily", start_time="08:00"))
    scheduler = Scheduler(owner)

    warnings = scheduler.conflict_warnings()

    assert len(warnings) == 1
    msg = warnings[0]
    assert "Biscuit: Walk" in msg
    assert "Mochi: Medication" in msg
    assert "same time" in msg


def test_conflict_warnings_empty_when_clear():
    owner = Owner("Jordan")
    pet = Pet("Biscuit", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "daily", start_time="08:00"))
    pet.add_task(Task("Feed", 10, "daily", start_time="09:00"))
    scheduler = Scheduler(owner)

    assert scheduler.conflict_warnings() == []


def test_malformed_start_time_is_skipped_not_fatal():
    owner = Owner("Jordan")
    pet = Pet("Biscuit", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "daily", start_time="8am"))     # bad format
    pet.add_task(Task("Feed", 10, "daily", start_time="08:00"))
    scheduler = Scheduler(owner)

    # Should not raise; the unparseable task is simply ignored.
    assert scheduler.detect_conflicts() == []
    assert scheduler.conflict_warnings() == []


def test_no_conflict_when_times_are_clear():
    owner = Owner("Jordan")
    pet = Pet("Biscuit", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "daily", start_time="08:00"))
    pet.add_task(Task("Feeding", 10, "daily", start_time="08:30"))  # starts as walk ends
    scheduler = Scheduler(owner)

    assert scheduler.detect_conflicts() == []


def test_unscheduled_tasks_never_conflict():
    owner = Owner("Jordan")
    pet = Pet("Biscuit", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "daily"))        # no start_time
    pet.add_task(Task("Feeding", 10, "daily"))     # no start_time
    scheduler = Scheduler(owner)

    assert scheduler.detect_conflicts() == []
