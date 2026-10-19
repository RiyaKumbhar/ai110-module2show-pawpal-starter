import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
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
        c6, c7 = st.columns(2)
        frequency = c6.selectbox("Repeats", ["once", "daily", "weekly"])
        due = c7.time_input("Due by (optional)", value=None)
        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == target)
            pet.add_task(
                Task(title=title, duration_minutes=int(duration), priority=priority,
                     category=category, frequency=frequency, due_time=due)
            )
            st.success(f"Added '{title}' for {target}.")
else:
    st.caption("Add a pet first to start adding tasks.")

view = st.selectbox("Show tasks for", ["All pets"] + [p.name for p in owner.pets])
shown = scheduler.filter_tasks(pet_name=None if view == "All pets" else view)
if shown:
    st.table(
        [
            {"Pet": t.pet_name, "Task": t.title, "Min": t.duration_minutes,
             "Priority": t.priority, "Repeats": t.frequency,
             "Done": "yes" if t.completed else "no"}
            for t in shown
        ]
    )
    pending = [t for t in shown if not t.completed]
    if pending:
        pick = st.selectbox(
            "Mark a task complete", pending, format_func=lambda t: f"{t.title} ({t.pet_name})"
        )
        if st.button("Complete task"):
            nxt = scheduler.complete_task(pick)
            st.success(
                f"Completed '{pick.title}'."
                + (f" Next {pick.frequency} occurrence added." if nxt else "")
            )
            st.rerun()
else:
    st.info("No tasks yet.")

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
        for task, reason in plan.skipped:
            st.warning(f"Skipped '{task.title}' ({task.pet_name}): {reason}")
        for a, b in scheduler.detect_conflicts(plan.scheduled):
            st.error(f"Conflict: {a.task.title} overlaps {b.task.title}")
