# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## ✨ Features

- **Multi-pet care tracking:** one owner, many pets, each with their own tasks (walks, feeding, meds, enrichment, grooming).
- **Priority-based sorting:** tasks are ordered high to low, then by earliest due time, then shortest first (`Scheduler.sort_tasks`).
- **Sorting by time:** view tasks by preferred time of day instead (`Scheduler.sort_by_time`).
- **Filtering:** by pet, completion status, and category, across all pets (`Scheduler.filter_tasks`).
- **Time-budgeted daily plan:** fits tasks into the owner's available minutes and lists what was skipped, with a reason for each (`Scheduler.generate_plan`).
- **Plan explanations:** every scheduled task shows why it was chosen, such as priority, due time, or repeat frequency.
- **Conflict warnings:** flags tasks whose preferred times overlap, for the same pet or different pets, without crashing (`Scheduler.find_time_conflicts`), and detects overlaps inside a built plan (`Scheduler.detect_conflicts`).
- **Daily and weekly recurrence:** completing a recurring task creates the next one, due tomorrow or next week (`Scheduler.complete_task`, `Task.next_occurrence`).
- **Streamlit UI:** add pets and tasks, filter and sort the task list, mark tasks complete, and generate the schedule from the browser.

## 🏗️ Implementation Summary

The logic layer lives in `pawpal_system.py` (UML in `diagrams/uml.mmd`). Run the CLI demo with `python main.py`.

| Class | Role |
|-------|------|
| `Task` | One care activity: title, duration, priority, category, due/preferred time, frequency, completion status, and the name of its pet. |
| `Pet` | Pet details plus its list of tasks; adds, edits, removes, and lists pending tasks. |
| `Owner` | Owns several pets and the daily time budget. `get_all_tasks()` returns every pet's tasks together. |
| `Scheduler` | The brain. Reads tasks across all pets through `Owner.get_all_tasks()`, then sorts, filters, plans, and explains. |
| `ScheduledItem` | A task placed at a start and end time, with the reason it was placed there. |
| `DailyPlan` | The scheduler's output: scheduled items, skipped tasks with reasons, and a readable `summary()`. |

**How they work together:** an `Owner` has `Pet`s, each `Pet` has `Task`s. `Scheduler.generate_plan()` collects all pending tasks from the owner, sorts them, and fits them into the available minutes starting at `day_start`. It returns a `DailyPlan` of `ScheduledItem`s, and anything that doesn't fit is recorded as skipped with a reason.

## 🖥️ Sample Output

Full output of `python main.py`:

```
====================================================
  Today's Schedule for Riya (90 min available)
====================================================
Daily plan for Sunday, October 18:
  08:00 — Breakfast (10 min) [priority: high] (Mochi)
      why: high priority, due by 09:00, repeats daily
  08:10 — Give medication (5 min) [priority: high] (Mochi)
      why: high priority, due by 09:30, repeats daily
  08:15 — Morning walk (30 min) [priority: high] (Biscuit)
      why: high priority, due by 10:00, repeats daily
  08:45 — Clean litter box (15 min) [priority: medium] (Mochi)
      why: medium priority
  09:00 — Laser pointer play (20 min) [priority: medium] (Mochi)
      why: medium priority
Skipped:
  Brush coat (Biscuit) — not enough time left (10 min remaining)
Total scheduled: 80 min

--- Mochi's tasks only (filter by pet) ---
  Give medication [high]
  Breakfast [high]
  Laser pointer play [medium]
  Clean litter box [medium]

--- All tasks by preferred time (sort_by_time) ---
  08:00  Morning walk (Biscuit)
  08:30  Breakfast (Mochi)
  09:00  Give medication (Mochi)
  17:00  Laser pointer play (Mochi)
  18:00  Brush coat (Biscuit)
  any time  Clean litter box (Mochi)

--- Completing a recurring task ---
  'Morning walk' done; next occurrence created: True
  next 'Morning walk' is due Monday, Oct 19

--- Filter by status: completed vs pending ---
  Completed:
    Morning walk (Biscuit)
  Pending:
    Brush coat (Biscuit)
    Morning walk (Biscuit)
    Give medication (Mochi)
    Breakfast (Mochi)
    Laser pointer play (Mochi)
    Clean litter box (Mochi)

--- Filter by pet AND status (Biscuit, pending) ---
  Brush coat
  Morning walk

--- Same-time warnings (lightweight check) ---
  WARNING: 'Vet call' (Biscuit) at 09:00 overlaps 'Give medication' (Mochi) at 09:00 [different pets]
  WARNING: 'Vet call' (Biscuit) at 09:00 overlaps 'Teeth brushing' (Biscuit) at 09:05 [same pet]

--- Conflict detection (two tasks forced to overlap) ---
  CONFLICT: Breakfast overlaps Breakfast
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
tests/test_pawpal.py ........................                            [100%]
============================== 24 passed in 0.02s ==============================
```

The 24 tests cover task completion, adding tasks to pets, gathering tasks across pets, sorting, filtering, time-limited planning, conflict detection and same-time warnings, and recurring tasks with due dates.

## 📐 Smarter Scheduling

All of these live on `Scheduler` in `pawpal_system.py` (except `Task.next_occurrence`).

### Sorting
- **`Scheduler.sort_tasks(tasks)`**: orders by priority (high to low), then earliest `due_time`, then shortest duration. `generate_plan` uses this.
- **`Scheduler.sort_by_time(tasks)`**: orders by `preferred_time` (tasks with none go last), with priority as the tiebreaker. It uses `sorted()` with a lambda key that returns a tuple.

### Filtering
- **`Scheduler.filter_tasks(pet_name=None, completed=None, category=None)`**: filters across all of the owner's pets. Any combination works, for example `filter_tasks(pet_name="Mochi", completed=False)`.
- **`Scheduler.generate_plan()`** also filters: it skips completed tasks and tasks whose `due_date` is in the future, and tasks that don't fit the time budget go in the plan's skipped list with a reason.

### Conflict detection
- **`Scheduler.find_time_conflicts(tasks=None)`**: a lightweight check on the times the owner asked for (`preferred_time` plus duration). It covers the same pet and different pets, and returns warning strings such as `WARNING: 'Vet call' (Biscuit) at 09:00 overlaps 'Give medication' (Mochi) at 09:00 [different pets]`. It never raises, so the program keeps running.
- **`Scheduler.detect_conflicts(items)`**: checks a built plan and returns every pair of overlapping `ScheduledItem`s.

### Recurring tasks
- **`Scheduler.complete_task(task)`**: marks the task done and, for daily or weekly tasks, adds the next occurrence to the same pet.
- **`Task.next_occurrence()`**: builds that copy (new id, not completed) with `due_date` = today + `timedelta(days=1)` for daily or `timedelta(weeks=1)` for weekly. One-off tasks return `None`.

## 📸 Demo Walkthrough

Start the app with `streamlit run app.py` (it opens at http://localhost:8501).

**What you can do in the UI**
- **Owner:** set your name and how many minutes you have today.
- **Pets:** add a pet with a name and species. Empty or duplicate names are rejected.
- **Tasks:** add a task for a pet with a title, duration, priority, category, how often it repeats, and an optional due time.
- **Task list:** filter by pet, status, or category, sort by priority or by preferred time, and mark a task complete.
- **Build Schedule:** generate today's plan, see why each task was chosen, and see anything skipped or conflicting.

**Example workflow**
1. Set "Minutes available today" to 60.
2. Add a pet, "Mochi" (cat).
3. Add three tasks for Mochi: "Give medication" (5 min, high, daily), "Breakfast" (10 min, high, daily), and "Laser pointer play" (20 min, medium).
4. Sort the task list by preferred time, then filter to pending tasks only.
5. Click **Generate schedule** to see today's plan with a reason for each task.
6. Mark "Give medication" complete. Because it repeats daily, a new copy appears, due tomorrow.

**Scheduler behaviors you will see**
- **Sorting:** high-priority tasks come first in the plan; the same list can be re-sorted by preferred time.
- **Skipping:** a task that doesn't fit in the remaining minutes is listed as skipped, with the number of minutes left.
- **Conflict warnings:** tasks with overlapping preferred times show a warning next to the task list, and overlapping slots in a plan show an error.
- **Recurrence:** completing a daily or weekly task adds the next occurrence automatically.

**Sample CLI output** (`python main.py`). The start of the run shows the generated plan:

```
====================================================
  Today's Schedule for Riya (90 min available)
====================================================
Daily plan for Sunday, October 18:
  08:00 — Breakfast (10 min) [priority: high] (Mochi)
      why: high priority, due by 09:00, repeats daily
  08:10 — Give medication (5 min) [priority: high] (Mochi)
      why: high priority, due by 09:30, repeats daily
  08:15 — Morning walk (30 min) [priority: high] (Biscuit)
      why: high priority, due by 10:00, repeats daily
  08:45 — Clean litter box (15 min) [priority: medium] (Mochi)
      why: medium priority
  09:00 — Laser pointer play (20 min) [priority: medium] (Mochi)
      why: medium priority
Skipped:
  Brush coat (Biscuit) — not enough time left (10 min remaining)
```

And the end of the run shows the filtering, recurrence, and conflict checks:

```
--- Same-time warnings (lightweight check) ---
  WARNING: 'Vet call' (Biscuit) at 09:00 overlaps 'Give medication' (Mochi) at 09:00 [different pets]
  WARNING: 'Vet call' (Biscuit) at 09:00 overlaps 'Teeth brushing' (Biscuit) at 09:05 [same pet]

--- Conflict detection (two tasks forced to overlap) ---
  CONFLICT: Breakfast overlaps Breakfast
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

## Testing PawPal+

command to run tests (python -m pytest)

(base) riyakumbhar@Riyas-MacBook-Air ai110-module2show-pawpal-starter % source /Users/riyakumbhar/ai110-module2show-pawpal-starter/.venv/bin/activate
(.venv) (base) riyakumbhar@Riyas-MacBook-Air ai110-module2show-pawpal-starter % python -m pytest
================================================================= test session starts =================================================================
platform darwin -- Python 3.14.4, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/riyakumbhar/ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 24 items                                                                                                                                    

tests/test_pawpal.py ........................                                                                                                   [100%]

================================================================= 24 passed in 0.02s ==================================================================
(.venv) (base) riyakumbhar@Riyas-MacBook-Air ai110-module2show-pawpal-starter % 

