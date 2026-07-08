"""Quick demo of the PawPal+ system.

Creates an owner with two pets and a few tasks added *out of order*, then uses
the Scheduler's sorting and filtering methods to prove they organize the day
correctly. Run it with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a titled block of tasks in a neat column."""
    print(f"\n{title}")
    if not tasks:
        print("   (none)")
        return
    for task in tasks:
        mark = "✓" if task.completed else " "
        when = task.start_time if task.start_time else "  —  "
        print(f"   [{mark}] {when}  {task.description:<20} {task.time:>3} min")


def main() -> None:
    line = "-" * 48

    # 1. Create the owner and two pets
    owner = Owner("Jordan")
    biscuit = Pet("Biscuit", "dog")
    mochi = Pet("Mochi", "cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # 2. Add tasks intentionally OUT OF ORDER (by both duration and time of day)
    #    so the sorting methods have real work to do.
    biscuit.add_task(Task("Vet visit", 60, "weekly", start_time="09:00"))
    biscuit.add_task(Task("Morning walk", 30, "daily", start_time="08:00"))
    mochi.add_task(Task("Feeding", 5, "daily", start_time="08:15"))
    biscuit.add_task(Task("Feeding", 10, "daily", start_time="08:20"))
    mochi.add_task(Task("Nap check", 2, "daily"))  # no scheduled time

    # Two tasks booked at the EXACT same time (08:00) — one per pet. The owner
    # can't walk Biscuit and give Mochi meds at once, so this should warn.
    mochi.add_task(Task("Medication", 10, "daily", start_time="08:00"))

    # Mark one task done so the status filter has something to separate.
    mochi.tasks[0].mark_complete()  # Mochi's Feeding is done

    scheduler = Scheduler(owner)

    print(line)
    print("PAWPAL+ SCHEDULE DEMO".center(48))
    print(f"Owner: {owner.name}".center(48))
    print(line)

    # 3. Sorting — by duration (shortest first) and by time of day
    print_tasks("Sorted by DURATION (shortest first):", scheduler.sorted_by_time())
    print_tasks(
        "Sorted by DURATION (longest first):",
        scheduler.sorted_by_time(ascending=False),
    )
    print_tasks("Sorted by TIME OF DAY:", scheduler.sorted_by_start_time())

    # 4. Filtering — by pet name and by completion status
    print_tasks('Filter by pet name "Biscuit":', scheduler.filter_tasks("biscuit"))
    print_tasks("Filter to STILL-TO-DO tasks:", scheduler.filter_tasks(completed=False))
    print_tasks("Filter to COMPLETED tasks:", scheduler.filter_tasks(completed=True))

    # 5. Conflict detection — returns warning strings, never crashes.
    print("\nConflict check:")
    warnings = scheduler.conflict_warnings()
    if not warnings:
        print("   No conflicts — the day is clear.")
    for message in warnings:
        print(f"   {message}")

    # 6. Recurring auto-scheduling — completing a daily task spawns the next one
    from datetime import date

    today = date(2026, 7, 7)
    walk = biscuit.tasks[1]  # Biscuit's daily "Morning walk"
    print("\nCompleting a recurring task:")
    print(f"   Marking '{walk.description}' complete on {today}...")
    upcoming = scheduler.complete_task(walk, on=today)
    if upcoming:
        print(
            f"   ↻ Auto-scheduled next '{upcoming.description}' "
            f"({upcoming.frequency}) due {upcoming.due_date}."
        )

    # 7. Totals
    pending = scheduler.filter_tasks(completed=False)
    total_minutes = sum(t.time for t in pending)
    print(f"\n{line}")
    print(f"{len(pending)} tasks still to do, {total_minutes} minutes of care remaining.")
    print(line)


if __name__ == "__main__":
    main()
