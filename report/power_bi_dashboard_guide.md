# Power BI Dashboard Guide

This guide walks you through building a portfolio-ready dashboard from the exported CSV files in `exports/`.

---

## Before You Start

1. Install [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (free).
2. Re-run all analyses if needed:

```bash
cd "D:\EDUCATON\_\01 - Projects\AB-Test-Meta-Analysis\analysis"
python 01_false_discovery.py
python 02_power_audit.py
python 03_peeking_detection.py
python 04_revenue_impact.py
python 05_category_analysis.py
```

3. Confirm `exports/` contains 31 CSV files.

---

## Step 1: Create the Data Model

### 1.1 Load the main experiment table

1. Open Power BI Desktop → **Get Data** → **Text/CSV**
2. Load `data/experiments.csv`
3. In Power Query, set these data types:
   - `was_peeked` → True/False
   - `p_value`, `statistical_power`, `true_effect` → Decimal Number
   - `quarter` → Text (we'll sort manually)
   - `decision`, `team`, `feature_category` → Text

### 1.2 Load summary/export tables

Load these from `exports/`:

| Table | Purpose |
|---|---|
| `revenue_waterfall.csv` | Waterfall chart |
| `revenue_summary.csv` | Executive KPI cards |
| `maturity_summary.csv` | Maturity score card |
| `power_overall_summary.csv` | Power KPI cards |
| `org_learning_curve.csv` | Trend line charts |
| `category_win_rates.csv` | Category bar charts |
| `team_win_rates.csv` | Team comparison |
| `top_missed_opportunities.csv` | Priority table |
| `peeking_evidence_summary.csv` | Peeking signals table |
| `fdr_summary.csv` | FDR methods table |
| `business_assumptions.csv` | Assumptions reference |
| `category_recommendations.csv` | Action items table |

**Tip:** Use **Transform Data** → disable "Detect data types" for summary tables to avoid type errors.

### 1.3 Create relationships (optional but recommended)

For drill-down from summary to detail, relate on shared keys:

| From | To | Column |
|---|---|---|
| `experiments` | `revenue_opportunity_detail` | `experiment_id` |
| `experiments` | `missed_winners` | `experiment_id` |
| `experiments` | `peeking_detail` | `experiment_id` |
| `category_win_rates` | `experiments` | `feature_category` |
| `team_win_rates` | `experiments` | `team` |

Use **Many-to-one** relationships. Cross-filter direction: Single.

### 1.4 Create a Quarter sort order

In `experiments` and `org_learning_curve`, add a calculated column:

```dax
Quarter Sort =
SWITCH(
    [quarter],
    "2023-Q1", 1,
    "2023-Q2", 2,
    "2023-Q3", 3,
    "2023-Q4", 4,
    "2024-Q1", 5,
    "2024-Q2", 6,
    99
)
```

Sort `quarter` by `Quarter Sort`.

---

## Step 2: Build 5 Dashboard Pages

Design a dark or clean corporate theme. Suggested color palette:

- Captured / positive: `#2E7D32` (green)
- Loss / risk: `#C62828` (red)
- Neutral: `#546E7A` (blue-gray)
- Accent: `#1565C0` (blue)

---

### Page 1: Executive Overview

**Purpose:** One-screen story for hiring managers and stakeholders.

**KPI Cards (top row):**

| Card | Source | Field |
|---|---|---|
| Total Experiments | `experiments` | `COUNT(experiment_id)` |
| Ship Rate | `experiments` | `% shipped = DIVIDE(COUNTROWS(FILTER(experiments, decision="ship")), COUNTROWS(experiments))` |
| Median Power | `power_overall_summary` | `median_power` |
| Maturity Score | `maturity_summary` | `total_score` |
| Revenue Missed | `revenue_summary` | `total_missed_usd` |
| Capture Rate | `revenue_summary` | `capture_rate` |

Format revenue as `$#,##0` or `$0.0M`.

**Visuals:**

1. **Waterfall chart** — `revenue_waterfall`
   - Category: `category`
   - Y-axis: `amount_usd`
   - Color by `type` (total=captured=green, loss=red, potential=blue)

2. **Donut chart** — Decisions breakdown
   - Legend: `decision`
   - Values: Count of experiments

3. **Line chart** — Learning curve
   - Source: `org_learning_curve`
   - X: `quarter` (sorted)
   - Lines: `ship_rate`, `median_power`, `peeking_rate`

4. **Text box** — 3-line executive summary (copy from `findings.md`)

**Slicers:** `team`, `feature_category`, `quarter`

---

### Page 2: Power Audit

**Purpose:** Show the underpowering problem visually.

**KPI Cards:**

| Card | Source | Field |
|---|---|---|
| Median Power | `power_overall_summary` | `median_power` |
| % Underpowered (<50%) | `power_overall_summary` | `pct_underpowered_below_50` |
| % Adequately Powered | `power_overall_summary` | `pct_adequately_powered` |
| Missed Winners | `missed_winners` | Row count |

**Visuals:**

1. **Histogram** — Power distribution
   - Source: `experiments`
   - X: `statistical_power` (binned, 10 bins, 0–1)
   - Y: Count
   - Add reference line at 0.80

2. **Scatter plot** — Power vs Observed Lift
   - X: `statistical_power`
   - Y: `observed_lift_relative`
   - Legend: `decision`
   - Size: `actual_n_control`

3. **Clustered bar** — Power by team
   - Source: `power_by_team`
   - X: `team`
   - Y: `median_power`
   - Add constant line at 0.80

4. **Table** — Top missed winners
   - Source: `top_missed_opportunities` or `missed_winners`
   - Columns: experiment name, team, true effect, power, p-value, annual revenue

5. **Matrix** — Sample size lookup
   - Source: `sample_size_lookup_table`
   - Rows: `metric`, Columns: `mde_relative`, Values: `required_n_per_group`

---

### Page 3: False Discovery & Peeking

**Purpose:** Demonstrate statistical rigor and process quality awareness.

**Visuals:**

1. **Histogram** — P-value distribution
   - Source: `pvalue_distribution` or `experiments`
   - X: `p_value` (20 bins)
   - Add reference line at 0.05

2. **Table** — FDR methods comparison
   - Source: `fdr_summary`
   - Columns: method, fdr_estimate, interpretation

3. **Table** — Peeking evidence signals
   - Source: `peeking_evidence_summary`
   - Columns: signal, finding, evidence_level, interpretation

4. **Scatter** — Duration ratio vs p-value
   - Source: `peeking_detail`
   - X: `duration_ratio`
   - Y: `p_value`
   - Color: `was_peeked`

5. **Clustered bar** — Ship rate by peeking status
   - Create calculated column `Peeking Status` = IF(was_peeked, "Peeked", "Full Run")
   - Y: % shipped

6. **Bar chart** — Decision maker behavior
   - Source: `decision_maker_patterns`
   - X: `decision_maker`
   - Y: `ship_rate`

---

### Page 4: Revenue Impact

**Purpose:** Translate stats into business dollars — the most impressive page for non-technical audiences.

**KPI Cards:**

| Card | Source | Field |
|---|---|---|
| Total Opportunity | `revenue_summary` | `total_opportunity_usd` |
| Captured | `revenue_summary` | `captured_usd` |
| Missed | `revenue_summary` | `total_missed_usd` |
| Upside at 80% Power | `revenue_summary` | `additional_at_80_power_usd` |

**Visuals:**

1. **Waterfall** — `revenue_waterfall` (same as Page 1, larger)

2. **Stacked bar** — Missed revenue by team
   - Source: `revenue_missed_by_team`
   - X: `team`
   - Y: `missed_revenue_usd`

3. **Stacked bar** — Missed revenue by category
   - Source: `revenue_missed_by_feature_category`

4. **Table** — Top missed opportunities
   - Source: `top_missed_opportunities`
   - Sort by `annual_revenue_opportunity` descending

5. **Card** — Business assumptions
   - Source: `business_assumptions`
   - Display: MAU, monthly revenue, traffic share
   - Add note: "Assumptions documented and tunable"

**DAX for formatted millions:**

```dax
Revenue (M) = DIVIDE([total_missed_usd], 1000000)
```

---

### Page 5: Category Patterns & Maturity

**Purpose:** Strategic recommendations — where to invest experimentation effort.

**Visuals:**

1. **Gauge** — Maturity score
   - Source: `maturity_summary`
   - Value: `total_score`
   - Min: 0, Max: 100
   - Target: 70

2. **Stacked bar** — Maturity components
   - Source: `maturity_score`
   - X: `component`
   - Y: `weighted_score`

3. **Clustered bar** — Ship rate by category
   - Source: `category_win_rates`
   - X: `feature_category`
   - Y: `ship_rate_pct`

4. **Scatter** — Detection efficiency
   - Source: `category_detection_efficiency`
   - X: `real_positive_rate`
   - Y: `ship_rate`
   - Label: `feature_category`
   - Ideal zone: top-left (high real positive, low ship = big gap)

5. **Line chart** — Quarterly trends
   - Source: `org_learning_curve`
   - Multiple lines: ship_rate, median_power, peeking_rate

6. **Table** — Recommendations
   - Source: `category_recommendations`
   - Columns: priority, category, issue, recommendation

---

## Step 3: Useful DAX Measures

Add these to the `experiments` table for flexible analysis:

```dax
Total Experiments = COUNTROWS(experiments)

Shipped Count =
CALCULATE(COUNTROWS(experiments), experiments[decision] = "ship")

Ship Rate =
DIVIDE([Shipped Count], [Total Experiments])

Significance Rate =
DIVIDE(
    CALCULATE(COUNTROWS(experiments), experiments[p_value] < 0.05),
    [Total Experiments]
)

Avg Power =
AVERAGE(experiments[statistical_power])

Peeked Rate =
DIVIDE(
    CALCULATE(COUNTROWS(experiments), experiments[was_peeked] = TRUE()),
    [Total Experiments]
)

Real Positive Rate =
DIVIDE(
    CALCULATE(
        COUNTROWS(experiments),
        experiments[true_effect_type] IN {"small_positive", "medium_positive"}
    ),
    [Total Experiments]
)
```

---

## Step 4: Formatting & Portfolio Polish

### Visual best practices

- Use consistent number formats: `%` for rates, `$0.0M` for revenue
- Add **bookmarks** for "Filtered by Growth" and "Filtered by Monetization" demo views
- Add a **tooltip page** showing experiment detail on hover
- Include a **"Methodology"** page explaining simulation approach and limitations

### Recommended layout per page

```
┌─────────────────────────────────────────────────┐
│  Title + Slicers (Team | Category | Quarter)    │
├──────────┬──────────┬──────────┬─────────────────┤
│  KPI 1   │  KPI 2   │  KPI 3   │  KPI 4          │
├──────────────────────────┬──────────────────────┤
│  Main chart (60% width)  │  Secondary (40%)     │
├──────────────────────────┴──────────────────────┤
│  Detail table                                   │
└─────────────────────────────────────────────────┘
```

---

## Step 5: Publish & Share

### Option A: Power BI Service (recommended for portfolio)

1. **File** → **Publish** → sign in with Microsoft account
2. Create a free Power BI account if needed
3. Share the report link on your portfolio/resume
4. Set sharing to "Anyone with the link can view"

### Option B: Export as PDF

1. **File** → **Export** → **Export to PDF**
2. Use as a static portfolio artifact alongside the live link

### Option C: Embed screenshots

Take screenshots of each page for GitHub README or LinkedIn posts.

---

## Step 6: Portfolio Presentation Tips

When presenting this project, lead with the business story:

1. **Hook:** "I audited 100 A/B tests and found $15M in missed revenue"
2. **Problem:** Underpowering (11% median power) and peeking (42% of tests)
3. **Analysis:** 5 statistical frameworks (FDR, power, peeking, revenue, maturity)
4. **Recommendation:** 4 actionable fixes with ROI
5. **Deliverable:** Interactive Power BI dashboard + reproducible Python pipeline

### Interview talking points

- "Why simulated data?" → Real A/B results are proprietary; simulation lets you validate detection methods with known ground truth
- "Most actionable finding?" → Revenue waterfall — translates process failures into dollars
- "What would you do first?" → Implement minimum sample size requirements using the lookup table
- "Biggest limitation?" → Revenue model assumptions; show sensitivity analysis if asked

---

## File Reference

| Export File | Best Visual |
|---|---|
| `revenue_waterfall.csv` | Waterfall chart |
| `revenue_summary.csv` | KPI cards |
| `org_learning_curve.csv` | Line chart |
| `category_win_rates.csv` | Bar chart |
| `category_detection_efficiency.csv` | Scatter plot |
| `maturity_score.csv` | Stacked bar / gauge |
| `power_overall_summary.csv` | KPI cards |
| `missed_winners.csv` | Table |
| `top_missed_opportunities.csv` | Table (executive) |
| `peeking_evidence_summary.csv` | Table |
| `fdr_summary.csv` | Table |
| `pvalue_distribution.csv` | Histogram |
| `sample_size_lookup_table.csv` | Matrix |
| `category_recommendations.csv` | Table |
| `business_assumptions.csv` | Card / text |

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Quarter sorts alphabetically | Use `Quarter Sort` calculated column |
| Revenue shows as text | Set `amount_usd` to Decimal in Power Query |
| Relationships cause duplicates | Use summary tables without relationships for KPI cards |
| `true_effect_type` shows blank | Reload `experiments.csv` — "null" was renamed to `no_effect` |
| Waterfall chart unavailable | Use Stacked bar as fallback, or install waterfall custom visual |
