# Rankings vs. Reality

**Do college rankings measure what's actually good for students?**
BU Spark! DS+X Hackathon, CollegeHack track.

We use the U.S. Department of Education's College Scorecard to find colleges that
deliver strong outcomes (graduation, earnings, low debt), especially for low-income
and first-generation students, and compare them with a prestige score built from
selectivity and wealth, which is what many rankings reward.

---

## How to run

You need Python 3.10+ and the College Scorecard download.

1. Put the unzipped Scorecard folder in this project so this file exists:
   `College_Scorecard_Raw_Data_10152026/Most-Recent-Cohorts-Institution.csv`
   (Download: https://collegescorecard.ed.gov/data/ → "All Data Files". If your
   folder has a different name, change `RAW_DIR` in `src/config.py`.)
2. Set up Python:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
   On Windows use `.venv\Scripts\pip` and `.venv\Scripts\python` instead.
3. Run the three phases:
   ```bash
   .venv/bin/python src/clean.py        # → data/clean_colleges.csv   (~5 s)
   .venv/bin/python src/analysis.py     # → data/results.csv + figures/  (~20 s)
   .venv/bin/streamlit run app/app.py   # opens the demo in your browser
   ```

Each phase only reads the CSV the previous one wrote, so once `data/results.csv`
exists you can work on the app without rerunning the models.

## Project layout

```
src/
  config.py          paths, column names, settings: everyone imports this
  clean.py           Phase 1: filter + clean the raw Scorecard file
  overperformers.py  Phase 2: models that predict outcomes; residuals
  prestige.py        Phase 2: prestige score, outcome score, optional rankings.csv
  plots.py           Phase 2: chart functions (also used by the app)
  analysis.py        Phase 2: runs everything, saves results + charts
app/
  app.py             Streamlit layout only
  scoring.py         weighted score + Monte Carlo fragility math
  sections/          one file per tab: matches (top-3 cards), ranking (full list),
                     report_card, map_view, value_added (hidden gems), scatter,
                     fragility, about; plus sidebar (priorities + filters)
data/                generated CSVs
figures/             generated charts (.png for slides, .html interactive)
```

## What we did

**Cleaning (`clean.py`).** Kept open public and private nonprofit colleges that
mainly award bachelor's degrees (`PREDDEG == 3`). Treated `NULL`, `PrivacySuppressed`,
`PS` and `NA` as missing. Dropped schools with no graduation rate or 10-year earnings,
and schools whose graduation rate comes from fewer than 100 students (some are
based on 1 student). Merged public/private net price into one column.
**Result: 1,405 colleges.**

**Overperformers (`overperformers.py`).** Predicted graduation rate and 10-year
earnings from inputs a college mostly doesn't control in the short run: % Pell,
% first-gen, admit rate, average SAT (+ a "not reported" flag), instructional
spending per student, and net price. Missing inputs were filled with the median
(fitted on training data only).

| Model (20% held-out test set) | Graduation rate R² / MAE | Earnings R² / MAE |
|---|---|---|
| Linear regression | 0.65 / 8.0 pts | 0.53 / $8,785 |
| Random forest | **0.72 / 7.2 pts** | **0.60 / $7,908** |

Residual = actual − predicted. Each school's prediction comes from 5-fold
cross-validation, so no school is judged by a model that trained on it.

**Prestige vs. outcomes (`prestige.py`).** Prestige score = average percentile of
admit rate (lower = more prestigious), SAT, faculty salary and spending. Outcome
score = average percentile of graduation rate, Pell graduation rate, earnings, low
debt and low net price.

**Key findings**
- Average SAT and % Pell are the strongest predictors of both outcomes: **who a
  college enrolls explains most of its results.**
- Prestige correlates with raw outcomes (Spearman 0.72 with graduation rate), but
  only **0.12** with graduation-rate *overperformance* and 0.13 with earnings
  overperformance. Prestige tells you who gets in, not how much a school adds.
- Top graduation overperformers include UC Riverside (+31 pts vs. predicted),
  Florida International, Rutgers-Newark, CSU Long Beach, Montclair State and San
  Diego State: public universities where 35-58% of students receive Pell grants.
- Boston University: prestige score 97, outcome score 76. Graduation rate exactly
  matches prediction (89.5%); earnings $4.4k below prediction.

**The app (`app/`).** Built for high school students. Pick a goal ("graduate without
debt", "first in my family"...), set how much each thing matters (Don't care → Must
have), and filter by budget, state, size and how hard it is to get in. All 1,405
schools re-rank live, compared with a prestige-only rank. Your top 3 show up as
cards that explain *why* they rank there, with plain-language stats and a 💎 badge
for hidden gems. A report-card tab grades any school A+ to F (on a curve) and
compares up to 3 side by side. A fragility check reruns the ranking 500 times with each weight
nudged ±20% and shows how much the top 20 reshuffles. The app also has a prestige
vs. outcomes scatter (BU highlighted, any school selectable), an overperformers
table, a US map, and a limitations page.

## Ethics & limitations

- **Earnings only cover federal financial aid recipients** who are working and not
  enrolled, and depend on majors and local job markets, not just the college.
  Arts and music schools look weak on earnings for this reason.
- **Correlation, not causation.** "Overperforming" means beating *our* 7-input
  model. Unmeasured factors (program mix, family wealth beyond Pell, motivation)
  matter.
- **Small schools are under-represented.** Privacy suppression hides values for
  small groups, and we drop tiny cohorts on purpose.
- **Graduation rates count first-time, full-time students only.**
- **A single score hides trade-offs.** Weights are value judgments; the fragility
  tab shows how much the answer depends on them.
- **Prestige is our proxy, not a real ranking.** We did not scrape U.S. News, QS or
  THE. `data/rankings.csv` is supported only if a librarian confirms we may use it.
- Faculty salary in the source data is monthly; SAT is missing for ~38% of schools
  (test-optional).

**Data:** U.S. Department of Education, College Scorecard, *Most Recent
Institution-Level Data* (downloaded October 2026). Public domain (U.S. government
work). Different measures come from different cohort years; see the Scorecard
technical documentation.

---

## Devpost draft

### Inspiration
Every fall, rankings tell families which colleges are "best." But many ranking
formulas reward how selective and wealthy a school is, which mostly measures who it
admits. As students, we wanted to know: which
colleges actually help their students graduate and earn a living without heavy debt,
especially students from low-income families?

### What it does
*Rankings vs. Reality* is an interactive Streamlit app built on federal College
Scorecard data for 1,405 four-year colleges. You choose what matters (affordability,
earnings, graduation, low debt, Pell-student graduation, prestige) and the list
re-ranks live, showing how far each school moves compared with a prestige-only
ranking. A fragility check reruns the ranking 500 times with slightly nudged weights
to show how arbitrary the top 20 can be. A machine-learning model finds
"overperformers": schools that graduate far more students, or produce higher
earnings, than expected given who they enroll and what they spend.

### How we built it
Python, pandas, scikit-learn, Plotly and Streamlit. We cleaned the 3,000+ column
Scorecard file down to 25 fields, handled privacy-suppressed values, and filtered
out graduation rates built on tiny cohorts. We trained linear regression and random
forest models (random forest: R² 0.72 for graduation rate, 0.60 for earnings on
held-out schools), used permutation importance to explain them, and used
cross-validated residuals to measure value added. The code is split into small
modules so five people could work in parallel.

### Challenges we ran into
- Some graduation rates were based on a single student, so our first "top
  overperformers" were tiny seminaries at 100%. We added a minimum cohort size.
- 38% of schools don't report SAT (test-optional). We kept them with a missing-value
  flag instead of dropping them.
- Missing data hides in several codes (`NULL`, `PrivacySuppressed`, `PS`).
- Choosing weights is a values question, not a math question, so we made that
  uncertainty visible instead of hiding it.

### Accomplishments that we're proud of
Finding that prestige barely predicts how much a school *adds* (correlation 0.12),
and surfacing public universities like UC Riverside, FIU and Rutgers-Newark that
graduate low-income students at rates 25-31 points above prediction.

### What we learned
How much of a college's outcomes are explained by its incoming students; why
held-out testing and cross-validated residuals matter; and that data
cleaning decisions (like a cohort-size cutoff) can change the story completely.

### What's next
- Add licensed ranking data (with library approval) to compare real ranks directly.
- Model Pell-student outcomes and earnings by field of study (Scorecard field-level
  data) to separate "good college" from "high-paying majors."
- Add uncertainty intervals to the overperformer estimates.
- Track trends over time using historical Scorecard files.
