"""Tab: letter-grade report cards for up to 3 schools, side by side."""

import pandas as pd
import streamlit as st

import scoring
from sections.matches import money, percent

# How to show the raw number behind each grade
RAW = {
    "affordability": lambda r: f"{money(r['net_price'])}/yr",
    "earnings": lambda r: f"{money(r['earnings_10yr'])} at 10 yrs",
    "graduation": lambda r: f"{percent(r['grad_rate'])} graduate",
    "low_debt": lambda r: f"{money(r['median_debt'])} debt",
    "mobility": lambda r: f"{percent(r['pell_grad_rate'])} of Pell students graduate",
    "prestige": lambda r: f"{r['prestige_score']:.0f} / 100 prestige",
}
GRADE_COLORS = {"A+": "green", "A": "green", "B": "blue", "C": "orange", "D": "red", "F": "red"}


def report_card(row, pct_row):
    with st.container(border=True):
        st.markdown(f"#### {row['name']}")
        st.caption(f"{row['state']} · {row['control_label']} · {row['undergrads']:,.0f} undergrads")
        if pd.notna(row.get("your_rank")):
            st.markdown(f"**#{row['your_rank']:.0f}** on your list · match score **{row['score']:.0f}**")
        else:
            st.markdown("_Hidden by your filters, so it's not on your list._")
        for key, (col, _, label, _) in scoring.CRITERIA.items():
            if pd.isna(row[col]):
                grade = "?"
            else:
                grade = scoring.letter_grade(pct_row[key])
            color = GRADE_COLORS.get(grade, "gray")
            st.markdown(f":{color}-background[**{grade}**] &nbsp; {label}")
            st.caption(RAW[key](row))


def render(all_schools, table, all_pcts):
    st.subheader("School report cards")
    st.write(
        "Look up any college (type to search) and compare up to 3. Grades are on a curve "
        f"against all {len(all_schools):,} colleges: **A+** = top 5%, **A** = top 15%, "
        "**B** = top 30%, **C** = top half, **D** and **F** = bottom half, **?** = no data."
    )
    names = all_schools["name"]
    picks = st.multiselect(
        "Schools to compare", names.sort_values().index, default=table.index[:2].tolist(),
        format_func=lambda i: f"{names[i]} ({all_schools.at[i, 'state']})", max_selections=3,
    )
    if not picks:
        return
    # Use the ranked table for schools on the list, so they show their rank and score
    rows = all_schools.loc[picks].join(table[["your_rank", "score"]])
    for col, (idx, row) in zip(st.columns(3), rows.iterrows()):
        with col:
            report_card(row, all_pcts.loc[idx])
