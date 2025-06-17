import streamlit as st
import random
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np

# Constants
NUM_HOLES = 18
YARDAGE_MIN = 40
YARDAGE_MAX = 140
SESSION_FILE = "sessions.json"

# Shot value data for interpolation
starting_yardages = list(range(40, 155, 5))
starting_values = [2.6, 2.62, 2.65, 2.67, 2.69, 2.7, 2.72, 2.73, 2.73, 2.75, 2.76,
                   2.77, 2.78, 2.79, 2.81, 2.82, 2.83, 2.85, 2.86, 2.87, 2.89, 2.91, 2.93]

ending_yardages = list(range(0, 16))
ending_values = [1, 1.04, 1.34, 1.56, 1.7, 1.78, 1.84, 1.89, 1.92, 1.95, 1.98, 2.0,
                 2.02, 2.05, 2.08, 2.1]

# Interpolation
def get_starting_shot_value(yardage):
    return float(np.interp(yardage, starting_yardages, starting_values))

def get_ending_shot_value(yardage):
    return float(np.interp(yardage, ending_yardages, ending_values))

# Scoring
def calculate_score(start_yardage, actual_yardage):
    end_diff = abs(start_yardage - actual_yardage)
    start_val = get_starting_shot_value(start_yardage)
    end_val = get_ending_shot_value(end_diff)
    return round(start_val - end_val - 1, 2)

# Session utilities
def generate_targets():
    return [random.randint(YARDAGE_MIN, YARDAGE_MAX) for _ in range(NUM_HOLES)]

def save_session(data):
    sessions = []
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            sessions = json.load(f)
    sessions.append(data)
    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f, indent=2)

def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return []

# Main app
def main():
    st.set_page_config(page_title="Wedge Practice", layout="centered")
    st.title("🏌️ Wedge Practice")

    # Initialize session state
    if "targets" not in st.session_state:
        st.session_state.targets = generate_targets()
        for i in range(NUM_HOLES):
            st.session_state[f"hole_input_{i}"] = st.session_state.targets[i]
        st.session_state.complete = False

    if not st.session_state.complete:
        st.markdown("### Enter your shot yardages for each hole below:")

        for hole in range(NUM_HOLES):
            target = st.session_state.targets[hole]
            key = f"hole_input_{hole}"

            st.markdown(
                f"<p style='font-size:20px;'>Hole {hole+1} - Target: <b>{target}</b> yards. Your shot (yards):</p>",
                unsafe_allow_html=True
            )

            col1, col2 = st.columns([3, 1])
            with col1:
                st.number_input(
                    label="",
                    min_value=0,
                    max_value=200,
                    value=st.session_state[key],
                    step=1,
                    key=key
                )
            with col2:
                if st.button("Clear", key=f"clear_button_{hole}"):
                    st.session_state[key] = 0

        if st.button("✅ Finish Session"):
            all_valid = all(
                isinstance(st.session_state[f"hole_input_{i}"], int) and 0 <= st.session_state[f"hole_input_{i}"] <= 200
                for i in range(NUM_HOLES)
            )
            if all_valid:
                st.session_state.complete = True
            else:
                st.warning("Please enter valid distances (0-200) for all holes before finishing.")

    else:
        targets = st.session_state.targets
        actuals = [st.session_state[f"hole_input_{i}"] for i in range(NUM_HOLES)]
        scores = []
        filtered_targets, filtered_actuals = [], []

        for t, a in zip(targets, actuals):
            if a != 0:
                scores.append(calculate_score(t, a))
                filtered_targets.append(t)
                filtered_actuals.append(a)
            else:
                scores.append(None)
                filtered_targets.append(t)
                filtered_actuals.append(None)

        total_score = round(sum(s for s in scores if s is not None), 2)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        save_session({
            "date": date_str,
            "targets": filtered_targets,
            "actuals": filtered_actuals,
            "scores": [s for s in scores if s is not None],
            "total_score": total_score
        })

        st.success(f"🏆 Session complete! Total Score: **{total_score}**")
        st.subheader("📋 Shot Summary")

        for i in range(NUM_HOLES):
            t = targets[i]
            a = actuals[i]
            s = scores[i]
            if a == 0:
                st.write(f"Hole {i+1}: Target {t} | Hit: ❌ Skipped | Score: N/A")
            else:
                st.write(f"Hole {i+1}: Target {t} | Hit: {a} | Score: {s}")

        df = pd.DataFrame({
            "Hole": list(range(1, NUM_HOLES + 1)),
            "Target Yardage": targets,
            "Actual Yardage": [a if a != 0 else "" for a in actuals],
            "Score": [s if s is not None else "" for s in scores]
        })
        df.loc[len(df)] = ["TOTAL", "", "", total_score]

        st.download_button(
            label="⬇️ Download This Session as CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"wedge_session_{date_str.replace(' ', '_').replace(':', '-')}.csv",
            mime="text/csv"
        )

        if st.button("🆕 Start New Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]

    st.markdown("---")
    st.subheader("📊 Session History")

    sessions = load_sessions()
    if sessions:
        history_df = pd.DataFrame(sessions)
        st.dataframe(history_df[["date", "total_score"]].sort_values("total_score", ascending=False), use_container_width=True)

        st.subheader("📈 Yardage Error Analysis")
        all_data = []
        for session in sessions:
            for t, a in zip(session["targets"], session["actuals"]):
                if a is not None:
                    all_data.append({"yardage": t, "error": abs(t - a)})

        if all_data:
            yardage_df = pd.DataFrame(all_data)
            yardage_stats = yardage_df.groupby("yardage").mean().reset_index()
            st.line_chart(yardage_stats.set_index("yardage"))
        else:
            st.info("No valid data points available for error analysis.")

if __name__ == "__main__":
    main()
