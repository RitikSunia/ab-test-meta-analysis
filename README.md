# A/B Test Meta-Analysis Engine

A strategic analysis of 100 simulated A/B experiments from a media/content platform, designed to audit an organization's experimentation program and surface systemic issues.

## Context

Simulates a streaming + news media company running experiments across Growth, Engagement, Monetization, and Content Algorithm teams over 6 quarters (2023-Q1 to 2024-Q2).

## Key Questions Answered

1. **False Discovery Rate** — How many shipped "winners" likely had no real effect?
2. **Power Audit** — Are we systematically running underpowered tests?
3. **Peeking Detection** — Is there evidence of early stopping or p-hacking?
4. **Revenue Impact** — How much revenue was left on the table from bad practices?
5. **Category Patterns** — Which experiment types consistently win or lose?

## Project Structure

```
AB-Test-Meta-Analysis/
├── data/
│   ├── generate_experiments.py   # Simulation script
│   └── experiments.csv           # Generated dataset (100 experiments)
├── analysis/
│   ├── utils.py                  # Shared statistical functions
│   ├── 01_false_discovery.py     # FDR analysis
│   ├── 02_power_audit.py         # Power analysis
│   ├── 03_peeking_detection.py   # P-hacking detection
│   ├── 04_revenue_impact.py      # Revenue opportunity cost
│   └── 05_category_analysis.py   # Win rates + learning curve
├── exports/                      # Power BI ready datasets (31 CSV files)
├── report/
│   ├── findings.md               # Written findings report (portfolio narrative)
│   └── power_bi_dashboard_guide.md  # Step-by-step Power BI build guide
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
python data/generate_experiments.py
```

## Run All Analyses

```bash
cd analysis
python run_all.py
```

This regenerates all 31 export files in `exports/`.

## Deliverables

| File | Purpose |
|---|---|
| `report/AB_Test_Meta_Analysis_Interview_Guide.pdf` | Interview prep guide (objectives, findings, Q&A) |
| `report/findings.md` | Full written findings report |
| `report/power_bi_dashboard_guide.md` | Step-by-step Power BI build guide |
| `exports/` | 31 Power BI-ready CSV files |

## Upload to GitHub

See [GITHUB_SETUP.md](GITHUB_SETUP.md) for push instructions.
