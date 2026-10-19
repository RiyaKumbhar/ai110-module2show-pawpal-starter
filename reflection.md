# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML had six classes, each with one clear job, built around the three core user actions (enter owner/pet info, add/edit tasks, generate and view a daily plan):

- **Owner**: holds basic owner info (name) and preferences, plus the time available per day. It owns one or more pets and supplies the time constraint the scheduler works within.
- **Pet**: holds basic pet info (name, species/breed) and the list of care tasks for that pet. It is responsible for adding, editing, and removing its own tasks.
- **Task**: represents a single care activity (walk, feeding, meds, enrichment, grooming). It stores a title, duration in minutes, and priority, and can be marked complete. It holds data only and has no scheduling logic.
- **Scheduler**: takes an owner's pet(s) and tasks and builds the daily plan. It sorts tasks by priority, fits them into the available time, and records a reason for each task it includes or leaves out so the plan can be explained to the user.
- **ScheduledItem**: a task placed at a specific start and end time, with the reason it was placed there. It can check whether it overlaps another item.
- **DailyPlan**: the scheduler's output. It holds the scheduled items and the skipped tasks (with reasons), and produces the summary shown to the user.

Relationships: an Owner has one or more Pets, a Pet has many Tasks, the Scheduler uses the Owner (for time and preferences) and the Tasks (for duration and priority) to produce a DailyPlan, and a DailyPlan contains ScheduledItems that each point to a Task. I kept scheduling logic in the Scheduler rather than in Task or Pet so the data classes stay simple and the scheduling behavior is easy to test on its own.

**b. Design changes**

Yes. After writing the class skeletons, I reviewed them for missing relationships and logic bottlenecks and made these changes:

- **Task now knows its pet (`pet_name`).** Originally a Task had no link back to its Pet, so once the Scheduler pulled tasks from several pets into one list, the plan couldn't say which pet each task was for. `Pet.add_task` now sets `pet_name` automatically.
- **Task gained `due_time`.** I only had `preferred_time`, but a task also needs a deadline so the scheduler can sort by time and detect conflicts.
- **Priority is validated.** Priority was a free-form string, so a typo like "urgent" would silently break sorting. Task now raises a `ValueError` unless the priority is high, medium, or low, both on creation and on update.
- **`Owner.get_pending_tasks()` added.** The Scheduler should only plan tasks that aren't completed, and across all pets. This method gives it that list in one call instead of making it filter every time.

I updated `diagrams/uml.mmd` to match. One bottleneck I noticed but have not fixed yet is recurring tasks: marking a daily or weekly task complete doesn't create the next occurrence. I plan to handle that when I implement the scheduling logic.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: the owner's total available minutes for the day, task priority (high, medium, low), and each task's `due_time`. `generate_plan` sorts pending tasks by priority, then earliest due time, then shortest duration, and adds them until the time budget runs out. Anything that doesn't fit goes into the plan's skipped list with a reason. I made the time budget a hard limit and priority the main sort key because a pet owner's real problem is "I only have 90 minutes, what must not be missed?" Medication and feeding should beat grooming. `preferred_time` is only used by `sort_by_time` for display; the planner does not use it to place tasks.

**b. Tradeoffs**

The planner is greedy and places tasks back to back from the day start (8:00 by default) in priority order. It ignores `preferred_time`, so a 6 PM task can be scheduled at 8:40 AM. It also never looks ahead, so a short low-priority task can be skipped even when a different combination of tasks would have used the time better. That is simple, predictable, and easy to explain ("why:" is printed for each item), which suits a small personal app, and the plan never overlaps because tasks are laid out sequentially. The cost is realism: a human would want the evening brush at 6 PM. Conflict detection (`detect_conflicts`) therefore matters mostly for plans built or edited by hand, since the generated plan cannot overlap on its own.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used Claude Code for design brainstorming, code generation, and review. I asked it to brainstorm the objects and their attributes and methods, draft the Mermaid class diagram, generate the dataclass skeletons from that UML, review the skeleton for missing relationships, and then implement the Scheduler, `main.py`, and the pytest suite. The most helpful prompts were specific and tied to a deliverable, such as "review my skeleton for missing relationships or logic bottlenecks" or "the Scheduler must read tasks through the Owner method." Those produced concrete changes instead of generic advice.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

**What the AI suggested and what I accepted:** The AI proposed six classes, adding `ScheduledItem` and `DailyPlan` beyond the four required, and I accepted them so each plan could carry a reason for every task and a list of skipped tasks. After its skeleton review I also accepted four changes: `pet_name` and `due_time` on Task, priority validation, and `Owner.get_pending_tasks()`.

**What I rejected or corrected:** The AI flagged that the planner ignores `preferred_time` and places tasks back-to-back, and I treated that as a known limitation instead of accepting the output as finished.

**How I verified it:** I did not trust the generated code on sight. I ran `python main.py` and read the schedule against the inputs (the task that didn't fit was skipped with the right reason), and I ran `python -m pytest`, where all 11 tests pass. The tests check behavior, such as sorting order, the time limit across two pets, no overlaps, and recurring tasks creating a fresh copy, so they would fail if the logic were wrong.

---

## 4. Testing and Verification

**a. What you tested**

I wrote 11 pytest tests in `tests/test_pawpal.py`. They cover marking a task complete, rejecting an invalid priority, `add_task` setting `pet_name`, collecting tasks across pets, sort order (priority, then due time, then duration), filtering by pet and status, the time limit holding across two pets, no overlaps and completed tasks skipped, conflict detection on an overlapping pair, and recurring versus one-off completion. I tested these because they are the places where a silent bug would give an owner a wrong plan without any error.

**b. Confidence**

I'm fairly confident in the core behavior: all 11 tests pass and I read the `main.py` output against the inputs. I'm less confident about edge cases I haven't tested: a task longer than the whole day, tasks running past midnight (the code skips them, but no test checks it), two pets with the same name (the `pet_name` lookup in `complete_task` would pick the first), an empty owner with no pets, and completing the same recurring task twice, which creates two copies. I would test those next, plus sorting when `preferred_time` is missing on every task.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with keeping the data classes simple and putting all the logic (sorting, filtering, conflicts, recurrence, planning) in `Scheduler`. It made the logic easy to test without any UI, and the same code drives both the `main.py` demo and the Streamlit app. Giving each plan a reason for every scheduled and skipped task also makes the result explainable.

**b. What you would improve**

I'd make the planner respect `preferred_time` and fill gaps instead of stacking everything from 8:00. I'd also give recurring tasks an actual due date (the next occurrence is currently just a copy with no date), and add real calendar dates to tasks so a "weekly" task is not only a label.

**c. Key takeaway**

AI is fast at producing a plausible first version, but it was only useful when I gave it a specific deliverable and then checked the result myself. The planner it generated ran without errors and still ignored `preferred_time`; I only noticed by reading the output against my inputs. Tests and reading the real output caught what "it runs" did not.
