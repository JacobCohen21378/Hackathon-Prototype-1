"""
Rankings vs. Reality -- Streamlit demo.

Run from the project folder (after src/clean.py and src/analysis.py):
    .venv/bin/streamlit run app/app.py

This file only does layout. Each tab lives in its own file in app/sections/.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Let the app import our shared code in src/ (config.py, plots.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import config  # noqa: E402
import scoring  # noqa: E402
from sections import (about, fragility, map_view, matches, ranking, report_card, scatter,  # noqa: E402
                      sidebar, value_added)

st.set_page_config(page_title="College Fit Finder", page_icon="🎓", layout="wide")


@st.cache_data
def load_results():
    return pd.read_csv(config.RESULTS_CSV)


def main():
    if not config.RESULTS_CSV.exists():
        st.error("data/results.csv not found. Run `src/clean.py` then `src/analysis.py` first.")
        st.stop()

    st.title("🎓 Find colleges that fit *you*")
    st.write(
        "Famous college rankings mostly reward how exclusive and rich a school is. "
        "But what about whether you'll graduate, what it costs, and whether it pays off? "
        "**Tell us what matters to you in the sidebar 👈** and get your own ranking of "
        "1,400+ U.S. colleges, built from real government data."
    )

    all_schools = load_results()
    weights = sidebar.weight_sliders()
    df = sidebar.filters(all_schools)
    if df.empty:
        st.warning("No colleges match these filters. Try a bigger budget or more states.")
        st.stop()

    # Percentiles use ALL schools, so filtering doesn't change a school's score
    all_pcts = scoring.percentiles(all_schools)
    pcts = all_pcts.loc[df.index]
    scores = scoring.weighted_score(pcts, weights)

    table = ranking.build_table(df, scores)

    tabs = st.tabs(["🏆 Your top matches", "📋 Full list", "📝 Report cards", "🗺️ Map",
                    "💎 Hidden gems", "📊 Fame vs. results", "🎲 How solid is this?", "ℹ️ About the data"])
    with tabs[0]:
        matches.render(table, pcts, weights)
    with tabs[1]:
        ranking.render(table)
    with tabs[2]:
        report_card.render(all_schools, table, all_pcts)
    with tabs[3]:
        map_view.render(table)
    with tabs[4]:
        value_added.render(df)
    with tabs[5]:
        scatter.render(df)
    with tabs[6]:
        fragility.render(df, pcts, weights)
    with tabs[7]:
        about.render()


main()
