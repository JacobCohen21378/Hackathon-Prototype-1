"""
Scoring math for the app (no Streamlit code in here, so it's easy to test).

How a school's score works:
  1. For each criterion, turn the raw number into a percentile (0 to 1):
     0.9 means the school beats 90% of schools on that criterion.
  2. Multiply each percentile by the weight the user chose.
  3. Divide by the total weight and scale to 0-100.
"""

import numpy as np
import pandas as pd

# key -> (column in results.csv, True if higher is better, label for the UI, short name)
CRITERIA = {
    "affordability": ("net_price", False, "💸 Low price after financial aid", "price"),
    "earnings": ("earnings_10yr", True, "🚀 High salary after college", "salary"),
    "graduation": ("grad_rate", True, "🎓 Students actually graduate", "graduation rate"),
    "low_debt": ("median_debt", False, "🧾 Leave with less debt", "debt"),
    "mobility": ("pell_grad_rate", True, "🌱 Low-income students succeed too", "low-income grad rate"),
    "prestige": ("prestige_score", True, "🏛️ Big-name reputation", "reputation"),
}

# What each criterion means, shown as a (?) tooltip next to its control
HELP = {
    "affordability": "What families actually pay per year after grants and scholarships, not the sticker price.",
    "earnings": "Typical (median) salary of former students 10 years after they started college.",
    "graduation": "Share of students who finish a degree within 6 years.",
    "low_debt": "Typical amount of student loans owed when students graduate.",
    "mobility": "Graduation rate for students with Pell grants (from lower-income families).",
    "prestige": "How selective and wealthy the school is: admit rate, SAT scores, faculty pay, spending.",
}

# How much a criterion matters, from the user's point of view -> weight
LEVELS = {0: "Don't care", 2: "A little", 5: "Matters", 8: "A lot", 10: "Must have"}

# Starting points for the weights (every value must be a key of LEVELS)
PRESETS = {
    "⚖️ A bit of everything": {"affordability": 5, "earnings": 5, "graduation": 5,
                               "low_debt": 5, "mobility": 5, "prestige": 2},
    "💸 Graduate without drowning in debt": {"affordability": 10, "earnings": 2, "graduation": 5,
                                            "low_debt": 10, "mobility": 2, "prestige": 0},
    "🚀 Get the best-paying career": {"affordability": 2, "earnings": 10, "graduation": 5,
                                     "low_debt": 2, "mobility": 0, "prestige": 2},
    "🌱 First in my family to go to college": {"affordability": 8, "earnings": 5, "graduation": 8,
                                              "low_debt": 5, "mobility": 10, "prestige": 0},
    "🏛️ Only the big names (like most rankings)": {"affordability": 0, "earnings": 0, "graduation": 0,
                                                   "low_debt": 0, "mobility": 0, "prestige": 10},
}


def percentiles(df):
    """One column per criterion, each 0-1. Missing values get 0.5 (neutral)."""
    out = pd.DataFrame(index=df.index)
    for key, (col, higher_is_better, _, _) in CRITERIA.items():
        out[key] = df[col].rank(pct=True, ascending=higher_is_better).fillna(0.5)
    return out


def weighted_score(pcts, weights):
    """Weighted average of the percentiles, scaled to 0-100."""
    w = pd.Series(weights)[pcts.columns]
    if w.sum() == 0:
        return pd.Series(0.0, index=pcts.index)
    return pcts.mul(w).sum(axis=1) / w.sum() * 100


def fragility(pcts, weights, n_runs=500, wiggle=0.2, top_n=20, seed=0):
    """Monte Carlo check: do small weight changes reshuffle the top of the list?

    In each run, every weight is multiplied by a random number between
    (1 - wiggle) and (1 + wiggle), e.g. 0.8 to 1.2 for wiggle=0.2.
    Weights set to 0 stay 0.

    Returns:
      summary  - per school: how often it lands in the top N, and its
                 typical best/worst rank (5th and 95th percentile)
      overlap  - per run: how many of the original top N are still top N
    """
    base = np.array([weights[key] for key in pcts.columns], dtype=float)
    if base.sum() == 0:
        return None, None

    rng = np.random.default_rng(seed)
    factors = rng.uniform(1 - wiggle, 1 + wiggle, size=(n_runs, len(base)))
    run_weights = base * factors                     # shape: runs x criteria

    scores = pcts.to_numpy() @ run_weights.T         # shape: schools x runs
    # rank 1 = highest score, computed separately for every run
    ranks = (-scores).argsort(axis=0).argsort(axis=0) + 1

    baseline = weighted_score(pcts, weights).rank(ascending=False, method="first")
    in_base_top = (baseline <= top_n).to_numpy()
    in_run_top = ranks <= top_n

    summary = pd.DataFrame({
        "baseline_rank": baseline.astype(int),
        "pct_runs_in_top": in_run_top.mean(axis=1) * 100,
        "best_rank": np.percentile(ranks, 5, axis=1).round().astype(int),
        "worst_rank": np.percentile(ranks, 95, axis=1).round().astype(int),
    }, index=pcts.index)
    overlap = in_run_top[in_base_top].sum(axis=0)    # one number per run
    return summary, overlap


def letter_grade(pct):
    """Turn a percentile (0-1) into a report-card grade, graded on a curve."""
    for cutoff, grade in [(0.95, "A+"), (0.85, "A"), (0.70, "B"), (0.50, "C"), (0.30, "D")]:
        if pct >= cutoff:
            return grade
    return "F"


def strengths(pct_row, weights, n=2):
    """The criteria that add the most to this school's score (percentile x weight)."""
    cared = [key for key in pct_row.index if weights[key] > 0]
    return sorted(cared, key=lambda key: pct_row[key] * weights[key], reverse=True)[:n]
