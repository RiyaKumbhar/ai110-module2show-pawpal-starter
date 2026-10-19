import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.caption(
    "Plan your pets' care for the day: add tasks, see them sorted and filtered, "
    "and get warned when two tasks collide."
)

st.divider()

# st.session_state is a dict-like "vault" that survives Streamlit reruns.
# Check for the key first so we only create the Owner once per session.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)
owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input("Minutes available today", 10, 600, owner.available_minutes, step=5)
    )

st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    c1, c2 = st.columns(2)
    new_pet_name = c1.text_input("Pet name")
    new_species = c2.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if not new_pet_name.strip():
            st.error("Please enter a pet name.")
        elif any(p.name == new_pet_name.strip() for p in owner.pets):
            st.error(f"{new_pet_name} is already added.")
        else:
            owner.add_pet(Pet(name=new_pet_name.strip(), species=new_species))
            st.success(f"Added {new_pet_name}!")

if owner.pets:
    st.write(", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.subheader("Tasks")
if owner.pets:
    with st.form("add_task", clear_on_submit=True):
        c1, c2 = st.columns(2)
        target = c1.selectbox("Pet", [p.name for p in owner.pets])
        title = c2.text_input("Task title", value="Morning walk")
        c3, c4, c5 = st.columns(3)
        duration = c3.number_input("Duration (min)", 1, 240, 20)
        priority = c4.selectbox("Priority", ["high", "medium", "low"])
        category = c5.selectbox(
            "Category", ["walk", "feeding", "meds", "enrichment", "grooming", "general"]
        )
        c6, c7, c8 = st.columns(3)
        frequency = c6.selectbox("Repeats", ["once", "daily", "weekly"])
        preferred = c7.time_input("Preferred time (optional)", value=None)
        due = c8.time_input("Due by (optional)", value=None)
        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == target)
            pet.add_task(
                Task(title=title, duration_minutes=int(duration), priority=priority,
                     category=category, frequency=frequency,
                     preferred_time=preferred, due_time=due)
            )
            st.success(f"Added '{title}' for {target}.")
else:
    st.caption("Add a pet first to start adding tasks.")

st.markdown("#### Your tasks")
f1, f2, f3 = st.columns(3)
view = f1.selectbox("Pet", ["All pets"] + [p.name for p in owner.pets])
status = f2.selectbox("Status", ["All", "Pending", "Completed"])
order = f3.selectbox("Sort by", ["Preferred time", "Priority"])

shown = scheduler.filter_tasks(
    pet_name=None if view == "All pets" else view,
    completed={"All": None, "Pending": False, "Completed": True}[status],
)
shown = scheduler.sort_by_time(shown) if order == "Preferred time" else scheduler.sort_tasks(shown)

# Surface preferred-time clashes right next to the list that causes them.
clashes = scheduler.find_time_conflicts()
if clashes:
    st.warning(
        f"**{len(clashes)} scheduling clash{'es' if len(clashes) != 1 else ''} found.** "
        "These tasks have preferred times that overlap:"
    )
    for msg in clashes:
        st.markdown(f"- {msg.removeprefix('WARNING: ')}")
    st.caption("Tip: move one of the tasks to a different time, or shorten its duration.")

if shown:
    st.table(
        [
            {"Time": f"{t.preferred_time:%H:%M}" if t.preferred_time else "any time",
             "Pet": t.pet_name, "Task": t.title, "Min": t.duration_minutes,
             "Priority": t.priority, "Repeats": t.frequency,
             "Done": "✅" if t.completed else "⏳"}
            for t in shown
        ]
    )
    pending = [t for t in shown if not t.completed]
    if pending:
        # Select by id: Streamlit passes back a copy of option objects, not the originals.
        labels = {t.id: f"{t.title} ({t.pet_name})" for t in pending}
        pick_id = st.selectbox("Mark a task complete", list(labels), format_func=labels.get)
        if st.button("Complete task"):
            pick = next(t for t in owner.get_all_tasks() if t.id == pick_id)
            nxt = scheduler.complete_task(pick)
            st.success(
                f"Completed '{pick.title}'."
                + (f" Next {pick.frequency} occurrence due {nxt.due_date:%b %d}." if nxt else "")
            )
            st.rerun()
else:
    st.info("No tasks match these filters." if owner.get_all_tasks() else "No tasks yet.")

st.divider()

st.subheader("Build Schedule")
if st.button("Generate schedule"):
    plan = scheduler.generate_plan()
    if not plan.scheduled and not plan.skipped:
        st.warning("Nothing to schedule. Add some pending tasks first.")
    else:
        st.success(
            f"Planned {plan.total_minutes} of {owner.available_minutes} minutes "
            f"({plan.remaining_minutes(owner)} min free)."
        )
        st.table(
            [
                {"Time": f"{i.start_time:%H:%M}-{i.end_time:%H:%M}", "Pet": i.task.pet_name,
                 "Task": i.task.title, "Why": i.reason}
                for i in plan.scheduled
            ]
        )
        if not plan.skipped and not scheduler.detect_conflicts(plan.scheduled):
            st.success("No conflicts: everything fits without overlaps.")
        for task, reason in plan.skipped:
            st.warning(f"Skipped '{task.title}' ({task.pet_name}): {reason}")
        for a, b in scheduler.detect_conflicts(plan.scheduled):
            st.error(
                f"Conflict: '{a.task.title}' ({a.start_time:%H:%M}-{a.end_time:%H:%M}) overlaps "
                f"'{b.task.title}' ({b.start_time:%H:%M}-{b.end_time:%H:%M}). "
                "Shorten one task or move it to another time."
            )
