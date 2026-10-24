"""Tab: the student's top matches as cards, with plain-language reasons."""

import pandas as pd
import streamlit as st

import scoring

MEDALS = ["🥇", "🥈", "🥉"]
# A school counts as a "hidden gem" if it ranks this many spots higher than on prestige
GEM_JUMP = 100


def money(x):
    return "no data" if pd.isna(x) else f"${x:,.0f}"


def percent(x):
    return "no data" if pd.isna(x) else f"{x:.0%}"


def why_line(pct_row, weights):
    """E.g. '💸 beats 91% of colleges on price · 🎓 ...' for the criteria they care about."""
    parts = []
    for key in scoring.strengths(pct_row, weights):
        _, _, label, short = scoring.CRITERIA[key]
        parts.append(f"{label.split()[0]} beats **{pct_row[key]:.0%}** of colleges on {short}")
    return " · ".join(parts)


def card(row, pct_row, weights, medal):
    with st.container(border=True):
        st.markdown(f"### {medal} {row['name']}")
        st.caption(f"{row['state']} · {row['control_label']} · {row['undergrads']:,.0f} undergrads")
        st.progress(int(row["score"]), text=f"Match score: **{row['score']:.0f} / 100**")
        if row["change"] >= GEM_JUMP:
            st.success(f"💎 **Hidden gem:** #{row['your_rank']} for you, "
                       f"but #{row['prestige_rank']} on a prestige-only list")
        st.markdown(f"**Why it's here:** {why_line(pct_row, weights)}")
        st.markdown(
            f"- 💸 **{money(row['net_price'])}** a year after aid (average)\n"
            f"- 🎓 **{percent(row['grad_rate'])}** of students graduate\n"
            f"- 🚀 **{money(row['earnings_10yr'])}** typical salary 10 years later\n"
            f"- 🧾 **{money(row['median_debt'])}** typical debt at graduation"
        )


def render(table, pcts, weights):
    st.subheader("Your top matches")
    if sum(weights.values()) == 0:
        st.info("👈 Tell us what matters to you in the sidebar to see your matches.")
        return

    st.write(f"Out of **{len(table):,}** colleges that fit your filters, these fit your "
             "priorities best. Change anything in the sidebar and watch the list change.")
    top = table.head(3)
    for col, (idx, row), medal in zip(st.columns(len(top)), top.iterrows(), MEDALS):
        with col:
            card(row, pcts.loc[idx], weights, medal)

    rest = table.iloc[3:10]
    if not rest.empty:
        st.markdown("#### Also worth a look")
        for _, row in rest.iterrows():
            gem = " 💎" if row["change"] >= GEM_JUMP else ""
            st.markdown(f"**#{row['your_rank']}  {row['name']}**{gem} · {row['state']} · "
                        f"score {row['score']:.0f} · {money(row['net_price'])}/yr after aid")
    st.caption("💎 = hidden gem: ranks way higher on what you care about than on prestige. "
               "See the full list, or look up any school's report card, in the other tabs.")
