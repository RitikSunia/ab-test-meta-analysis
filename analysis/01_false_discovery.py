"""
Stage 2: False Discovery Rate (FDR) Analysis

Key question: Among experiments we declared "winners" and shipped,
how many actually had no real effect?

Outputs:
- FDR estimates via 3 methods
- P-value distribution analysis
- Summary table exported to ../exports/fdr_summary.csv
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
from utils import benjamini_hochberg

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiments.csv')
EXPORT_PATH = os.path.join(os.path.dirname(__file__), '..', 'exports')


def load_data():
    df = pd.read_csv(DATA_PATH)
    return df


def method_1_ground_truth_fdr(df):
    """
    Direct FDR using simulation ground truth.
    In real life you wouldn't have this — it validates the other methods.
    """
    shipped = df[df['decision'] == 'ship']
    false_discoveries = shipped[shipped['true_effect_type'] == 'no_effect']

    fdr = len(false_discoveries) / len(shipped) if len(shipped) > 0 else 0

    return {
        'method': 'Ground Truth (Simulation Only)',
        'fdr_estimate': round(fdr, 4),
        'n_shipped': len(shipped),
        'n_false_discoveries': len(false_discoveries),
        'interpretation': f"{len(false_discoveries)} of {len(shipped)} shipped experiments had zero true effect"
    }


def method_2_benjamini_hochberg(df):
    """
    Apply BH correction to all p-values.
    Compare how many "significant" results survive adjustment.
    """
    significant_raw = (df['p_value'] < 0.05).sum()
    rejected_bh = benjamini_hochberg(df['p_value'].values, alpha=0.05)
    significant_bh = rejected_bh.sum()

    lost_to_correction = significant_raw - significant_bh
    implied_fdr = lost_to_correction / significant_raw if significant_raw > 0 else 0

    return {
        'method': 'Benjamini-Hochberg Correction',
        'significant_before_correction': int(significant_raw),
        'significant_after_correction': int(significant_bh),
        'lost_to_correction': int(lost_to_correction),
        'implied_fdr': round(implied_fdr, 4),
        'interpretation': f"{lost_to_correction} of {significant_raw} significant results would not survive FDR correction"
    }


def method_3_post_ship_reversal(df):
    """
    Empirical FDR: among shipped experiments with post-ship data,
    how many showed zero or negative lift in production?
    """
    shipped = df[df['decision'] == 'ship'].copy()
    shipped_with_data = shipped[shipped['post_ship_lift'].notna()]

    reversals = shipped_with_data[shipped_with_data['post_ship_lift'] <= 0]
    degradations = shipped_with_data[shipped_with_data['post_ship_lift'] < -0.01]

    fdr_reversal = len(reversals) / len(shipped_with_data) if len(shipped_with_data) > 0 else 0

    return {
        'method': 'Post-Ship Reversal Rate',
        'n_shipped_with_followup': len(shipped_with_data),
        'n_reversals': len(reversals),
        'n_degradations': len(degradations),
        'fdr_estimate': round(fdr_reversal, 4),
        'interpretation': f"{len(reversals)} of {len(shipped_with_data)} shipped experiments showed no lift in production"
    }


def pvalue_distribution_analysis(df):
    """
    Analyze the p-value distribution.
    Under all-null, p-values should be uniform.
    Excess of small p-values = real effects exist.
    Spike just below 0.05 = potential p-hacking.
    """
    p_values = df['p_value'].values

    bins_below_05 = np.sum(p_values < 0.05)
    expected_below_05 = len(p_values) * 0.05

    bin_edges = np.arange(0, 1.05, 0.05)
    counts, _ = np.histogram(p_values, bins=bin_edges)

    just_below_05 = np.sum((p_values >= 0.04) & (p_values < 0.05))
    just_above_05 = np.sum((p_values >= 0.05) & (p_values < 0.06))
    caliper_ratio = just_below_05 / just_above_05 if just_above_05 > 0 else float('inf')

    null_only = df[df['true_effect_type'] == 'no_effect']['p_value'].values
    ks_stat, ks_p = stats.kstest(null_only, 'uniform') if len(null_only) > 5 else (None, None)

    return {
        'total_experiments': len(p_values),
        'significant_at_05': int(bins_below_05),
        'expected_significant_if_all_null': round(expected_below_05, 1),
        'caliper_ratio_04_05_vs_05_06': round(caliper_ratio, 2),
        'ks_test_null_experiments': {
            'statistic': round(ks_stat, 4) if ks_stat else None,
            'p_value': round(ks_p, 4) if ks_p else None,
            'uniform_null_rejected': ks_p < 0.05 if ks_p else None,
        },
        'p_value_histogram_counts': counts.tolist(),
        'p_value_histogram_bins': bin_edges.tolist(),
    }


def export_results(df, fdr_results):
    """Export analysis results for Power BI."""
    os.makedirs(EXPORT_PATH, exist_ok=True)

    # FDR summary table
    summary_rows = []
    for result in fdr_results:
        summary_rows.append({
            'method': result.get('method', ''),
            'fdr_estimate': result.get('fdr_estimate', result.get('implied_fdr', '')),
            'interpretation': result.get('interpretation', ''),
        })
    pd.DataFrame(summary_rows).to_csv(
        os.path.join(EXPORT_PATH, 'fdr_summary.csv'), index=False
    )

    # Shipped experiments detail (for Power BI drill-down)
    shipped = df[df['decision'] == 'ship'].copy()
    shipped['is_false_discovery'] = shipped['true_effect_type'] == 'no_effect'
    shipped['post_ship_reversal'] = shipped['post_ship_lift'] <= 0
    shipped.to_csv(
        os.path.join(EXPORT_PATH, 'shipped_experiments_detail.csv'), index=False
    )

    # P-value data for histogram in Power BI
    pvalue_df = df[['experiment_id', 'experiment_name', 'team', 'feature_category',
                    'p_value', 'decision', 'true_effect_type', 'was_peeked']].copy()
    pvalue_df['p_value_bin'] = pd.cut(pvalue_df['p_value'], bins=np.arange(0, 1.05, 0.05))
    pvalue_df.to_csv(
        os.path.join(EXPORT_PATH, 'pvalue_distribution.csv'), index=False
    )

    print(f"Exported to {EXPORT_PATH}/")


def main():
    print("=" * 60)
    print("STAGE 2: FALSE DISCOVERY RATE ANALYSIS")
    print("=" * 60)

    df = load_data()

    # --- Method 1: Ground Truth ---
    result_1 = method_1_ground_truth_fdr(df)
    print(f"\n--- {result_1['method']} ---")
    print(f"  FDR: {result_1['fdr_estimate']:.0%}")
    print(f"  {result_1['interpretation']}")

    # --- Method 2: Benjamini-Hochberg ---
    result_2 = method_2_benjamini_hochberg(df)
    print(f"\n--- {result_2['method']} ---")
    print(f"  Significant before correction: {result_2['significant_before_correction']}")
    print(f"  Significant after correction:  {result_2['significant_after_correction']}")
    print(f"  Implied FDR: {result_2['implied_fdr']:.0%}")
    print(f"  {result_2['interpretation']}")

    # --- Method 3: Post-Ship Reversal ---
    result_3 = method_3_post_ship_reversal(df)
    print(f"\n--- {result_3['method']} ---")
    print(f"  FDR (reversal rate): {result_3['fdr_estimate']:.0%}")
    print(f"  {result_3['interpretation']}")

    # --- P-value Distribution ---
    pval_analysis = pvalue_distribution_analysis(df)
    print(f"\n--- P-value Distribution ---")
    print(f"  Significant at 0.05: {pval_analysis['significant_at_05']}")
    print(f"  Expected if all null: {pval_analysis['expected_significant_if_all_null']}")
    print(f"  Caliper ratio (0.04-0.05 vs 0.05-0.06): {pval_analysis['caliper_ratio_04_05_vs_05_06']}")
    if pval_analysis['ks_test_null_experiments']['p_value'] is not None:
        print(f"  KS test on null experiments: p={pval_analysis['ks_test_null_experiments']['p_value']:.4f}")

    # --- Export ---
    export_results(df, [result_1, result_2, result_3])

    print("\n" + "=" * 60)
    print("FINDINGS SUMMARY")
    print("=" * 60)
    print(f"""
  • Ground-truth FDR: {result_1['fdr_estimate']:.0%} of shipped experiments were false discoveries
  • BH correction would have caught {result_2['lost_to_correction']} of {result_2['significant_before_correction']} "significant" results
  • Post-ship reversal rate: {result_3['fdr_estimate']:.0%} showed no benefit in production
  • Caliper ratio: {pval_analysis['caliper_ratio_04_05_vs_05_06']} (>1.5 suggests p-hacking)
    """)


if __name__ == '__main__':
    main()
