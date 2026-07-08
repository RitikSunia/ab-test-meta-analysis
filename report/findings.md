# A/B Test Meta-Analysis Engine — Findings Report

**Author:** [Your Name]  
**Date:** [Date]  
**Domain:** Media / Content Platform (Streaming + News)  
**Scope:** 100 experiments across 6 quarters (2023-Q1 to 2024-Q2)

---

## Executive Summary

I conducted a meta-analysis of 100 A/B experiments run by a simulated media/content platform to audit the health of their experimentation program. The analysis reveals a program that is **activity-rich but outcome-poor**: teams are running many tests, but systemic underpowering, peeking behavior, and weak detection processes mean the organization captures only **18% of available revenue opportunity** — leaving an estimated **$15.0M annually** on the table.

The experimentation program scores **40.2/100** on a composite maturity index, classifying it as **Early Stage**. While shipped decisions happen to be correct (0% false discovery rate among shipped winners), this is due to conservative decision-making rather than rigorous process — 41% of nominally significant results would not survive multiple-testing correction.

**Top recommendation:** Implement minimum sample size requirements and sequential testing protocols. The ROI case is clear: improving to 80% statistical power could unlock an additional **$11.4M per year**.

---

## 1. Background & Objective

### Business Context

The platform has 2.5M monthly active users and $102M in annual revenue (subscriptions + advertising). Four teams — Growth, Engagement, Monetization, and Content-Algo — run experiments across six feature categories including UI/UX, recommendation algorithms, pricing/paywalls, content formats, notifications, and onboarding flows.

### Objective

Answer six strategic questions about experimentation quality:

1. What is the actual false discovery rate?
2. Are experiments systematically underpowered?
3. Is there evidence of peeking or p-hacking?
4. How much revenue is lost due to bad experimentation practices?
5. Which experiment categories consistently win or lose?
6. Is the organization improving over time?

### Methodology

- **Data:** 100 simulated experiments with known ground-truth effects (52% no effect, 25% small positive, 12% medium positive, 11% negative)
- **Why simulation:** Real A/B test results are proprietary; simulation enables validation of detection methods against known truth
- **Analysis:** Python (pandas, scipy, statsmodels) for statistical analysis; Power BI for visualization
- **Revenue model:** Metric-specific translation of relative lifts to annual dollar impact, documented in `business_assumptions.csv`

---

## 2. Key Findings

### 2.1 False Discovery Rate — Decisions Are Accidentally Correct

| Method | FDR Estimate | Interpretation |
|---|---|---|
| Ground truth (simulation) | 0% | 0 of 13 shipped experiments had zero true effect |
| Benjamini-Hochberg correction | 41% | 7 of 17 significant results would not survive FDR correction |
| Post-ship reversal rate | 0% | 0 of 13 shipped experiments showed no lift in production |

**Insight:** The organization's conservative shipping criteria accidentally prevent false discoveries. However, if they shipped everything at p < 0.05, nearly half would be false positives. The process works by being overly cautious, not by being rigorous.

### 2.2 Power Audit — Critically Underpowered

| Metric | Value | Target |
|---|---|---|
| Median statistical power | **10.9%** | 80% |
| Adequately powered (≥80%) | **13%** | >80% of experiments |
| Severely underpowered (<20%) | **62%** | <10% |
| Real winners missed | **32 of 44** | — |
| Improvement at 80% power | **2.92x** more winners detected | — |

**By team:**

| Team | Median Power | Ship Rate |
|---|---|---|
| Content-Algo | 39.0% | 27% |
| Monetization | 10.5% | 0% |
| Engagement | 2.5% | 15% |
| Growth | 2.5% | 9% |

**Insight:** The typical experiment uses only 71% of the required sample size. Growth and Engagement teams are essentially running coin-flip experiments on their most important metrics. Monetization ran 25 experiments and shipped zero — not because nothing works, but because tests lack power to detect real effects.

### 2.3 Peeking Detection — Behavioral Bias, Not P-Hacking

| Signal | Finding | Verdict |
|---|---|---|
| Caliper test (p-value clustering at 0.05) | Ratio = 1.0 | Clean |
| P-value uniformity (null experiments) | KS p = 0.41 | Clean |
| Peeking vs significance rate | 21% (peeked) vs 14% (not peeked) | Moderate concern |
| Duration shortfall bias | Early-stopped: 21% sig vs 14% full-run | Moderate concern |

**Key facts:**
- 42% of experiments are stopped before reaching planned duration
- Peeked experiments ship at **19%** vs **9%** for non-peeked (2.1x higher)
- No crude p-hacking detected, but selection bias from early stopping inflates apparent win rates

**Decision-maker behavior:**

| Role | Ship Rate | Avg p-value When Shipping |
|---|---|---|
| Data | 8.5% | 0.003 |
| PM | 16.7% | 0.011 |
| Leadership | 17.6% | 0.003 |

Data team acts as the most conservative gatekeeper; PMs ship at 2x the rate of the data team.

### 2.4 Revenue Impact — $15M Left on the Table

| Category | Amount |
|---|---|
| Total revenue opportunity (all real winners) | $18.4M |
| Revenue captured (shipped winners) | $3.3M |
| **Total missed** | **$15.0M** |
| — Missed due to peeking | $2.1M |
| — Missed due to underpowering | $1.4M |
| — Missed due to sampling noise / other | $11.5M |
| — Post-ship lift degradation | $0.2M |
| Potential at 80% power program | $14.7M |
| **Additional upside at 80% power** | **$11.4M** |

Missed revenue represents **14.7% of total annual revenue** ($102M).

**Top missed opportunity:** EXP-0064 — Bottom nav bar redesign (+10.7% true effect, $10.8M annual opportunity).

**By team:** Monetization accounts for $12.1M of the $15.0M missed — low base rates on conversion metrics amplify the dollar impact of undetected effects.

### 2.5 Category Patterns — High Potential, Low Detection

| Category | Ship Rate | Real Positive Rate | Detection Efficiency |
|---|---|---|---|
| Pricing/Paywall | 25% | 67% | 38% |
| Onboarding-Flow | 20% | 53% | 38% |
| Notifications | 12% | 59% | 20% |
| UI/UX | 10% | 35% | 29% |
| Content-Format | 9% | 36% | 25% |
| Recommendation-Algo | 7% | 21% | 33% |

Chi-squared test: No statistically significant difference in ship rates across categories (p = 0.69).

**Insight:** Notifications has the highest real-positive rate (59%) but the lowest detection efficiency (20%) — the biggest strategic gap. Pricing/Paywall is the strongest performer with 25% ship rate and 10% average lift when shipped.

### 2.6 Org Learning Curve — Not Improving Systematically

| Quarter | Ship Rate | Median Power | Peeking Rate |
|---|---|---|---|
| 2023-Q1 | 0% | 2.5% | 24% |
| 2023-Q2 | 30% | 30.3% | 45% |
| 2023-Q3 | 5% | 2.5% | 62% |
| 2024-Q2 | 13% | 4.5% | 25% |

**Trend analysis:**
- Ship rate: slowly improving (+1.0%/quarter)
- Power: flat (no meaningful improvement)
- Peeking: worsening (+0.5%/quarter)

**Experimentation Maturity Score: 40.2/100 (Early Stage)**

| Component | Weighted Score |
|---|---|
| Power adequacy | 8.2 / 30 |
| Ship decision quality | 6.8 / 25 |
| Process discipline | 11.6 / 20 |
| Detection efficiency | 4.1 / 15 |
| Sample size compliance | 9.5 / 10 |

---

## 3. Recommendations

### Priority 1: Implement Minimum Sample Size Requirements

Use the exported `sample_size_lookup_table.csv` as a pre-experiment planning tool. No experiment should launch without confirming adequate power for the planned MDE.

**Expected impact:** 2.92x more real winners detected.

### Priority 2: Adopt Sequential Testing for Safe Peeking

42% of experiments are peeked. Rather than banning peeking (which teams will do anyway), implement always-valid p-values or group sequential designs that maintain statistical validity.

**Expected impact:** Reduce selection bias; recover $2.1M in peeking-related missed revenue.

### Priority 3: Require Pre-Registration

Lock experiment duration, primary metric, and sample size before launch. Prevents moving goalposts and documents intent.

**Expected impact:** Improve process discipline score from 11.6 to target 16+.

### Priority 4: Post-Ship Holdback Validation

Keep 5% of traffic on control for 30 days after shipping. Validates that test results hold in production and catches false discoveries early.

**Expected impact:** Reduce post-ship degradation losses; build confidence in shipped decisions.

---

## 4. Limitations

1. **Simulated data:** Results depend on simulation assumptions (effect size distributions, peeking rates). Real-world data may differ.
2. **Revenue model assumptions:** Dollar estimates are illustrative, based on documented assumptions in `business_assumptions.csv`. Actual impact depends on traffic, monetization, and experiment scope.
3. **Single organization:** Findings reflect one simulated company's behavior patterns, not industry benchmarks.
4. **No interaction effects:** Experiments are analyzed independently; overlapping tests are not modeled.

### Sensitivity Analysis (Optional Extension)

To strengthen the portfolio, vary key assumptions and show how conclusions change:
- What if 30% (not 52%) of experiments have no effect?
- What if peeking rate is 20% instead of 42%?
- What if monthly revenue is $5M instead of $8.5M?

---

## 5. Deliverables

| Deliverable | Location |
|---|---|
| Python analysis pipeline (5 stages) | `analysis/` |
| Simulated experiment dataset | `data/experiments.csv` |
| 31 Power BI-ready export files | `exports/` |
| Interactive Power BI dashboard | [Link to published report] |
| This findings report | `report/findings.md` |
| Dashboard build guide | `report/power_bi_dashboard_guide.md` |

---

## 6. Conclusion

This meta-analysis demonstrates that experimentation volume alone does not drive value. A media platform running 100 experiments per year can still miss 82% of available revenue improvement if tests are underpowered, peeked at, and decided without statistical guardrails.

The path forward is not more experiments — it is better experiments. The data supports a clear ROI case for investing in experimentation infrastructure: an estimated **$11.4M in additional annual revenue** from reaching 80% statistical power, against the cost of longer test durations and governance tooling.

The maturity score (40.2/100) provides a baseline KPI to track quarterly improvement as recommendations are implemented.

---

*Analysis pipeline is fully reproducible. Clone the repository, run `pip install -r requirements.txt`, execute the five analysis scripts, and rebuild the Power BI dashboard from exported CSVs.*
