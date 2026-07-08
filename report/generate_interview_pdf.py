"""
Generate a professional PDF interview guide for the A/B Test Meta-Analysis project.
Run: python report/generate_interview_pdf.py
Output: report/AB_Test_Meta_Analysis_Interview_Guide.pdf
"""

import os
from datetime import date

try:
    from fpdf import FPDF
except ImportError:
    raise SystemExit(
        "fpdf2 is required. Install with: python -m pip install fpdf2"
    )


class InterviewPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "A/B Test Meta-Analysis Engine | Portfolio Interview Guide", align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(21, 101, 192)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(self.l_margin)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(self.l_margin)
        self.multi_cell(0, 5.5, f"  -  {text}")
        self.ln(1)


def build_pdf(output_path):
    pdf = InterviewPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Cover
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(21, 101, 192)
    pdf.ln(20)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 12, "A/B Test Meta-Analysis Engine")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(60, 60, 60)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 8, "Portfolio Project Interview Guide")
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 11)
    cover_lines = [
        f"Date: {date.today().strftime('%B %d, %Y')}",
        "Domain: Media and Content Platform (Streaming and News)",
        "Tools: Python, scipy, statsmodels, Power BI",
    ]
    for line in cover_lines:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, line)
    pdf.ln(15)

    pdf.set_draw_color(21, 101, 192)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)

    pdf.section_title("30-Second Elevator Pitch")
    pdf.body_text(
        "I built an end-to-end meta-analysis of 100 A/B experiments for a simulated media platform. "
        "The project audits experimentation program health using five statistical frameworks: false discovery rate, "
        "power analysis, peeking detection, revenue impact modeling, and organizational maturity scoring. "
        "I found the program captures only 18% of available value, with $15M in annual revenue left on the table, "
        "and delivered actionable recommendations through a reproducible Python pipeline and Power BI dashboard."
    )

    pdf.section_title("1. Project Objective")
    pdf.body_text(
        "The objective was to demonstrate strategic data analyst capabilities beyond running individual t-tests. "
        "Instead of analyzing one experiment, this project audits an entire experimentation program to answer: "
        "Are we shipping false winners? Are tests underpowered? Is peeking inflating results? "
        "How much revenue are we losing? Which experiment types work best? Is the organization improving over time?"
    )
    pdf.body_text(
        "This mirrors real work done by senior analysts and experimentation platform teams at companies like "
        "Booking.com, Netflix, and Microsoft, who publish research on experimentation program quality."
    )

    pdf.section_title("2. Why This Project Was Built")
    pdf.sub_title("Problem it solves")
    pdf.bullet("Most data analyst portfolios show descriptive dashboards on clean Kaggle datasets.")
    pdf.bullet("Hiring managers struggle to see if candidates understand experimentation at a strategic level.")
    pdf.bullet("Real A/B test data is proprietary and cannot be shared publicly.")
    pdf.sub_title("Solution approach")
    pdf.bullet("Simulate 100 realistic experiments with known ground truth (so detection methods can be validated).")
    pdf.bullet("Apply rigorous statistical methods used in industry experimentation audits.")
    pdf.bullet("Translate statistical findings into dollar impact for business stakeholders.")
    pdf.bullet("Deliver reproducible code plus visualization-ready exports for Power BI.")

    pdf.add_page()
    pdf.section_title("3. What Was Built (End-to-End)")
    pdf.sub_title("Stage 1: Data Generation")
    pdf.bullet("Python simulation of 100 experiments across 4 teams and 6 feature categories.")
    pdf.bullet("Realistic biases: 42% peeking rate, underpowered sample sizes, conservative shipping.")
    pdf.bullet("Ground truth labels (no_effect, small_positive, medium_positive, negative) for validation.")
    pdf.sub_title("Stage 2: False Discovery Rate Analysis")
    pdf.bullet("Three FDR estimation methods: ground truth, Benjamini-Hochberg, post-ship reversal.")
    pdf.bullet("Finding: 0% FDR among shipped, but 41% of significant results fail BH correction.")
    pdf.sub_title("Stage 3: Power Audit")
    pdf.bullet("Median power: 10.9% (target: 80%). 62% of tests severely underpowered.")
    pdf.bullet("32 of 44 real winners missed. 2.92x more winners detectable at 80% power.")
    pdf.sub_title("Stage 4: Peeking / P-Hacking Detection")
    pdf.bullet("Caliper test, Fisher's exact test, KS uniformity test, duration shortfall analysis.")
    pdf.bullet("No crude p-hacking, but peeked tests ship 2.1x more often (selection bias).")
    pdf.sub_title("Stage 5: Revenue Impact")
    pdf.bullet("$18.4M total opportunity, $3.3M captured, $15.0M missed (14.7% of annual revenue).")
    pdf.bullet("$11.4M additional upside if program reaches 80% power.")
    pdf.sub_title("Stage 6: Category Patterns + Maturity Score")
    pdf.bullet("Maturity score: 40.2/100 (Early Stage). Notifications has highest detection gap.")
    pdf.bullet("Quarterly learning curve shows flat power improvement, worsening peeking.")
    pdf.sub_title("Stage 7: Deliverables")
    pdf.bullet("31 Power BI-ready CSV exports, written findings report, dashboard build guide.")

    pdf.add_page()
    pdf.section_title("4. Key Findings (Interview-Ready)")
    pdf.sub_title("Headline metrics")
    pdf.bullet("100 experiments | 13 shipped (13%) | 17 statistically significant (17%)")
    pdf.bullet("Median statistical power: 10.9% | Peeking rate: 42%")
    pdf.bullet("Revenue capture rate: 18% | Maturity score: 40.2/100")
    pdf.sub_title("Top 3 insights")
    pdf.bullet("Underpowering is the root cause: teams run tests too short/small to detect real effects.")
    pdf.bullet("Peeking creates selection bias: early-stopped tests ship more often, not because they are better.")
    pdf.bullet("Revenue framing makes the case actionable: $15M missed is more compelling than 'low power'.")
    pdf.sub_title("Recommendations delivered")
    pdf.bullet("Implement minimum sample size requirements (lookup table provided).")
    pdf.bullet("Adopt sequential testing for safe peeking.")
    pdf.bullet("Require pre-registration of metrics, duration, and sample size.")
    pdf.bullet("Post-ship holdback validation (5% control traffic for 30 days).")

    pdf.section_title("5. Technical Skills Demonstrated")
    pdf.bullet("Python: pandas, numpy, scipy, statsmodels for statistical analysis")
    pdf.bullet("Statistics: two-proportion z-test, Benjamini-Hochberg FDR, power analysis, KS test, chi-squared, Fisher's exact")
    pdf.bullet("Data engineering: reproducible pipeline, modular utils, batch export generation")
    pdf.bullet("Business analytics: revenue modeling, waterfall analysis, maturity scoring")
    pdf.bullet("Visualization: Power BI dashboard design with 5 themed pages")
    pdf.bullet("Communication: executive summary, written report, interview narrative")

    pdf.add_page()
    pdf.section_title("6. What Interviewers Will Get Out of This")
    pdf.sub_title("For hiring managers")
    pdf.bullet("Evidence you think beyond SQL queries and basic charts.")
    pdf.bullet("You can connect statistical rigor to business outcomes (dollars, not just p-values).")
    pdf.bullet("You understand how experimentation programs fail at the organizational level.")
    pdf.sub_title("For technical interviewers")
    pdf.bullet("You can explain WHY each statistical test was chosen and its limitations.")
    pdf.bullet("You built a reproducible pipeline, not a one-off notebook.")
    pdf.bullet("You handled real-world data issues (CSV null parsing, scipy API changes).")
    pdf.sub_title("For business stakeholders")
    pdf.bullet("Clear ROI case: $11.4M upside from fixing experimentation infrastructure.")
    pdf.bullet("Prioritized recommendations with expected impact per initiative.")
    pdf.bullet("Maturity score provides a trackable KPI for program improvement.")

    pdf.section_title("7. Common Interview Questions & Answers")
    qa = [
        ("Why simulated data instead of real?",
         "Real A/B results are proprietary. Simulation lets me know ground truth to validate "
         "detection methods. Post-ship holdback would be the real-world equivalent."),
        ("What is the most actionable finding?",
         "The revenue waterfall. It translates process failures into dollars leaders understand. "
         "$15M missed is more actionable than 'median power is 11%'."),
        ("What would you do first if hired?",
         "Implement minimum sample size requirements using the lookup table. It is low-cost, "
         "high-impact, and addresses the root cause of missed winners."),
        ("Biggest limitation?",
         "Revenue estimates depend on documented assumptions (MAU, ARPU). I would run sensitivity "
         "analysis varying those inputs to show robustness."),
        ("How is this different from a Kaggle project?",
         "It is prescriptive, not descriptive. It answers 'what should we do' not just 'what happened'. "
         "It uses multiple data sources, statistical frameworks, and business translation."),
    ]
    for q, a in qa:
        pdf.sub_title(f"Q: {q}")
        pdf.body_text(f"A: {a}")

    pdf.add_page()
    pdf.section_title("8. How to Present in an Interview (5-Minute Structure)")
    pdf.bullet("Minute 1: Context - media platform, 100 experiments, experimentation audit objective.")
    pdf.bullet("Minute 2: Problem - 11% median power, 42% peeking, only 18% revenue captured.")
    pdf.bullet("Minute 3: Approach - 5-stage pipeline, 3 FDR methods, revenue model, maturity score.")
    pdf.bullet("Minute 4: Top finding - $15M missed, 32 real winners not shipped, 2.92x improvement possible.")
    pdf.bullet("Minute 5: Recommendations + your role - built pipeline, exports, Power BI, written report.")

    pdf.section_title("9. Project Repository Structure")
    pdf.body_text(
        "data/ - Simulation script and experiments.csv\n"
        "analysis/ - 5 analysis scripts + run_all.py + utils.py\n"
        "exports/ - 31 Power BI-ready CSV files\n"
        "report/ - Findings report, Power BI guide, this interview PDF\n"
        "README.md - Project overview and setup instructions"
    )

    pdf.section_title("10. Next Steps to Strengthen the Portfolio")
    pdf.bullet("Publish Power BI dashboard and add live link to README.")
    pdf.bullet("Add sensitivity analysis section (vary revenue assumptions).")
    pdf.bullet("Record a 3-minute Loom walkthrough of the dashboard.")
    pdf.bullet("Add Bayesian analysis comparison as a bonus section.")

    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        0, 5,
        "This document accompanies the GitHub repository. "
        "All analysis is reproducible via: python analysis/run_all.py"
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    return output_path


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(base, "AB_Test_Meta_Analysis_Interview_Guide.pdf")
    path = build_pdf(out)
    print(f"PDF generated: {path}")
