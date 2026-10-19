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

Output of `python main.py`, which builds one owner, two pets, and six tasks, then prints the generated plan:

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
tests/test_pawpal.py ...........                                         [100%]
============================== 11 passed in 0.01s ==============================
```

The 11 tests cover task completion, adding tasks to pets, gathering tasks across pets, sorting, filtering, time-limited planning, conflict detection, and recurring tasks.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `sort_tasks`, `sort_by_time` | Priority, then due time, then shortest; or by preferred time |
| Filtering | `filter_tasks`, `generate_plan` | Filter by pet, status, category; tasks that don't fit are skipped with a reason |
| Conflict handling | `detect_conflicts` | Returns every pair of overlapping scheduled items |
| Recurring tasks | `complete_task` | Completing a daily or weekly task adds a fresh copy to the pet |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
