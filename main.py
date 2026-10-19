"""Terminal demo for the PawPal+ logic layer."""

from datetime import time

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner(name="Riya", available_minutes=90)

    biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever", age=3)
    mochi = Pet(name="Mochi", species="cat", breed="Tabby", age=5)
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Tasks are deliberately added out of chronological order.
    biscuit.add_task(Task("Brush coat", 25, "low", category="grooming",
                          preferred_time=time(18, 0)))
    biscuit.add_task(Task("Morning walk", 30, "high", category="walk",
                          preferred_time=time(8, 0), due_time=time(10, 0), frequency="daily"))
    mochi.add_task(Task("Give medication", 5, "high", category="meds",
                        preferred_time=time(9, 0), due_time=time(9, 30), frequency="daily"))
    mochi.add_task(Task("Breakfast", 10, "high", category="feeding",
                        preferred_time=time(8, 30), due_time=time(9, 0), frequency="daily"))
    mochi.add_task(Task("Laser pointer play", 20, "medium", category="enrichment",
                        preferred_time=time(17, 0)))
    mochi.add_task(Task("Clean litter box", 15, "medium", category="grooming"))

    scheduler = Scheduler(owner)

    print("=" * 52)
    print(f"  Today's Schedule for {owner.name} "
          f"({owner.available_minutes} min available)")
    print("=" * 52)
    print(scheduler.generate_plan().summary())

    print("\n--- Mochi's tasks only (filter by pet) ---")
    for task in scheduler.filter_tasks(pet_name="Mochi"):
        print(f"  {task.title} [{task.priority}]")

    print("\n--- All tasks by preferred time (sort_by_time) ---")
    for task in scheduler.sort_by_time(owner.get_all_tasks()):
        when = f"{task.preferred_time:%H:%M}" if task.preferred_time else "any time"
        print(f"  {when}  {task.title} ({task.pet_name})")

    print("\n--- Completing a recurring task ---")
    walk = scheduler.filter_tasks(pet_name="Biscuit", category="walk")[0]
    new_task = scheduler.complete_task(walk)
    print(f"  '{walk.title}' done; next occurrence created: {new_task is not None}")
    if new_task:
        print(f"  next '{new_task.title}' is due {new_task.due_date:%A, %b %d}")

    print("\n--- Filter by status: completed vs pending ---")
    for label, done in (("Completed", True), ("Pending", False)):
        print(f"  {label}:")
        for task in scheduler.filter_tasks(completed=done):
            print(f"    {task.title} ({task.pet_name})")

    print("\n--- Filter by pet AND status (Biscuit, pending) ---")
    for task in scheduler.filter_tasks(pet_name="Biscuit", completed=False):
        print(f"  {task.title}")

    print("\n--- Same-time warnings (lightweight check) ---")
    biscuit.add_task(Task("Vet call", 15, "medium", category="meds",
                          preferred_time=time(9, 0)))  # same time as Mochi's medication
    biscuit.add_task(Task("Teeth brushing", 10, "low", category="grooming",
                          preferred_time=time(9, 5)))  # overlaps Vet call, same pet
    for warning in scheduler.find_time_conflicts():
        print(f"  {warning}")

    print("\n--- Conflict detection (two tasks forced to overlap) ---")
    plan = scheduler.generate_plan()
    clash = plan.scheduled[0]
    plan.scheduled.append(
        type(clash)(clash.task, clash.start_time, clash.end_time, "forced overlap")
    )
    for a, b in scheduler.detect_conflicts(plan.scheduled):
        print(f"  CONFLICT: {a.task.title} overlaps {b.task.title}")


if __name__ == "__main__":
    main()
