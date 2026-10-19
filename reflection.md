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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
