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

# Simple scoring: 100 max, minus 2 points per yard off
def calculate_score(target, actual):
    diff = abs(target - actual)
    return max(0, round(100 - diff * 2, 1))

# Save session data
def save_session(data):
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            sessions = json.load(f)
    else:
        sessions = []

    sessions.append(data)
    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f, indent=2)

# Load saved sessions
def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return []

# Main Streamlit app
def main():
    st.set_page_config(page_title="Wedge Practice", layout="centered")
    st.title("🏌️‍♂️ Wedge Practice App")

    # First-time setup
    if "targets" not in st.session_state:
        st.session_state.targets = generate_targets()
        st.session_state.actuals = [None] * NUM_HOLES
        st.session_state.current_hole = 0
        st.session_state.complete = False

    hole = st.session_state.current_hole
    target = st.session_state.targets[hole]

    if not st.session_state.complete:
        st.markdown(f"### Hole {hole + 1} of {NUM_HOLES}")
        st.markdown(f"🎯 **Target Distance:** `{target}` yards")

        actual = st.number_input("How far did you hit it?", 0.0, 200.0, step=0.5, key=f"input_{hole}")
        st.session_state.actuals[hole] = actual

        col1, col2 = st.columns(2)
        if hole > 0:
            if col1.button("⬅️ Back"):
                st.session_state.current_hole -= 1
        if hole < NUM_HOLES - 1:
            if col2.button("➡️ Next"):
                st.session_state.current_hole += 1
        else:
            if col2.button("✅ Finish"):
                st.session_state.complete = True
                st.rerun()
    else:
        # Scoring
        scores = [
            calculate_score(t, a) for t, a in zip(st.session_state.targets, st.session_state.actuals)
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

        st.success(f"🎉 Session complete! Total Score: **{total_score} / 1800**")
        st.subheader("📋 Shot Summary")

        for i in range(NUM_HOLES):
            st.write(f"Hole {i+1}: Target {st.session_state.targets[i]} | "
                     f"Hit {st.session_state.actuals[i]} | "
                     f"Score: {scores[i]}")

        # Reset app state button
        if st.button("🆕 Start New Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Show session history
    st.markdown("---")
    st.subheader("📊 Session History")
    sessions = load_sessions()

    if sessions:
        df = pd.DataFrame(sessions)
        st.dataframe(df[["date", "total_score"]].sort_values("total_score", ascending=False), use_container_width=True)

        # Yardage analysis
        st.subheader("📈 Yardage Accuracy Analysis")
        all_data = []
        for s in sessions:
            for t, a in zip(s["targets"], s["actuals"]):
                all_data.append({"yardage": t, "error": abs(t - a)})

        yardage_df = pd.DataFrame(all_data)
        yardage_stats = yardage_df.groupby("yardage").mean().reset_index()
        st.line_chart(yardage_stats.set_index("yardage"))

if __name__ == "__main__":
    main()
