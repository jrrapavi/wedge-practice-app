import streamlit as st
import random
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np

# Constants
YARDAGE_MIN = 40
YARDAGE_MAX = 140
SESSION_FILE = "sessions.json"

starting_yardages = list(range(40, 155, 5))
starting_values = [2.6, 2.62, 2.65, 2.67, 2.69, 2.7, 2.72, 2.73, 2.73, 2.75, 2.76,
                   2.77, 2.78, 2.79, 2.81, 2.82, 2.83, 2.85, 2.86, 2.87, 2.89, 2.91, 2.93]

ending_yardages = list(range(0, 16))
ending_values = [1, 1.04, 1.34, 1.56, 1.7, 1.78, 1.84, 1.89, 1.92, 1.95, 1.98, 2.0,
                 2.02, 2.05, 2.08, 2.1]

def get_starting_shot_value(yardage):
    return float(np.interp(yardage, starting_yardages, starting_values))

def get_ending_shot_value(yardage):
    return float(np.interp(yardage, ending_yardages, ending_values))

def calculate_score(start_yardage, actual_yardage):
    end_diff = abs(start_yardage - actual_yardage)
    start_val = get_starting_shot_value(start_yardage)
    end_val = get_ending_shot_value(end_diff)
    return round(start_val - end_val - 1, 2)

def generate_targets(num_holes):
    return [random.randint(YARDAGE_MIN, YARDAGE_MAX) for _ in range(num_holes)]

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

def main():
    st.set_page_config(page_title="Wedge Practice", layout="centered")
    st.title("🏌️ Wedge Practice")

    # 🛡️ Safe session state setup
    if "num_holes" not in st.session_state:
        st.markdown("### ⛳ Select Number of Holes")
        st.session_state.num_holes = st.radio("How many holes would you like to play?", [9, 18])
        if st.button("Start Session"):
            num_holes = st.session_state.num_holes
            st.session_state.targets = generate_targets(num_holes)
            for i in range(num_holes):
                st.session_state[f"hole_input_{i}"] = st.session_state.targets[i]
            st.session_state.complete = False
            st.experimental_rerun()
        return

    # Safe default
    if "complete" not in st.session_state:
        st.session_state.complete = False

    if "targets" not in st.session_state:
        return  # Don't proceed until session is fully initialized

    num_holes = st.session_state.num_holes

    if not st.session_state.complete:
        st.markdown("### 🎯 Enter your distances:")

        for hole in range(num_holes):
            target = st.session_state.targets[hole]
            key = f"hole_input_{hole}"

            st.markdown(f"<p style='font-size:18px;'>Hole {hole+1}: <b>{target} yards</b></p>", unsafe_allow_html=True)

            st.number_input(
                label="Your Shot:",
                min_value=0,
                max_value=200,
                step=1,
                value=st.session_state[key],
                key=key
            )
            st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("✅ Finish Session", use_container_width=True):
            all_valid = all(
                isinstance(st.session_state[f"hole_input_{i}"], int) and 0 <= st.session_state[f"hole_input_{i}"] <= 200
                for i in range(num_holes)
            )
            if all_valid:
                st.session_state.complete = True
                st.experimental_rerun()
            else:
                st.warning("⚠️ Please enter values between 0 and 200 for all holes.")

    else:
        targets = st.session_state.targets
        actuals = [st.session_state[f"hole_input_{i}"] for i in range(num_holes)]
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

        st.success(f"🏁 Session Complete! Total Score: **{total_score}**")
        st.markdown("### 📝 Shot Summary")

        for i in range(num_holes):
            t = targets[i]
            a = actuals[i]
            s = scores[i]
            if a == 0:
                st.write(f"Hole {i+1}: Target {t} | Skipped ❌")
            else:
                st.write(f"Hole {i+1}: Target {t} | You hit: {a} | Score: {s}")

        df = pd.DataFrame({
            "Hole": list(range(1, num_holes + 1)),
            "Target Yardage": targets,
            "Actual Yardage": [a if a != 0 else "" for a in actuals],
            "Score": [s if s is not None else "" for s in scores]
        })
        df.loc[len(df)] = ["TOTAL", "", "", total_score]

        st.download_button(
            "⬇️ Download Session CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"wedge_session_{date_str.replace(' ', '_').replace(':', '-')}.csv",
            mime="text/csv"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔁 Start New Session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()

    # Session history
    with st.expander("📊 View Past Sessions & Performance"):
        sessions = load_sessions()
        if sessions:
            history_df = pd.DataFrame(sessions)
            st.dataframe(history_df[["date", "total_score"]].sort_values("total_score", ascending=False), use_container_width=True)

            st.markdown("### 📈 Yardage Error Trend")
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
                st.info("No valid data points yet.")
        else:
            st.info("No session history available yet.")

if __name__ == "__main__":
    main()
