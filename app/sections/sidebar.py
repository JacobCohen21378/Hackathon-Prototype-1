"""Sidebar: what the student cares about, plus filters. Returns what they picked."""

import pandas as pd
import streamlit as st

import scoring

# Size buckets by number of undergrads: label -> (min, max)
SIZES = {
    "Small (under 5k)": (0, 5000),
    "Medium (5k-15k)": (5000, 15000),
    "Large (15k+)": (15000, float("inf")),
}
# Selectivity buckets by admit rate: label -> (min, max)
SELECTIVITY = {
    "Super selective (<20% get in)": (0, 0.2),
    "Selective (20-50%)": (0.2, 0.5),
    "Most applicants get in (50%+)": (0.5, 1.01),
}
MAX_BUDGET = 60000


def weight_sliders():
    """A goal picker plus one "how much do you care?" control per criterion."""
    st.sidebar.header("1. What matters to you?")
    preset = st.sidebar.selectbox("Pick a goal to start from", list(scoring.PRESETS))
    defaults = scoring.PRESETS[preset]
    st.sidebar.caption("Then fine-tune it:")

    weights = {}
    for key, (_, _, label, _) in scoring.CRITERIA.items():
        # Putting the preset in the key resets the controls when the preset changes
        weights[key] = st.sidebar.select_slider(
            label, options=list(scoring.LEVELS), value=defaults[key],
            format_func=scoring.LEVELS.get, help=scoring.HELP[key], key=f"{preset}-{key}",
        )
    return weights


def in_buckets(values, buckets, picked):
    """True where the value falls in any of the picked buckets."""
    keep = pd.Series(False, index=values.index)
    for name in picked:
        lo, hi = buckets[name]
        keep |= values.between(lo, hi, inclusive="left")
    return keep


def filters(df):
    """Optional filters. Returns the filtered table."""
    st.sidebar.header("2. Narrow it down")
    budget = st.sidebar.slider(
        "Max price per year after aid", 5000, MAX_BUDGET, MAX_BUDGET, step=2500, format="$%d",
        help="Average net price. What YOU pay depends on your family's income, so check "
             "each school's net price calculator.",
    )
    states = st.sidebar.multiselect("Where? (leave empty for anywhere)", sorted(df["state"].unique()))
    sizes = st.sidebar.pills("School size", list(SIZES), default=list(SIZES), selection_mode="multi")
    selectivity = st.sidebar.pills(
        "How hard to get in?", list(SELECTIVITY), default=list(SELECTIVITY), selection_mode="multi",
        help="Turn off \"Super selective\" to see great schools beyond the famous few.",
    )
    types = st.sidebar.pills(
        "Public or private?", sorted(df["control_label"].unique()),
        default=sorted(df["control_label"].unique()), selection_mode="multi",
    )

    keep = (df["control_label"].isin(types)
            & in_buckets(df["undergrads"], SIZES, sizes)
            # No admit rate usually means open admission, so count it as "most get in"
            & in_buckets(df["admit_rate"].fillna(1), SELECTIVITY, selectivity))
    if budget < MAX_BUDGET:
        keep &= df["net_price"] <= budget  # schools with no price data drop out here
    if states:
        keep &= df["state"].isin(states)
    return df[keep]
