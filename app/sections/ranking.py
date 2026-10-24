"""Tab: the live re-ranked table based on the user's weights."""

import streamlit as st

# How each column shows up in the table
COLUMNS = {
    "your_rank": st.column_config.NumberColumn("Your rank"),
    "prestige_rank": st.column_config.NumberColumn("Prestige rank"),
    "change": st.column_config.NumberColumn("vs. prestige", format="%+d",
                                             help="Prestige rank minus your rank. Positive = ranks higher on YOUR list."),
    "name": st.column_config.TextColumn("School", width="large"),
    "state": "State",
    "control_label": "Type",
    "score": st.column_config.ProgressColumn("Match score", min_value=0, max_value=100, format="%.0f"),
    "net_price": st.column_config.NumberColumn("Price/yr after aid ($)", format="localized"),
    "grad_pct": st.column_config.NumberColumn("Grad rate", format="%.0f%%"),
    "pell_grad_pct": st.column_config.NumberColumn("Low-income grad rate", format="%.0f%%"),
    "earnings_10yr": st.column_config.NumberColumn("Salary at 10 yrs ($)", format="localized"),
    "median_debt": st.column_config.NumberColumn("Typical debt ($)", format="localized"),
}


def build_table(df, scores):
    """Add rank columns and percent columns that are easy to read."""
    t = df.assign(score=scores)
    t["your_rank"] = t["score"].rank(ascending=False, method="first").astype(int)
    t["prestige_rank"] = t["prestige_score"].rank(ascending=False, method="first").astype(int)
    t["change"] = t["prestige_rank"] - t["your_rank"]
    t["grad_pct"] = t["grad_rate"] * 100
    t["pell_grad_pct"] = t["pell_grad_rate"] * 100
    return t.sort_values("your_rank")


def render(table):
    st.subheader("The full list")
    st.write(
        "Every college that fits your filters, ranked by what you said matters. "
        "**vs. prestige** shows how many spots a school moves compared with a list "
        "that only cares about reputation (like many famous rankings)."
    )
    n = st.slider("How many to show", 10, 200, 50, step=10)
    st.dataframe(
        table.head(n)[list(COLUMNS)], column_config=COLUMNS,
        hide_index=True, width="stretch", height=600,
    )
