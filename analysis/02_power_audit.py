"""
Stage 3: Statistical Power Audit

Key question: Are we systematically running underpowered tests,
and what does that cost us in missed real effects?

Outputs:
- Power distribution across all experiments
- Power breakdown by team, category, quarter
- Recommended sample sizes vs. actual
- Missed winners due to underpowering
- Exports for Power BI
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
from utils import calculate_power, required_sample_size

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiments.csv')
EXPORT_PATH = os.path.join(os.path.dirname(__file__), '..', 'exports')


def load_data():
    return pd.read_csv(DATA_PATH)


def overall_power_assessment(df):
    """High-level power statistics across the experiment corpus."""
    power_values = df['statistical_power'].dropna()

    return {
        'total_experiments': len(df),
        'experiments_with_power_data': len(power_values),
        'mean_power': round(power_values.mean(), 4),
        'median_power': round(power_values.median(), 4),
        'pct_adequately_powered': round((power_values >= 0.80).mean(), 4),
        'pct_underpowered_below_50': round((power_values < 0.50).mean(), 4),
        'pct_severely_underpowered_below_20': round((power_values < 0.20).mean(), 4),
        'power_25th_percentile': round(power_values.quantile(0.25), 4),
        'power_75th_percentile': round(power_values.quantile(0.75), 4),
    }


def power_by_group(df):
    """Break down power by team, category, and quarter."""
    results = {}

    for group_col in ['team', 'feature_category', 'quarter']:
        grouped = df.groupby(group_col)['statistical_power'].agg([
            ('median_power', 'median'),
            ('mean_power', 'mean'),
            ('pct_adequate', lambda x: (x >= 0.80).mean()),
            ('n_experiments', 'count'),
        ]).round(4)
        grouped = grouped.sort_values('median_power', ascending=False)
        results[group_col] = grouped

    return results


def sample_size_gap_analysis(df):
    """
    For each experiment, calculate what sample size was NEEDED
    vs what was actually used. Quantify the gap.
    """
    rows = []

    for _, row in df.iterrows():
        needed_n = required_sample_size(
            base_rate=row['base_rate'],
            relative_mde=row['planned_mde'],
            power=0.80,
            alpha=0.05
        )

        actual_n = row['actual_n_control']
        gap_ratio = actual_n / needed_n if needed_n and needed_n != np.inf else None

        rows.append({
            'experiment_id': row['experiment_id'],
            'team': row['team'],
            'feature_category': row['feature_category'],
            'base_rate': row['base_rate'],
            'planned_mde': row['planned_mde'],
            'required_n_per_group': needed_n if needed_n != np.inf else None,
            'actual_n_per_group': actual_n,
            'sample_gap_ratio': round(gap_ratio, 3) if gap_ratio else None,
            'adequately_sized': gap_ratio >= 1.0 if gap_ratio else False,
        })

    gap_df = pd.DataFrame(rows)
    gap_df = gap_df[gap_df['required_n_per_group'].notna()]

    return gap_df


def missed_winners_analysis(df):
    """
    Identify experiments that had a REAL positive effect but were
    not shipped — likely because the test was underpowered.
    """
    real_positives = df[df['true_effect_type'].isin(['small_positive', 'medium_positive'])]
    missed = real_positives[real_positives['decision'] != 'ship']

    missed_detail = missed[[
        'experiment_id', 'experiment_name', 'team', 'feature_category',
        'true_effect', 'true_effect_type', 'statistical_power',
        'p_value', 'decision', 'actual_n_control', 'planned_mde'
    ]].copy()

    missed_detail['reason_missed'] = missed_detail.apply(_classify_miss_reason, axis=1)
    missed_detail = missed_detail.sort_values('true_effect', ascending=False)

    return missed_detail


def _classify_miss_reason(row):
    """Determine why a real winner was missed."""
    reasons = []
    if row['statistical_power'] < 0.50:
        reasons.append('severely_underpowered')
    elif row['statistical_power'] < 0.80:
        reasons.append('underpowered')

    if row['true_effect'] < row['planned_mde']:
        reasons.append('effect_smaller_than_mde')

    if not reasons:
        reasons.append('bad_luck_sampling_noise')

    return '; '.join(reasons)


def power_improvement_simulation(df):
    """
    Simulate: if we had run every experiment at 80% power,
    how many more winners would we have detected?
    """
    real_positives = df[df['true_effect_type'].isin(['small_positive', 'medium_positive'])]

    detected_actual = real_positives[real_positives['decision'] == 'ship']
    detection_rate_actual = len(detected_actual) / len(real_positives) if len(real_positives) > 0 else 0

    # At 80% power, ~80% of real effects would be detected
    expected_detection_at_80_power = int(len(real_positives) * 0.80)
    additional_winners = expected_detection_at_80_power - len(detected_actual)

    return {
        'total_real_positives': len(real_positives),
        'detected_currently': len(detected_actual),
        'detection_rate_current': round(detection_rate_actual, 4),
        'expected_detected_at_80_power': expected_detection_at_80_power,
        'additional_winners_at_80_power': additional_winners,
        'improvement_factor': round(expected_detection_at_80_power / max(len(detected_actual), 1), 2),
    }


def recommended_sample_sizes_table(df):
    """
    Create a lookup table: for each metric type and common MDEs,
    show the required sample size. This becomes a practical tool for the org.
    """
    metrics = df.groupby('primary_metric')['base_rate'].median().to_dict()
    mde_levels = [0.03, 0.05, 0.08, 0.10, 0.15]

    rows = []
    for metric, base_rate in sorted(metrics.items()):
        for mde in mde_levels:
            n = required_sample_size(base_rate, mde, power=0.80)
            rows.append({
                'metric': metric,
                'base_rate': base_rate,
                'mde_relative': mde,
                'required_n_per_group': n if n != np.inf else None,
                'required_total_n': n * 2 if n != np.inf else None,
            })

    return pd.DataFrame(rows)


def export_results(overall, by_group, gap_df, missed_df, simulation, lookup_table):
    """Export all power audit data for Power BI."""
    os.makedirs(EXPORT_PATH, exist_ok=True)

    # Overall power metrics
    pd.DataFrame([overall]).to_csv(
        os.path.join(EXPORT_PATH, 'power_overall_summary.csv'), index=False
    )

    # Power by group
    for group_name, group_df in by_group.items():
        group_df.to_csv(
            os.path.join(EXPORT_PATH, f'power_by_{group_name}.csv')
        )

    # Sample size gap
    gap_df.to_csv(
        os.path.join(EXPORT_PATH, 'sample_size_gap.csv'), index=False
    )

    # Missed winners
    missed_df.to_csv(
        os.path.join(EXPORT_PATH, 'missed_winners.csv'), index=False
    )

    # Simulation results
    pd.DataFrame([simulation]).to_csv(
        os.path.join(EXPORT_PATH, 'power_improvement_simulation.csv'), index=False
    )

    # Sample size lookup table
    lookup_table.to_csv(
        os.path.join(EXPORT_PATH, 'sample_size_lookup_table.csv'), index=False
    )

    print(f"  Exported 6 files to {EXPORT_PATH}/")


def main():
    print("=" * 60)
    print("STAGE 3: STATISTICAL POWER AUDIT")
    print("=" * 60)

    df = load_data()

    # --- Overall Assessment ---
    overall = overall_power_assessment(df)
    print(f"\n--- Overall Power Assessment ---")
    print(f"  Median power:                    {overall['median_power']:.1%}")
    print(f"  Adequately powered (>=80%):      {overall['pct_adequately_powered']:.0%}")
    print(f"  Underpowered (<50%):             {overall['pct_underpowered_below_50']:.0%}")
    print(f"  Severely underpowered (<20%):    {overall['pct_severely_underpowered_below_20']:.0%}")

    # --- By Group ---
    by_group = power_by_group(df)
    print(f"\n--- Power by Team ---")
    print(by_group['team'].to_string())
    print(f"\n--- Power by Feature Category ---")
    print(by_group['feature_category'].to_string())
    print(f"\n--- Power by Quarter (learning curve?) ---")
    print(by_group['quarter'].to_string())

    # --- Sample Size Gap ---
    gap_df = sample_size_gap_analysis(df)
    adequately_sized_pct = gap_df['adequately_sized'].mean()
    median_gap = gap_df['sample_gap_ratio'].median()
    print(f"\n--- Sample Size Gap Analysis ---")
    print(f"  Adequately sized experiments:  {adequately_sized_pct:.0%}")
    print(f"  Median sample ratio (actual/needed): {median_gap:.2f}x")
    print(f"  (1.0x = exactly right, <1.0x = too small)")

    # --- Missed Winners ---
    missed_df = missed_winners_analysis(df)
    print(f"\n--- Missed Winners ---")
    print(f"  Real positive experiments:     {len(df[df['true_effect_type'].isin(['small_positive', 'medium_positive'])])}")
    print(f"  Actually shipped:              {len(df[(df['true_effect_type'].isin(['small_positive', 'medium_positive'])) & (df['decision'] == 'ship')])}")
    print(f"  Missed (not shipped):          {len(missed_df)}")
    print(f"\n  Top missed winners:")
    for _, row in missed_df.head(5).iterrows():
        print(f"    {row['experiment_id']} | true effect: +{row['true_effect']:.1%} | power: {row['statistical_power']:.0%} | reason: {row['reason_missed']}")

    # --- Improvement Simulation ---
    simulation = power_improvement_simulation(df)
    print(f"\n--- What If We Had 80% Power? ---")
    print(f"  Real positives in corpus:      {simulation['total_real_positives']}")
    print(f"  Currently detecting:           {simulation['detected_currently']}")
    print(f"  Would detect at 80% power:     {simulation['expected_detected_at_80_power']}")
    print(f"  Additional winners found:      +{simulation['additional_winners_at_80_power']}")
    print(f"  Improvement factor:            {simulation['improvement_factor']}x more winners")

    # --- Sample Size Lookup ---
    lookup = recommended_sample_sizes_table(df)
    print(f"\n--- Sample Size Lookup Table (for org use) ---")
    print("  [Exported to CSV — shows required N for each metric at common MDE levels]")

    # --- Export ---
    print(f"\n--- Exporting ---")
    export_results(overall, by_group, gap_df, missed_df, simulation, lookup)

    # --- Summary ---
    print("\n" + "=" * 60)
    print("FINDINGS SUMMARY")
    print("=" * 60)
    print(f"""
  CRITICAL: This organization is severely underpowered.

  • Median power is {overall['median_power']:.0%} (industry standard target: 80%)
  • {overall['pct_severely_underpowered_below_20']:.0%} of experiments have <20% power
  • Only {overall['pct_adequately_powered']:.0%} of experiments meet the 80% threshold
  • Typical experiment uses {median_gap:.1f}x the required sample size
  • {len(missed_df)} real winners were missed — {simulation['improvement_factor']}x more could be found

  RECOMMENDATION: Implement minimum sample size requirements.
  Use the exported lookup table as a planning tool.
    """)


if __name__ == '__main__':
    main()
