from datetime import time

import pytest

from pawpal_system import Owner, Pet, ScheduledItem, Scheduler, Task


@pytest.fixture
def owner():
    o = Owner("Riya", available_minutes=60)
    dog, cat = Pet("Biscuit", "dog"), Pet("Mochi", "cat")
    o.add_pet(dog)
    o.add_pet(cat)
    return o


def test_mark_complete_changes_status():
    task = Task("Walk", 30)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_invalid_priority_rejected():
    with pytest.raises(ValueError):
        Task("Walk", 30, priority="urgent")


def test_add_task_sets_pet_name_and_grows_list(owner):
    dog = owner.pets[0]
    dog.add_task(Task("Walk", 30))
    assert len(dog.tasks) == 1
    assert dog.tasks[0].pet_name == "Biscuit"


def test_owner_get_all_tasks_spans_pets(owner):
    owner.pets[0].add_task(Task("Walk", 30))
    owner.pets[1].add_task(Task("Feed", 10))
    assert {t.title for t in owner.get_all_tasks()} == {"Walk", "Feed"}


def test_sort_tasks_by_priority_then_due_time_then_duration(owner):
    s = Scheduler(owner)
    low = Task("low", 5, "low")
    late = Task("late", 20, "high", due_time=time(11))
    early = Task("early", 20, "high", due_time=time(9))
    med = Task("med", 5, "medium")
    assert s.sort_tasks([low, late, med, early]) == [early, late, med, low]


def test_filter_tasks_by_pet_and_status(owner):
    dog, cat = owner.pets
    walk, feed = Task("Walk", 30), Task("Feed", 10)
    dog.add_task(walk)
    cat.add_task(feed)
    feed.mark_complete()
    s = Scheduler(owner)
    assert s.filter_tasks(pet_name="Biscuit") == [walk]
    assert s.filter_tasks(completed=True) == [feed]


def test_generate_plan_respects_time_limit_across_pets(owner):
    owner.pets[0].add_task(Task("Walk", 40, "high"))
    owner.pets[1].add_task(Task("Play", 30, "medium"))
    plan = Scheduler(owner).generate_plan()
    assert [i.task.title for i in plan.scheduled] == ["Walk"]
    assert [t.title for t, _ in plan.skipped] == ["Play"]
    assert plan.total_minutes <= owner.available_minutes


def test_generate_plan_has_no_overlaps_and_skips_completed(owner):
    done = Task("Done", 10)
    owner.pets[0].add_task(done)
    owner.pets[0].add_task(Task("Walk", 20))
    owner.pets[1].add_task(Task("Feed", 10))
    done.mark_complete()
    s = Scheduler(owner)
    plan = s.generate_plan()
    assert "Done" not in [i.task.title for i in plan.scheduled]
    assert s.detect_conflicts(plan.scheduled) == []


def test_detect_conflicts_finds_overlap(owner):
    a = ScheduledItem(Task("A", 30), time(8, 0), time(8, 30))
    b = ScheduledItem(Task("B", 30), time(8, 15), time(8, 45))
    c = ScheduledItem(Task("C", 10), time(9, 0), time(9, 10))
    assert Scheduler(owner).detect_conflicts([a, b, c]) == [(a, b)]


def test_complete_recurring_task_creates_next_occurrence(owner):
    dog = owner.pets[0]
    walk = Task("Walk", 30, frequency="daily")
    dog.add_task(walk)
    nxt = Scheduler(owner).complete_task(walk)
    assert walk.completed and nxt is not None
    assert not nxt.completed and nxt.id != walk.id
    assert len(dog.tasks) == 2


def test_complete_one_off_task_creates_nothing(owner):
    dog = owner.pets[0]
    task = Task("Vet", 60)
    dog.add_task(task)
    assert Scheduler(owner).complete_task(task) is None
    assert len(dog.tasks) == 1
