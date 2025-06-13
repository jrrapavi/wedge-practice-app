import streamlit as st
import random
import json
import os
from datetime import datetime
import pandas as pd

# Constants
NUM_HOLES = 18
YARDAGE_MIN = 40
YARDAGE_MAX = 140
SESSION_FILE = "sessions.json"

# Generate 18 random target yardages
def generate_targets():
    return [random.randint(YARDAGE_MIN, YARDAGE_MAX) for _ in range(NUM_HOLES)]

# Scoring function: max 100, lose 2 points per yard off
def calculate_score(target, actual):
    diff = abs(target - actual)
    return max(0, 100 - diff * 2)

# Save session to JSON file
def save_session(data):
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            sessions = json.load(f)
    else:
        sessions = []

    sessions.append(data)

    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f, indent=2)

# Load past sessions
def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return []

def valid_input(val):
    if val.strip() == "":
        return None, "Please enter a number to continue."
    try:
        intval = int(val)
        if 0 <= intval <= 200:
            return intval, None
        else:
            return None, "Please enter a whole number between 0 and 200."
    except ValueError:
        return None, "Please enter a valid whole number."

def main():
    st.set_page_config(page_title="Wedge Practice", layout="centered")
    st.title("🏌️ Wedge Practice App")

    # Initialize session state once
    if "targets" not in st.session_state:
        st.session_state.targets = generate_targets()
        st.session_state.actuals = [None] * NUM_HOLES
        st.session_state.current_hole = 0
        st.session_state.complete = False
        st.session_state.inputs = {}  # hold text inputs by hole

    hole = st.session_state.current_hole
    target = st.session_state.targets[hole]

    if not st.session_state.complete:
        st.markdown(f"### Hole {hole + 1} of {NUM_HOLES}")
        st.markdown(f"🎯 **Target Distance:** `{target} yards`")

        # Load previous input for hole if exists
        prev_input = st.session_state.inputs.get(hole, "")

        with st.form(key=f"input_form_{hole}", clear_on_submit=False):
            user_input = st.text_input(
                "How far did you hit it? (yards)",
                value=prev_input,
                key=f"hole_input_{hole}"
            )
            submitted = st.form_submit_button("Save Input")

            actual, warning_msg = valid_input(user_input)
            if warning_msg:
                st.warning(warning_msg)

            if submitted:
                if warning_msg is None:
                    # Save valid input text and actual value
                    st.session_state.inputs[hole] = user_input
                    st.session_state.actuals[hole] = actual
                    st.success("Input saved!")
                else:
                    st.warning("Fix input before saving.")

        # Navigation buttons
        col1, col2 = st.columns(2)

        # Disable navigation buttons until current hole input saved & valid
        can_navigate = (hole in st.session_state.inputs) and (valid_input(st.session_state.inputs[hole])[1] is None)

        if hole > 0:
            if col1.button("⬅️ Back"):
                st.session_state.current_hole = hole - 1

        if hole < NUM_HOLES - 1:
            if col2.button("➡️ Next", disabled=not can_navigate):
                st.session_state.current_hole = hole + 1
        else:
            if col2.button("✅ Finish", disabled=not can_navigate):
                st.session_state.complete = True
                st.experimental_rerun()

    else:
        scores = [
            calculate_score(t, a if a is not None else 0) for t, a in zip(st.session_state.targets, st.session_state.actuals)
        ]
        total_score = sum(scores)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        session_data = {
            "date": date_str,
            "targets": st.session_state.targets,
            "actuals": st.session_state.actuals,
            "scores": scores,
            "total_score": total_score
        }

        save_session(session_data)

        st.success(f"🏆 Session complete! Total Score: **{total_score} / {NUM_HOLES * 100}**")
        st.subheader("📋 Shot Summary")
        for i in range(NUM_HOLES):
            actual_display = st.session_state.actuals[i] if st.session_state.actuals[i] is not None else "No Data"
            st.write(f"Hole {i+1}: Target {st.session_state.targets[i]} | "
                     f"Hit {actual_display} | "
                     f"Score: {scores[i]}")

        # Download CSV
        session_df = pd.DataFrame({
            "Hole": list(range(1, NUM_HOLES + 1)),
            "Target Yardage": st.session_state.targets,
            "Actual Yardage": [a if a is not None else "" for a in st.session_state.actuals],
            "Score": scores
        })
        session_df.loc[len(session_df.index)] = ["TOTAL", "", "", total_score]
        csv_data = session_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download This Session as CSV",
            data=csv_data,
            file_name=f"wedge_session_{date_str.replace(' ', '_').replace(':', '-')}.csv",
            mime="text/csv"
        )

        if st.button("🆕 Start New Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()

    # Session history and analysis
    st.markdown("---")
    st.subheader("📊 Session History")
    sessions = load_sessions()

    if sessions:
        df = pd.DataFrame(sessions)
        st.dataframe(df[["date", "total_score"]].sort_values("total_score", ascending=False), use_container_width=True)

        st.subheader("📈 Yardage Error Analysis")
        all_data = []
        for s in sessions:
            for t, a in zip(s["targets"], s["actuals"]):
                if a is not None:
                    all_data.append({"yardage": t, "error": abs(t - a)})

        yardage_df = pd.DataFrame(all_data)
        yardage_stats = yardage_df.groupby("yardage").mean().reset_index()
        st.line_chart(yardage_stats.set_index("yardage"))

if __name__ == "__main__":
    main()
