"""Quick demo of the PawPal+ system.

Creates an owner with two pets and a few tasks, then prints today's schedule.
Run it with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    # 1. Create the owner
    owner = Owner("Jordan")

    # 2. Create two pets
    biscuit = Pet("Biscuit", "dog")
    mochi = Pet("Mochi", "cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # 3. Add tasks with different times (minutes) and frequencies
    biscuit.add_task(Task("Morning walk", 30, "daily"))
    biscuit.add_task(Task("Feeding", 10, "daily"))
    mochi.add_task(Task("Feeding", 5, "daily"))
    mochi.add_task(Task("Vet visit", 60, "weekly"))

    # 4. Use the scheduler to gather and print today's schedule
    scheduler = Scheduler(owner)
    today = scheduler.tasks_by_frequency("daily")

    line = "-" * 40
    print(line)
    print("TODAY'S SCHEDULE".center(40))
    print(f"Owner: {owner.name}".center(40))
    print(line)

    for pet in owner.pets:
        pet_tasks = [t for t in pet.tasks if t.frequency == "daily"]
        print(f"\n🐾 {pet.name} — {pet.species}")
        if not pet_tasks:
            print("   (no tasks today)")
            continue
        for task in pet_tasks:
            mark = "✓" if task.completed else " "
            # left-align the name, right-align the duration in a neat column
            print(f"   [{mark}] {task.description:<20} {task.time:>3} min")

    total_minutes = sum(t.time for t in today)
    print(f"\n{line}")
    print(f"Total: {len(today)} tasks, {total_minutes} minutes of care today.")
    print(line)


if __name__ == "__main__":
    main()
