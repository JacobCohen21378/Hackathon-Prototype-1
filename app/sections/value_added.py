"""Tab: overperformers -- schools that beat the model's prediction."""

import pandas as pd
import streamlit as st

import config

TARGETS = {
    "Graduation rate": "grad_rate",
    "Earnings 10 years out": "earnings_10yr",
}


@st.cache_data
def load_model_scores():
    path = config.DATA_DIR / "model_scores.csv"
    return pd.read_csv(path) if path.exists() else None


def model_scores_table():
    scores = load_model_scores()
    if scores is None:
        return
    st.markdown("**How accurate is the model?** (tested on 20% of schools it never saw)")
    scores = scores.replace({"grad_rate": "Graduation rate", "earnings_10yr": "Earnings",
                             "linear": "Linear regression", "forest": "Random forest"})
    st.dataframe(
        scores[["target", "model", "r2", "mae"]],
        column_config={
            "target": "Predicting", "model": "Model",
            "r2": st.column_config.NumberColumn("R²", format="%.2f"),
            "mae": st.column_config.NumberColumn("Mean abs. error", format="%.3f"),
        },
        hide_index=True,
    )
    st.caption("R² = share of the differences between schools the model explains (1.0 = all). "
               "Grad-rate error is a fraction (0.07 = 7 points); earnings error is in dollars.")


def render(df):
    st.subheader("Hidden gems: colleges that beat the odds")
    st.write(
        "Some colleges do way better than you'd expect. We used a machine-learning model "
        "(a random forest) to predict each school's results from **who it enrolls** "
        "(% low-income, % first-gen, SAT, admit rate) and **how much money it has**. "
        "The schools below beat that prediction by the most, so they're doing something right."
    )
    choice = st.radio("Beat the odds on...", list(TARGETS), horizontal=True)
    target = TARGETS[choice]
    col = f"residual_{target}"

    t = df.sort_values(col, ascending=False).head(25).copy()
    is_rate = target == "grad_rate"
    scale = 100 if is_rate else 1  # show rates as percent
    for c in [target, f"predicted_{target}", col]:
        t[c] = t[c] * scale
    fmt = "%.0f%%" if is_rate else "localized"
    st.dataframe(
        t[["name", "state", "control_label", "pct_pell", target, f"predicted_{target}", col]]
        .assign(pct_pell=t["pct_pell"] * 100),
        column_config={
            "name": st.column_config.TextColumn("School", width="large"),
            "state": "State", "control_label": "Type",
            "pct_pell": st.column_config.NumberColumn("% Pell", format="%.0f%%"),
            target: st.column_config.NumberColumn("Actual", format=fmt),
            f"predicted_{target}": st.column_config.NumberColumn("Predicted", format=fmt),
            col: st.column_config.NumberColumn("Beat prediction by", format=fmt),
        },
        hide_index=True, width="stretch", height=500,
    )
    model_scores_table()
