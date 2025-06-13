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

# Streamlit app
def main():
    st.set_page_config(page_title="Wedge Practice", layout="centered")
    st.title("🏌️ Wedge Practice App")

    # First-time session state setup
    if "targets" not in st.session_state:
        st.session_state.targets = generate_targets()
        st.session_state.actuals = [None] * NUM_HOLES
        st.session_state.current_hole = 0
        st.session_state.complete = False

    hole = st.session_state.current_hole
    target = st.session_state.targets[hole]

    # Hole-by-hole input UI
    if not st.session_state.complete:
        st.markdown(f"### Hole {hole + 1} of {NUM_HOLES}")
        st.markdown(f"🎯 **Target Distance:** `{target} yards`")

        # Default value setup
        current_value = st.session_state.actuals[hole]
        if current_value is None:
            current_value = 0

        actual = st.number_input(
            "How far did you hit it?",
            min_value=0,
            max_value=200,
            step=1,
            value=current_value,
            key=f"hole_input_{hole}"
        )
        st.session_state.actuals[hole] = actual

        # Navigation buttons
        col1, col2 = st.columns(2)
        if hole > 0:
            if col1.button("⬅️ Back"):
                st.session_state.current_hole -= 1
                st.rerun()

        if hole < NUM_HOLES - 1:
            if col2.button("➡️ Next"):
                st.session_state.current_hole += 1
                st.rerun()
        else:
            if col2.button("✅ Finish"):
                st.session_state.complete = True
                st.rerun()

    # Session complete — show summary and save
    else:
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

        st.success(f"🏆 Session complete! Total Score: **{total_score} / 1800**")
        st.subheader("📋 Shot Summary")
        for i in range(NUM_HOLES):
            st.write(f"Hole {i+1}: Target {st.session_state.targets[i]} | "
                     f"Hit {st.session_state.actuals[i]} | "
                     f"Score: {scores[i]}")

        # Download this session as CSV
        session_df = pd.DataFrame({
            "Hole": list(range(1, NUM_HOLES + 1)),
            "Target Yardage": st.session_state.targets,
            "Actual Yardage": st.session_state.actuals,
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

        # Restart session
        if st.button("🆕 Start New Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Show session history and performance analysis
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
                all_data.append({"yardage": t, "error": abs(t - a)})

        yardage_df = pd.DataFrame(all_data)
        yardage_stats = yardage_df.groupby("yardage").mean().reset_index()
        st.line_chart(yardage_stats.set_index("yardage"))

if __name__ == "__main__":
    main()
