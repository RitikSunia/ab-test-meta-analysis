"""
Stage 4: Peeking / P-hacking Detection

Key question: Is there evidence that experiments are being checked early
and stopped when results look favorable — inflating false positive rates?

Signals we look for:
1. P-value clustering just below 0.05 (caliper test)
2. Correlation between early stopping and significance
3. P-value distribution shape for null experiments (should be uniform)
4. Duration shortfall patterns
5. Decision-maker behavior differences

Outputs:
- Peeking evidence summary
- Exports for Power BI
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiments.csv')
EXPORT_PATH = os.path.join(os.path.dirname(__file__), '..', 'exports')


def load_data():
    return pd.read_csv(DATA_PATH)


def signal_1_caliper_test(df):
    """
    Caliper test: compare count of p-values just below 0.05 vs just above.
    Under no manipulation, these bins should have similar counts.
    A ratio > 1.5 suggests selective reporting or early stopping at significance.
    """
    p = df['p_value'].values

    # Narrow caliper (0.04-0.05 vs 0.05-0.06)
    just_below = np.sum((p >= 0.04) & (p < 0.05))
    just_above = np.sum((p >= 0.05) & (p < 0.06))
    narrow_ratio = just_below / just_above if just_above > 0 else float('inf')

    # Wide caliper (0.03-0.05 vs 0.05-0.07)
    below_wide = np.sum((p >= 0.03) & (p < 0.05))
    above_wide = np.sum((p >= 0.05) & (p < 0.07))
    wide_ratio = below_wide / above_wide if above_wide > 0 else float('inf')

    # Binomial test: under null, P(falling in [0.04,0.05]) = P(falling in [0.05,0.06])
    total_near = just_below + just_above
    if total_near > 0:
        binom_result = stats.binomtest(just_below, total_near, 0.5)
        binom_p = binom_result.pvalue
    else:
        binom_p = 1.0

    return {
        'just_below_05': int(just_below),
        'just_above_05': int(just_above),
        'narrow_caliper_ratio': round(narrow_ratio, 2),
        'wide_caliper_ratio': round(wide_ratio, 2),
        'binomial_test_p': round(binom_p, 4),
        'evidence_of_manipulation': narrow_ratio > 1.5,
        'interpretation': _interpret_caliper(narrow_ratio),
    }


def _interpret_caliper(ratio):
    if ratio > 2.0:
        return "Strong evidence of p-hacking or selective stopping"
    elif ratio > 1.5:
        return "Moderate evidence — warrants investigation"
    elif ratio > 1.2:
        return "Weak signal — possibly noise"
    else:
        return "No evidence of manipulation at the 0.05 boundary"


def signal_2_peeking_vs_significance(df):
    """
    Compare significance rates between peeked and non-peeked experiments.
    If peeking inflates significance, peeked experiments will have higher rates.
    """
    df_copy = df.copy()
    df_copy['is_significant'] = df_copy['p_value'] < 0.05

    peeked = df_copy[df_copy['was_peeked'] == True]
    not_peeked = df_copy[df_copy['was_peeked'] == False]

    sig_rate_peeked = peeked['is_significant'].mean()
    sig_rate_not_peeked = not_peeked['is_significant'].mean()

    # Fisher's exact test
    contingency = pd.crosstab(df_copy['was_peeked'], df_copy['is_significant'])
    if contingency.shape == (2, 2):
        odds_ratio, fisher_p = stats.fisher_exact(contingency)
    else:
        odds_ratio, fisher_p = 1.0, 1.0

    # Also check ship rates
    ship_rate_peeked = (peeked['decision'] == 'ship').mean()
    ship_rate_not_peeked = (not_peeked['decision'] == 'ship').mean()

    return {
        'n_peeked': len(peeked),
        'n_not_peeked': len(not_peeked),
        'sig_rate_peeked': round(sig_rate_peeked, 4),
        'sig_rate_not_peeked': round(sig_rate_not_peeked, 4),
        'sig_rate_difference': round(sig_rate_peeked - sig_rate_not_peeked, 4),
        'ship_rate_peeked': round(ship_rate_peeked, 4),
        'ship_rate_not_peeked': round(ship_rate_not_peeked, 4),
        'fisher_odds_ratio': round(odds_ratio, 3),
        'fisher_p_value': round(fisher_p, 4),
        'peeking_inflates_significance': sig_rate_peeked > sig_rate_not_peeked + 0.05,
    }


def signal_3_pvalue_uniformity(df):
    """
    Under the null hypothesis, p-values should follow Uniform(0,1).
    Test this on experiments where ground truth effect is zero.
    Deviation suggests the testing process is compromised.
    """
    null_experiments = df[df['true_effect_type'] == 'no_effect']
    null_pvalues = null_experiments['p_value'].dropna().values

    if len(null_pvalues) < 8:
        return {
            'n_null_experiments': len(null_experiments),
            'ks_statistic': None,
            'ks_p_value': None,
            'ks_rejects_uniform': None,
            'chi2_statistic': None,
            'chi2_p_value': None,
            'chi2_rejects_uniform': None,
            'null_p_value_bins': [],
            'interpretation': f"Too few null experiments ({len(null_pvalues)}) for reliable uniformity test"
        }

    # Kolmogorov-Smirnov test against uniform
    ks_stat, ks_p = stats.kstest(null_pvalues, 'uniform')

    # Chi-squared goodness of fit (binned)
    n_bins = min(10, len(null_pvalues) // 5)
    n_bins = max(n_bins, 4)
    observed_counts, _ = np.histogram(null_pvalues, bins=n_bins, range=(0, 1))
    expected_count = len(null_pvalues) / n_bins
    chi2_stat, chi2_p = stats.chisquare(observed_counts, f_exp=[expected_count]*n_bins)

    return {
        'n_null_experiments': len(null_experiments),
        'ks_statistic': round(ks_stat, 4),
        'ks_p_value': round(ks_p, 4),
        'ks_rejects_uniform': ks_p < 0.05,
        'chi2_statistic': round(chi2_stat, 4),
        'chi2_p_value': round(chi2_p, 4),
        'chi2_rejects_uniform': chi2_p < 0.05,
        'null_p_value_bins': observed_counts.tolist(),
        'interpretation': "P-values are uniform (no process issues)" if ks_p >= 0.05
                          else "P-values deviate from uniform — process may be compromised"
    }


def signal_4_duration_shortfall(df):
    """
    Analyze the pattern of duration shortfalls.
    Do experiments that stop early tend to have more favorable results?
    """
    df_copy = df.copy()
    df_copy['duration_ratio'] = df_copy['actual_duration_days'] / df_copy['planned_duration_days']
    df_copy['stopped_early'] = df_copy['duration_ratio'] < 0.85
    df_copy['is_significant'] = df_copy['p_value'] < 0.05

    early = df_copy[df_copy['stopped_early']]
    full = df_copy[~df_copy['stopped_early']]

    # Correlation between duration shortfall and p-value
    corr, corr_p = stats.pearsonr(df_copy['duration_ratio'], df_copy['p_value'])

    # Average lift comparison
    avg_lift_early = early['observed_lift_relative'].mean()
    avg_lift_full = full['observed_lift_relative'].mean()

    return {
        'n_stopped_early': len(early),
        'n_ran_full': len(full),
        'pct_stopped_early': round(len(early) / len(df_copy), 4),
        'median_duration_ratio_early': round(early['duration_ratio'].median(), 3),
        'sig_rate_early': round(early['is_significant'].mean(), 4),
        'sig_rate_full': round(full['is_significant'].mean(), 4),
        'avg_lift_early': round(avg_lift_early, 4),
        'avg_lift_full': round(avg_lift_full, 4),
        'duration_pvalue_correlation': round(corr, 4),
        'correlation_p_value': round(corr_p, 4),
        'early_stopping_biases_results': early['is_significant'].mean() > full['is_significant'].mean() + 0.05,
    }


def signal_5_decision_maker_patterns(df):
    """
    Do certain decision-makers ship at higher rates or with weaker evidence?
    """
    df_copy = df.copy()
    df_copy['is_significant'] = df_copy['p_value'] < 0.05

    by_decision_maker = df_copy.groupby('decision_maker').agg(
        n_decisions=('experiment_id', 'count'),
        ship_rate=('decision', lambda x: (x == 'ship').mean()),
        avg_p_value_when_shipped=('p_value', lambda x: x[df_copy.loc[x.index, 'decision'] == 'ship'].mean()),
        pct_shipped_without_significance=('experiment_id', lambda x: (
            (df_copy.loc[x.index, 'decision'] == 'ship') &
            (df_copy.loc[x.index, 'p_value'] >= 0.05)
        ).mean()),
    ).round(4)

    return by_decision_maker


def export_results(df, caliper, peeking_sig, uniformity, duration, decision_makers):
    """Export peeking detection data for Power BI."""
    os.makedirs(EXPORT_PATH, exist_ok=True)

    # Peeking summary
    summary = pd.DataFrame([{
        'signal': 'Caliper Test',
        'finding': f"Ratio: {caliper['narrow_caliper_ratio']}",
        'evidence_level': 'Strong' if caliper['evidence_of_manipulation'] else 'None',
        'interpretation': caliper['interpretation'],
    }, {
        'signal': 'Peeking vs Significance',
        'finding': f"Peeked sig rate: {peeking_sig['sig_rate_peeked']:.0%} vs Non-peeked: {peeking_sig['sig_rate_not_peeked']:.0%}",
        'evidence_level': 'Moderate' if peeking_sig['peeking_inflates_significance'] else 'None',
        'interpretation': f"Fisher p={peeking_sig['fisher_p_value']}",
    }, {
        'signal': 'P-value Uniformity (Null Only)',
        'finding': f"KS p={uniformity['ks_p_value']}",
        'evidence_level': 'Concerning' if uniformity['ks_rejects_uniform'] else 'Clean',
        'interpretation': uniformity['interpretation'],
    }, {
        'signal': 'Duration Shortfall Bias',
        'finding': f"Early sig rate: {duration['sig_rate_early']:.0%} vs Full: {duration['sig_rate_full']:.0%}",
        'evidence_level': 'Moderate' if duration['early_stopping_biases_results'] else 'None',
        'interpretation': f"Correlation: {duration['duration_pvalue_correlation']}",
    }])
    summary.to_csv(os.path.join(EXPORT_PATH, 'peeking_evidence_summary.csv'), index=False)

    # Experiment-level peeking data for Power BI scatter/bars
    peeking_detail = df[['experiment_id', 'experiment_name', 'team',
                         'was_peeked', 'p_value', 'decision',
                         'planned_duration_days', 'actual_duration_days',
                         'planned_n_per_group', 'actual_n_control']].copy()
    peeking_detail['duration_ratio'] = peeking_detail['actual_duration_days'] / peeking_detail['planned_duration_days']
    peeking_detail['sample_ratio'] = peeking_detail['actual_n_control'] / peeking_detail['planned_n_per_group']
    peeking_detail['is_significant'] = peeking_detail['p_value'] < 0.05
    peeking_detail.to_csv(os.path.join(EXPORT_PATH, 'peeking_detail.csv'), index=False)

    # Decision maker patterns
    decision_makers.to_csv(os.path.join(EXPORT_PATH, 'decision_maker_patterns.csv'))

    print(f"  Exported 3 files to {EXPORT_PATH}/")


def main():
    print("=" * 60)
    print("STAGE 4: PEEKING / P-HACKING DETECTION")
    print("=" * 60)

    df = load_data()

    # --- Signal 1: Caliper Test ---
    caliper = signal_1_caliper_test(df)
    print(f"\n--- Signal 1: Caliper Test (P-value Clustering) ---")
    print(f"  P-values in [0.04, 0.05): {caliper['just_below_05']}")
    print(f"  P-values in [0.05, 0.06): {caliper['just_above_05']}")
    print(f"  Narrow caliper ratio:     {caliper['narrow_caliper_ratio']}")
    print(f"  Binomial test p-value:    {caliper['binomial_test_p']}")
    print(f"  Verdict: {caliper['interpretation']}")

    # --- Signal 2: Peeking vs Significance ---
    peeking_sig = signal_2_peeking_vs_significance(df)
    print(f"\n--- Signal 2: Peeking Correlation with Significance ---")
    print(f"  Peeked experiments:       {peeking_sig['n_peeked']} ({peeking_sig['n_peeked']}/{peeking_sig['n_peeked']+peeking_sig['n_not_peeked']})")
    print(f"  Significance rate (peeked):     {peeking_sig['sig_rate_peeked']:.0%}")
    print(f"  Significance rate (not peeked): {peeking_sig['sig_rate_not_peeked']:.0%}")
    print(f"  Ship rate (peeked):             {peeking_sig['ship_rate_peeked']:.0%}")
    print(f"  Ship rate (not peeked):         {peeking_sig['ship_rate_not_peeked']:.0%}")
    print(f"  Fisher's exact test p:          {peeking_sig['fisher_p_value']}")
    print(f"  Verdict: {'Peeking inflates significance' if peeking_sig['peeking_inflates_significance'] else 'No significant inflation detected'}")

    # --- Signal 3: P-value Uniformity ---
    uniformity = signal_3_pvalue_uniformity(df)
    print(f"\n--- Signal 3: P-value Uniformity (Null Experiments) ---")
    print(f"  Null experiments tested:  {uniformity['n_null_experiments']}")
    print(f"  KS test statistic:        {uniformity['ks_statistic']}")
    print(f"  KS test p-value:          {uniformity['ks_p_value']}")
    print(f"  Chi-squared p-value:      {uniformity['chi2_p_value']}")
    print(f"  Verdict: {uniformity['interpretation']}")

    # --- Signal 4: Duration Shortfall ---
    duration = signal_4_duration_shortfall(df)
    print(f"\n--- Signal 4: Duration Shortfall Patterns ---")
    print(f"  Stopped early (<85% planned): {duration['n_stopped_early']} ({duration['pct_stopped_early']:.0%})")
    print(f"  Ran full duration:            {duration['n_ran_full']}")
    print(f"  Sig rate (early stopped):     {duration['sig_rate_early']:.0%}")
    print(f"  Sig rate (full run):          {duration['sig_rate_full']:.0%}")
    print(f"  Avg lift (early):             {duration['avg_lift_early']:+.2%}")
    print(f"  Avg lift (full):              {duration['avg_lift_full']:+.2%}")
    print(f"  Duration-pvalue correlation:  {duration['duration_pvalue_correlation']} (p={duration['correlation_p_value']})")
    print(f"  Verdict: {'Early stopping biases results' if duration['early_stopping_biases_results'] else 'No clear bias from early stopping'}")

    # --- Signal 5: Decision Maker Patterns ---
    decision_makers = signal_5_decision_maker_patterns(df)
    print(f"\n--- Signal 5: Decision Maker Behavior ---")
    print(decision_makers.to_string())

    # --- Export ---
    print(f"\n--- Exporting ---")
    export_results(df, caliper, peeking_sig, uniformity, duration, decision_makers)

    # --- Overall Verdict ---
    signals_positive = sum([
        bool(caliper['evidence_of_manipulation']),
        bool(peeking_sig['peeking_inflates_significance']),
        bool(uniformity['ks_rejects_uniform']),
        bool(duration['early_stopping_biases_results']),
    ])

    print("\n" + "=" * 60)
    print("FINDINGS SUMMARY")
    print("=" * 60)
    print(f"""
  Peeking/P-hacking Signals Detected: {signals_positive} of 4

  {'WARNING: Multiple signals suggest systematic peeking behavior.' if signals_positive >= 2
   else 'LIMITED EVIDENCE: Some peeking occurs but may not systematically bias outcomes.' if signals_positive == 1
   else 'CLEAN: No strong evidence of p-hacking or systematic peeking.'}

  Key facts:
  • {duration['pct_stopped_early']:.0%} of experiments stopped before reaching planned duration
  • Peeked experiments ship at {peeking_sig['ship_rate_peeked']:.0%} vs {peeking_sig['ship_rate_not_peeked']:.0%} for non-peeked
  • Caliper ratio: {caliper['narrow_caliper_ratio']} (>1.5 = concerning)

  RECOMMENDATION: {'Implement sequential testing (always-valid p-values) to allow safe peeking.' if signals_positive >= 1
   else 'Current practices appear sound, but monitor quarterly.'}
    """)


if __name__ == '__main__':
    main()
