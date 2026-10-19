# Doctoome – Data Case Study (type 2 diabetes questionnaire)

*English version of `README.md`. The scripts, comments and presentation are in French; I am happy to walk through them in English.*

## 1. Context (brief)

Doctoome launched a landing page for a type 2 diabetes awareness questionnaire (5 questions).
Visitors arrive through several channels, then leave, start or complete the questionnaire.
Each completed questionnaire receives an analytical category "according to this questionnaire":
`no_current_indication`, `possible_risk` or `declared_diagnosed`.

The data (6 Parquet tables: 26,000 sessions, 20,000 visitors, June–August 2026) are **synthetic**.
The questionnaire is **fictional, simplified and not medically validated**: I draw no medical conclusion from it.
The brief is deliberately open: it asks to choose and justify one's priorities.

**My framing (assumption):** I assumed that the goal of such a page is to turn visitors into users.
This goal comes from Doctoome's public website, not from the data: no event after the result is available.

**Main findings:**
1. **The summer traffic growth comes from returning visitors.** Sessions from new visitors are flat
   (9,572 in June, 9,875 in July); sessions from returning visitors grow almost fivefold (996 then 4,878).
2. **The questionnaire loses the most people at Q4** (13.5% drop-off, versus 2–6% for the other questions),
   especially on mobile (16.9% versus 8.0% on desktop).
3. **The classification rule is very lenient**: a single warning answer leads to "no current indication".

## 1b. Prioritisation

| Area studied | Why |
|---|---|
| Funnel by question and device | The only place where Doctoome can act directly |
| Acquisition sources, by volume **and** quality, at equal age | Know where to invest without being misled by age or device |
| Data quality | Every conclusion depends on it (visitor definition, observation window, name variants) |
| Consistency of answers → categories | Check that the result reflects the answers |
| Linguistic analysis of the questions | The questionnaire is the only text in the data |

Discarded after testing: gender, day, hour, region, campaigns (no solid effect, see §7).

## 2. Reproducing the analysis

Requirements: Python 3.10 or later. Put the six original `.parquet` files in `data/`
(the raw data is **not published** in this repository, as a precaution).

```bash
pip install -r requirements.txt
python scripts/01_explorer.py              # quality checks (display only)
python scripts/02_nettoyer.py              # cleaning -> creates data_clean/
python scripts/03_analyses_sql.py          # runs all sql/*.sql -> outputs/*.csv
python scripts/04_graphiques.py            # charts -> outputs/graph*.png
python scripts/05_analyse_linguistique.py  # NLP analysis of the questions -> outputs/*.csv
python scripts/06_tests_significativite.py # chi-square tests -> outputs/06_tests_significativite.csv
```

Run the scripts **in this order**, from the project folder. Paths are relative.
Dependencies: `pandas`, `pyarrow`, `duckdb`, `matplotlib`, `scipy`.

## 3. Folder structure

```
doctoome_case/
├── data/            original data (never modified, not published)
├── data_clean/      cleaned tables (created by 02, not published)
├── scripts/         01 to 06 (Python)
├── sql/             01 to 14 (DuckDB queries on the Parquet files)
├── outputs/         results: CSV files and PNG charts
├── presentation/    slides for the executive team (PDF)
├── requirements.txt
├── README.md        French version
└── README_EN.md     this file
```

Note: in `outputs/`, the prefixes **06, 07 and 08 each appear twice**, because the SQL queries (03)
and scripts 05 and 06 number their own files. They are different results.

## 4. Data quality and transformations

Principle: **delete almost nothing; correct and flag** (`flag_` columns).

| Issue | Decision |
|---|---|
| Gender: `F`, `Female`, `female` | Harmonised (lower case, abbreviations expanded); missing becomes `unknown` |
| Regions: accents, hyphens, capitals | Simplified key, then the most frequent spelling is kept |
| Sources: `Google`/`google`, `ChatGPT`/`chatgpt`/`AI Assistant`, `facebook`/`instagram` | Grouped into `google_organic`, `ai_assistant`, `social` |
| Age | 2026 − birth year; `flag_mineur` (minor); `flag_annee_suspecte` (peaks in 1946 and 2008) |
| `direct` with a campaign name (219 sessions) | `flag_direct_avec_campagne` (inconsistency) |
| Times in UTC | Converted to Paris time; weeks start on Monday |
| Data stops on 2 August at 16:44 UTC (679 sessions on 1–2 August) | `flag_periode_incomplete`; excluded from trends |
| Answers changed within a session | The **last** one is kept: the rule then reproduces **100%** of the official results |
| 5 answers but no result (105 sessions) | `flag_5rep_sans_resultat` (tracking anomaly) |
| `questionnaire_start` with no Q1 view and no answer (893 of 16,774, i.e. 5.3%) | Kept and flagged in `sql/14`; sensitive comparisons are tested with both definitions of "start" |
| `first_seen_at` | Equal to the first observed session for all 20,000 visitors (`sql/14`): no history before June |

## 5. Hypotheses

| Hypothesis | Status | Evidence |
|---|---|---|
| `Google`/`google` = organic search | Supported | 100% of `google_ads` have a campaign, 0% of `google`; same profile as `google_organic` |
| `is_returning_visitor` depends on the observation window | **Confirmed** | `first_seen_at` = first session for 20,000 of 20,000 visitors: the share of returning visitors rises by construction (`sql/13`, `sql/14`) |
| A visitor is not a person | Supported | The same visitor answers both "yes" and "no" to permanent facts (see §6) |
| Q5 is ambiguous (scope of "without") | Supported | 319 of the 1,252 diagnosed people answer "yes" to Q5 |
| Q4 drop-off comes from its format on mobile | Supported | Mobile drop-off ≈ 2× desktop, only at Q4 |
| Q4 drop-off also comes from low perceived relevance ("what does this have to do with diabetes?") | **Not proven** | Only lifestyle question; no drop-off reason in the data |
| "Social" visits are partly accidental clicks | Partly supported | 48.6% do not start; 88% on mobile |
| Visitors coming from an AI assistant are more engaged | Partly supported | They start much more often (+11 pts); the gap for finishing is small and fragile (see §7) |
| Connection problems by region | **Rejected** | No regional effect (see §7) |
| Questions in English | Explained by the brief | Fictional, simplified questions for the exercise |

## 6. Key results (with the source of each figure)

1. **New visitors are not growing.** New-visitor sessions: 9,572 in June, 9,875 in July.
   Returning-visitor sessions: 996 then 4,878. The share of new visitors drops from 90.6% to 66.9% **by construction of the metric**
   (`first_seen_at` = first session for everyone). Overall completion rises from 39.9% (week of 1 June) to 47.1% (week of 20 July),
   while new-visitor completion stays between 38.8% and 42.1%. Source: `sql/05`, `sql/13`, `sql/14`, `graph5`.
2. **Funnel.** Out of 26,000 sessions, 35.5% leave before starting and 43.7% complete. Q4 is where the most people are lost:
   13.5% (Q1 2.0%, Q2 5.0%, Q3 5.8%, Q5 4.8%). Mobile 16.9%, desktop 8.0%, tablet 8.2%.
   Median time: 21.0 s at Q4 versus 13.4–13.6 s for the others. Source: `sql/01`, `sql/02`, `outputs/07_linguistique_questions.csv`, `graph1`, `graph2`.
3. **"Rarely or never" at Q4 increases with age**: 14.7% among 18–24 year-olds, 36.7% among those aged 65+.
   This answer adds a risk point, so it weighs more on older people's results. Source: `sql/12`.
4. **The classification rule is very lenient.** Reconstructed rule (it reproduces 100% of the results): Q1 = yes gives
   "diagnosed"; otherwise 1 point per risk answer (Q2, Q3, Q4 "rarely or never", Q5), and 2 points or more
   give "possible risk". A single warning answer therefore gives "no current indication": Q5 = yes without diagnosis,
   1,857 sessions of which 730 (39.3%); Q2 = yes, 2,007 sessions of which 797 (39.7%). "Not sure" and "prefer not to say"
   count as "no". Source: `sql/10`, `05_analyse_linguistique.py`.
5. **Sources.** AI assistants lead to more starts: 74.7% versus 63.3% for organic Google. Among those who start,
   the gap for finishing is small (70.8% versus 68.2%, see §7). At equal age, AI keeps a better completion rate
   (50.8–55.6% versus 42.7–44.9%). Social networks: 48.6% do not start, 88% on mobile. Median age: social 36,
   AI 37, organic Google 44, Google Ads 52. E-mail has the best completion (64.7%) but brings only 22.8% new
   visitors: good quality, little acquisition. Source: `sql/03`, `sql/07`, `sql/08`, `sql/09`, `sql/11`, `graph6`, `graph7`.
6. **Visitor ≠ person.** For a permanent fact ("have you ever been…"), the same visitor answers both yes and no:
   Q1 20.3%, Q3 40.5%, Q5 28.2%. Among the 1,503 visitors who took the questionnaire several times,
   678 got a different result. Source: `outputs/08_coherence_visiteurs.csv`, `sql/06`.
7. **The categories lead to no measurable next step.** The data stops at the result: we cannot know whether the
   visitor signs up or books a consultation. The proposed main KPI (result → sign-up) requires collecting new
   events (see §9).

## 7. Significance tests (chi-square test)

Threshold: p < 0.05. A gap is considered "solid" only if p < 0.01. Script: `06_tests_significativite.py`.

| Comparison | p-value | Reading |
|---|---|---|
| Q4 drop-off: mobile / desktop / tablet | < 0.0001 | **Real.** 95% confidence intervals: mobile [16.0; 17.6], desktop [7.2; 8.7] |
| "Rarely or never" (Q4) by age | < 0.0001 | **Real** |
| Start and completion by source | < 0.0001 | **Real** |
| Start: AI / organic Google | < 0.0001 | **Real** (74.7% / 63.3%) |
| Finishing (among starters): AI / organic Google | 0.039 (0.073 if "start" = Q1 viewed) | **Fragile**: depends on the definition |
| Google Ads campaigns | 0.026 (0.13 if "start" = Q1 viewed) | **Fragile**: not retained |
| Q4 drop-off by region | 0.19 (0.62 on mobile) | **Rejected** |
| Gender, day of the week, hour | 0.11 to 0.82 | **Rejected** |

Leads tested and discarded: region/connection, Ads campaigns, gender, day and hour.

## 8. Linguistic analysis (NLP)

`05_analyse_linguistique.py` links the **form** of the questions to **behaviour**: length, temporality
("ever" = permanent fact, "usually" = habit), negation, two ideas in one question, threshold to calculate
("at least 30 minutes"). Q4 is the only one combining a habit, a threshold to calculate and long answers
(19.5 characters on average, versus 4–7 elsewhere): it is also the most abandoned and the slowest.
Q5 contains a negation ("without") whose scope is ambiguous. Q2 and Q3 ask about two ideas at once.
The per-visitor consistency check (§6, point 6) confirms that permanent facts are not stable from one visit to the next.
Suggested rewordings follow patient-friendly language: short questions, yes/no answers, examples.

## 9. Answers to the four questions

**1. Key findings**: see §6.

**2. Unanswered questions**
- Why do people drop off at Q4: format, perceived relevance, or discomfort answering?
- What do people do after the result? (no data)
- Does AI bring more motivated visitors, or does it guide them better?
- Are "social" visits accidental clicks?
- How many real people are behind the visitor IDs?

**3. Data to collect**
- Post-result events: click to a practitioner, account creation, appointment
- Drop-off reason (short exit question)
- Loading time and technical errors by device
- Account ID (to deduplicate visitors)
- Cost per campaign; questionnaire version (for A/B tests)
- History before June (to define "new" and "returning" correctly)

**4. What to monitor over 12 months**
- **Main KPI: result → sign-up or appointment**
- Start rate by source
- Drop-off by question and device (Q4 on mobile first)
- Number of **new** visitors per month, on a fixed window
- Share of warning answers classified "no current indication"
- Share of starts without a Q1 view (tracking reliability)
- Cost per sign-up by source; A/B tests on Q4 and Q5

## 10. Limitations

- The data is synthetic (brief): its regularity probably comes from the generation process (only 9 regions,
  2,700–2,900 sessions each, Île-de-France like the others; 1,000–1,100 sessions per hour,
  including at night). I draw no conclusion about real-world behaviour.
- The announced period is June–August, but the data stops on 2 August.
- The analysis is descriptive: it does not prove causality.
- Several tests were run without correction: a result close to 0.05 remains to be confirmed, and two conclusions
  depend on the definition of "start" (see §7).
- If the data were real, it would be health data (GDPR), with minors flagged.

## 11. Use of AI

I used an AI assistant (Claude) to structure the analysis, write code (Python and SQL) and check calculations.
I ran every script myself and verified that the analysis reproduces. I am working through each step
so that I can explain and modify the work submitted.
