"""PawPal+ logic layer: backend classes for pet care planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from copy import copy
from datetime import date, datetime, time, timedelta
from uuid import uuid4

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str = "medium"  # "high" | "medium" | "low"
    category: str = "general"  # walk, feeding, meds, enrichment, grooming
    preferred_time: time | None = None
    due_time: time | None = None
    pet_name: str = ""  # set by Pet.add_task so a plan can say which pet a task is for
    frequency: str = "once"  # "once" | "daily" | "weekly"
    completed: bool = False
    id: str = field(default_factory=lambda: uuid4().hex[:8])

    def __post_init__(self) -> None:
        """Reject priorities other than high, medium, or low."""
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"priority must be one of {list(PRIORITY_ORDER)}")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def update(self, **changes) -> None:
        """Change task fields by name and re-validate the result."""
        for key, value in changes.items():
            if not hasattr(self, key):
                raise AttributeError(f"Task has no field '{key}'")
            setattr(self, key, value)
        self.__post_init__()

    def is_high_priority(self) -> bool:
        """Return True if this task is high priority."""
        return self.priority == "high"


@dataclass
class Pet:
    name: str
    species: str
    breed: str = ""
    age: int | None = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and record the pet's name on it."""
        task.pet_name = self.name
        self.tasks.append(task)

    def edit_task(self, task_id: str, **changes) -> None:
        """Update the fields of the task with the given id."""
        self._find(task_id).update(**changes)

    def remove_task(self, task_id: str) -> None:
        """Delete the task with the given id from this pet."""
        self.tasks.remove(self._find(task_id))

    def get_pending_tasks(self) -> list[Task]:
        """Return the tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def _find(self, task_id: str) -> Task:
        """Return the task with the given id, or raise KeyError."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"No task with id '{task_id}'")


@dataclass
class Owner:
    name: str
    available_minutes: int = 120
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        self.pets.remove(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return every task from every pet, combined into one list."""
        return [t for pet in self.pets for t in pet.tasks]

    def get_pending_tasks(self) -> list[Task]:
        """Return the tasks that are not yet completed."""
        return [t for pet in self.pets for t in pet.get_pending_tasks()]

    def update_preferences(self, **prefs) -> None:
        """Merge new preferences into the owner's preferences."""
        self.preferences.update(prefs)


@dataclass
class ScheduledItem:
    task: Task
    start_time: time
    end_time: time
    reason: str = ""

    def overlaps(self, other: ScheduledItem) -> bool:
        """Return True if this item's time slot overlaps the other's."""
        return self.start_time < other.end_time and other.start_time < self.end_time

    def describe(self) -> str:
        """Return a one-line, human-readable description of this item."""
        return (
            f"{self.start_time:%H:%M} — {self.task.title} "
            f"({self.task.duration_minutes} min) [priority: {self.task.priority}]"
        )


@dataclass
class DailyPlan:
    plan_date: date = field(default_factory=date.today)
    scheduled: list[ScheduledItem] = field(default_factory=list)
    skipped: list[tuple[Task, str]] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        """Total duration of all scheduled items, in minutes."""
        return sum(i.task.duration_minutes for i in self.scheduled)

    def add_item(self, item: ScheduledItem) -> None:
        """Append a scheduled item to the plan."""
        self.scheduled.append(item)

    def remaining_minutes(self, owner: Owner) -> int:
        """Return the owner's available minutes minus the scheduled total."""
        return owner.available_minutes - self.total_minutes

    def summary(self) -> str:
        """Return the plan as readable text, including skipped tasks."""
        lines = [f"Daily plan for {self.plan_date:%A, %B %d}:"]
        for item in self.scheduled:
            pet = f" ({item.task.pet_name})" if item.task.pet_name else ""
            lines.append(f"  {item.describe()}{pet}")
            if item.reason:
                lines.append(f"      why: {item.reason}")
        if self.skipped:
            lines.append("Skipped:")
            for task, reason in self.skipped:
                lines.append(f"  {task.title} ({task.pet_name}) — {reason}")
        lines.append(f"Total scheduled: {self.total_minutes} min")
        return "\n".join(lines)


def _add_minutes(start: time, minutes: int) -> time | None:
    """Return start + minutes, or None if it would run past midnight."""
    end = datetime.combine(date.today(), start) + timedelta(minutes=minutes)
    return end.time() if end.date() == date.today() else None


class Scheduler:
    """Builds plans from every pet's tasks, read through Owner.get_all_tasks()."""

    def __init__(self, owner: Owner, day_start: time = time(8, 0)):
        """Create a scheduler for the given owner, starting the day at day_start."""
        self.owner = owner
        self.day_start = day_start

    # --- algorithmic feature 1: sorting -------------------------------------
    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Priority first (high to low), then earliest due time, then shortest."""
        return sorted(
            tasks,
            key=lambda t: (
                PRIORITY_ORDER[t.priority],
                t.due_time or time.max,
                t.duration_minutes,
            ),
        )

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Order by preferred time (tasks without one last), then priority."""
        return sorted(
            tasks,
            key=lambda t: (t.preferred_time or time.max, PRIORITY_ORDER[t.priority]),
        )

    # --- algorithmic feature 2: filtering -----------------------------------
    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        category: str | None = None,
    ) -> list[Task]:
        """Filter tasks across all of the owner's pets."""
        return [
            t
            for t in self.owner.get_all_tasks()
            if (pet_name is None or t.pet_name == pet_name)
            and (completed is None or t.completed == completed)
            and (category is None or t.category == category)
        ]

    # --- algorithmic feature 3: conflict detection --------------------------
    def detect_conflicts(
        self, items: list[ScheduledItem]
    ) -> list[tuple[ScheduledItem, ScheduledItem]]:
        """Return every pair of scheduled items whose time slots overlap."""
        ordered = sorted(items, key=lambda i: i.start_time)
        return [
            (a, b)
            for n, a in enumerate(ordered)
            for b in ordered[n + 1 :]
            if a.overlaps(b)
        ]

    # --- algorithmic feature 4: recurring tasks -----------------------------
    def complete_task(self, task: Task) -> Task | None:
        """Mark a task done; daily/weekly tasks get a fresh copy for next time."""
        task.mark_complete()
        if task.frequency == "once":
            return None
        pet = next((p for p in self.owner.pets if p.name == task.pet_name), None)
        if pet is None:
            return None
        nxt = copy(task)
        nxt.completed = False
        nxt.id = uuid4().hex[:8]
        pet.add_task(nxt)
        return nxt

    # --- planning -----------------------------------------------------------
    def generate_plan(self) -> DailyPlan:
        """Fit pending tasks from all pets into the owner's available time."""
        plan = DailyPlan()
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        clock = self.day_start
        for task in self.sort_tasks(pending):
            if plan.total_minutes + task.duration_minutes > self.owner.available_minutes:
                plan.skipped.append(
                    (task, f"not enough time left ({plan.remaining_minutes(self.owner)} min remaining)")
                )
                continue
            end = _add_minutes(clock, task.duration_minutes)
            if end is None:
                plan.skipped.append((task, "would run past the end of the day"))
                continue
            plan.add_item(ScheduledItem(task, clock, end, self.explain_choice(task)))
            clock = end
        return plan

    def explain_choice(self, task: Task) -> str:
        """Return a short reason describing why this task was scheduled."""
        reason = f"{task.priority} priority"
        if task.due_time:
            reason += f", due by {task.due_time:%H:%M}"
        if task.frequency != "once":
            reason += f", repeats {task.frequency}"
        return reason
