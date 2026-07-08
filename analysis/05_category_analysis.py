"""
Stage 6: Category Win Rates + Org Learning Curve

Key questions:
1. Which experiment categories consistently produce winners?
2. Is the organization improving its experimentation practices over time?
3. What is the overall experimentation maturity score?

Outputs:
- Win rates by category and team
- Quarterly learning curve metrics
- Experimentation maturity score
- Exports for Power BI
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiments.csv')
EXPORT_PATH = os.path.join(os.path.dirname(__file__), '..', 'exports')

QUARTER_ORDER = ['2023-Q1', '2023-Q2', '2023-Q3', '2023-Q4', '2024-Q1', '2024-Q2']


def load_data():
    df = pd.read_csv(DATA_PATH)
    df['is_significant'] = df['p_value'] < 0.05
    df['was_shipped'] = df['decision'] == 'ship'
    df['had_real_effect'] = df['true_effect_type'].isin(['small_positive', 'medium_positive'])
    return df


def category_win_rates(df):
    """Win rates and performance metrics by feature category."""
    summary = df.groupby('feature_category').agg(
        total_experiments=('experiment_id', 'count'),
        ship_count=('was_shipped', 'sum'),
        ship_rate=('was_shipped', 'mean'),
        significance_rate=('is_significant', 'mean'),
        kill_rate=('decision', lambda x: (x == 'kill').mean()),
        inconclusive_rate=('decision', lambda x: (x == 'inconclusive').mean()),
        avg_lift_when_shipped=('observed_lift_relative', lambda x: x[df.loc[x.index, 'was_shipped']].mean()),
        avg_true_effect=('true_effect', 'mean'),
        real_positive_rate=('had_real_effect', 'mean'),
        median_power=('statistical_power', 'median'),
        peeking_rate=('was_peeked', 'mean'),
    ).round(4)

    summary = summary.sort_values('ship_rate', ascending=False)
    summary['ship_rate_pct'] = (summary['ship_rate'] * 100).round(1)
    summary['significance_rate_pct'] = (summary['significance_rate'] * 100).round(1)

    return summary


def team_win_rates(df):
    """Win rates and performance metrics by team."""
    summary = df.groupby('team').agg(
        total_experiments=('experiment_id', 'count'),
        ship_count=('was_shipped', 'sum'),
        ship_rate=('was_shipped', 'mean'),
        significance_rate=('is_significant', 'mean'),
        avg_lift_when_shipped=('observed_lift_relative', lambda x: x[df.loc[x.index, 'was_shipped']].mean()),
        avg_true_effect=('true_effect', 'mean'),
        real_positive_rate=('had_real_effect', 'mean'),
        median_power=('statistical_power', 'median'),
        peeking_rate=('was_peeked', 'mean'),
    ).round(4)

    return summary.sort_values('ship_rate', ascending=False)


def chi_squared_category_test(df):
    """
    Test whether ship rates differ significantly across categories.
    Null: ship rate is the same for all categories.
    """
    contingency = pd.crosstab(df['feature_category'], df['was_shipped'])
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

    return {
        'chi2_statistic': round(chi2, 4),
        'p_value': round(p_value, 4),
        'degrees_of_freedom': dof,
        'significant_difference': p_value < 0.05,
        'interpretation': (
            'Ship rates differ significantly across categories'
            if p_value < 0.05
            else 'No statistically significant difference in ship rates across categories'
        ),
    }


def category_vs_truth(df):
    """
    Compare observed ship rate to underlying true positive rate by category.
    Reveals which categories have high potential but poor detection.
    """
    summary = df.groupby('feature_category').agg(
        real_positive_rate=('had_real_effect', 'mean'),
        ship_rate=('was_shipped', 'mean'),
        detection_gap=('had_real_effect', 'mean'),  # placeholder, fixed below
    )

    summary['detection_gap'] = summary['real_positive_rate'] - summary['ship_rate']
    summary['detection_efficiency'] = (
        summary['ship_rate'] / summary['real_positive_rate']
    ).replace([np.inf, -np.inf], np.nan).round(4)

    return summary.sort_values('detection_gap', ascending=False)


def org_learning_curve(df):
    """
    Track experimentation quality metrics over quarters.
    Is the org getting better at running and interpreting tests?
    """
    df_ordered = df.copy()
    df_ordered['quarter'] = pd.Categorical(
        df_ordered['quarter'], categories=QUARTER_ORDER, ordered=True
    )

    curve = df_ordered.groupby('quarter', observed=False).agg(
        n_experiments=('experiment_id', 'count'),
        ship_rate=('was_shipped', 'mean'),
        significance_rate=('is_significant', 'mean'),
        median_power=('statistical_power', 'median'),
        mean_power=('statistical_power', 'mean'),
        peeking_rate=('was_peeked', 'mean'),
        avg_sample_size=('actual_n_control', 'mean'),
        avg_duration_days=('actual_duration_days', 'mean'),
        real_positive_rate=('had_real_effect', 'mean'),
        avg_lift_observed=('observed_lift_relative', 'mean'),
    ).round(4)

    curve = curve.reset_index()

    # Trend: linear regression slope for key metrics over time
    x = np.arange(len(curve))
    trends = {}
    for metric in ['ship_rate', 'median_power', 'peeking_rate', 'significance_rate']:
        y = curve[metric].values.astype(float)
        if len(y) >= 3 and not np.all(np.isnan(y)):
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            trends[metric] = {
                'slope_per_quarter': round(slope, 4),
                'r_squared': round(r_value ** 2, 4),
                'trend_p_value': round(p_value, 4),
                'direction': 'improving' if slope > 0 and metric != 'peeking_rate'
                              else 'worsening' if slope < 0 and metric != 'peeking_rate'
                              else 'improving' if slope < 0 and metric == 'peeking_rate'
                              else 'worsening',
            }
        else:
            trends[metric] = {'slope_per_quarter': None, 'direction': 'insufficient_data'}

    return curve, trends


def experimentation_maturity_score(df):
    """
    Composite score (0-100) measuring experimentation program health.
    Components:
    - Power adequacy (30%)
    - Ship decision quality (25%)
    - Process discipline - low peeking (20%)
    - Detection efficiency (15%)
    - Sample size compliance (10%)
    """
    # Power adequacy: % of experiments with >= 50% power (scaled to 80% target)
    power_score = min((df['statistical_power'] >= 0.50).mean() / 0.80, 1.0) * 100

    # Ship decision quality: of real positives, what % were shipped
    real_positives = df[df['had_real_effect']]
    ship_quality = (real_positives['was_shipped'].mean() if len(real_positives) > 0 else 0) * 100

    # Process discipline: inverse of peeking rate
    peeking_score = (1 - df['was_peeked'].mean()) * 100

    # Detection efficiency: shipped real positives / total real positives
    detection_score = ship_quality  # same metric, different weight

    # Sample size compliance: actual vs planned
    df_copy = df.copy()
    df_copy['sample_ratio'] = df_copy['actual_n_control'] / df_copy['planned_n_per_group']
    sample_score = min(df_copy['sample_ratio'].median(), 1.0) * 100

    components = {
        'power_adequacy': round(power_score * 0.30, 1),
        'ship_decision_quality': round(ship_quality * 0.25, 1),
        'process_discipline': round(peeking_score * 0.20, 1),
        'detection_efficiency': round(detection_score * 0.15, 1),
        'sample_size_compliance': round(sample_score * 0.10, 1),
    }

    total_score = round(sum(components.values()), 1)

    maturity_level = (
        'Mature' if total_score >= 70
        else 'Developing' if total_score >= 50
        else 'Early Stage' if total_score >= 30
        else 'Critical'
    )

    return {
        'total_score': total_score,
        'maturity_level': maturity_level,
        'components': components,
        'raw_metrics': {
            'pct_power_above_50': round((df['statistical_power'] >= 0.50).mean(), 4),
            'real_positive_ship_rate': round(ship_quality / 100, 4),
            'peeking_rate': round(df['was_peeked'].mean(), 4),
            'median_sample_ratio': round(df_copy['sample_ratio'].median(), 4),
        },
    }


def category_recommendations(category_summary, category_truth):
    """Generate actionable recommendations per category."""
    recs = []

    for category in category_summary.index:
        row = category_summary.loc[category]
        truth = category_truth.loc[category]

        if row['median_power'] < 0.30:
            recs.append({
                'category': category,
                'priority': 'High',
                'issue': 'Severely underpowered',
                'recommendation': f'Increase sample sizes — median power is only {row["median_power"]:.0%}',
            })
        elif truth['detection_efficiency'] < 0.25 and truth['real_positive_rate'] > 0.35:
            recs.append({
                'category': category,
                'priority': 'High',
                'issue': 'High potential, low detection',
                'recommendation': f'{truth["real_positive_rate"]:.0%} real positives but only {row["ship_rate"]:.0%} shipped — review decision criteria',
            })
        elif row['peeking_rate'] > 0.50:
            recs.append({
                'category': category,
                'priority': 'Medium',
                'issue': 'High peeking rate',
                'recommendation': f'{row["peeking_rate"]:.0%} of experiments peeked — implement sequential testing',
            })
        elif row['ship_rate'] > 0.20:
            recs.append({
                'category': category,
                'priority': 'Low',
                'issue': 'Strong performer',
                'recommendation': f'Continue investing — {row["ship_rate"]:.0%} ship rate with {row["avg_lift_when_shipped"]:.1%} avg lift',
            })

    return pd.DataFrame(recs)


def export_results(category_summary, team_summary, chi2_result, category_truth,
                   learning_curve, trends, maturity, recommendations):
    """Export category and learning curve data for Power BI."""
    os.makedirs(EXPORT_PATH, exist_ok=True)

    category_summary.to_csv(os.path.join(EXPORT_PATH, 'category_win_rates.csv'))
    team_summary.to_csv(os.path.join(EXPORT_PATH, 'team_win_rates.csv'))
    category_truth.to_csv(os.path.join(EXPORT_PATH, 'category_detection_efficiency.csv'))
    learning_curve.to_csv(os.path.join(EXPORT_PATH, 'org_learning_curve.csv'), index=False)

    pd.DataFrame([{
        'chi2_statistic': chi2_result['chi2_statistic'],
        'p_value': chi2_result['p_value'],
        'significant_difference': chi2_result['significant_difference'],
        'interpretation': chi2_result['interpretation'],
    }]).to_csv(os.path.join(EXPORT_PATH, 'category_chi_squared_test.csv'), index=False)

    maturity_rows = [{'component': k, 'weighted_score': v} for k, v in maturity['components'].items()]
    maturity_rows.append({'component': 'TOTAL', 'weighted_score': maturity['total_score']})
    pd.DataFrame(maturity_rows).to_csv(os.path.join(EXPORT_PATH, 'maturity_score.csv'), index=False)

    pd.DataFrame([{
        'total_score': maturity['total_score'],
        'maturity_level': maturity['maturity_level'],
        **maturity['raw_metrics'],
    }]).to_csv(os.path.join(EXPORT_PATH, 'maturity_summary.csv'), index=False)

    trends_df = pd.DataFrame([
        {'metric': k, **v} for k, v in trends.items()
    ])
    trends_df.to_csv(os.path.join(EXPORT_PATH, 'learning_curve_trends.csv'), index=False)

    if len(recommendations) > 0:
        recommendations.to_csv(os.path.join(EXPORT_PATH, 'category_recommendations.csv'), index=False)

    print(f"  Exported up to 10 files to {EXPORT_PATH}/")


def main():
    print("=" * 60)
    print("STAGE 6: CATEGORY WIN RATES + ORG LEARNING CURVE")
    print("=" * 60)

    df = load_data()

    # --- Category Win Rates ---
    category_summary = category_win_rates(df)
    print(f"\n--- Win Rates by Feature Category ---")
    print(category_summary[['total_experiments', 'ship_rate_pct', 'significance_rate_pct',
                            'median_power', 'peeking_rate', 'avg_lift_when_shipped']].to_string())

    # --- Team Win Rates ---
    team_summary = team_win_rates(df)
    print(f"\n--- Win Rates by Team ---")
    print(team_summary[['total_experiments', 'ship_rate', 'significance_rate',
                        'median_power', 'peeking_rate']].to_string())

    # --- Chi-squared Test ---
    chi2_result = chi_squared_category_test(df)
    print(f"\n--- Chi-Squared Test (Category Ship Rates) ---")
    print(f"  Chi2 statistic:  {chi2_result['chi2_statistic']}")
    print(f"  P-value:         {chi2_result['p_value']}")
    print(f"  Verdict:         {chi2_result['interpretation']}")

    # --- Detection Efficiency ---
    category_truth = category_vs_truth(df)
    print(f"\n--- Detection Efficiency by Category ---")
    print(f"  (Real positive rate vs ship rate — gap = missed opportunity)")
    print(category_truth[['real_positive_rate', 'ship_rate', 'detection_gap', 'detection_efficiency']].to_string())

    # --- Learning Curve ---
    learning_curve, trends = org_learning_curve(df)
    print(f"\n--- Org Learning Curve (by Quarter) ---")
    print(learning_curve[['quarter', 'n_experiments', 'ship_rate', 'median_power',
                          'peeking_rate', 'significance_rate']].to_string(index=False))

    print(f"\n--- Trend Analysis ---")
    for metric, trend in trends.items():
        if trend.get('slope_per_quarter') is not None:
            print(f"  {metric:<22} slope: {trend['slope_per_quarter']:+.4f}/quarter | "
                  f"R²: {trend['r_squared']:.3f} | {trend['direction']}")
        else:
            print(f"  {metric:<22} insufficient data")

    # --- Maturity Score ---
    maturity = experimentation_maturity_score(df)
    print(f"\n--- Experimentation Maturity Score ---")
    print(f"  Overall Score:  {maturity['total_score']}/100 ({maturity['maturity_level']})")
    print(f"  Components:")
    for component, score in maturity['components'].items():
        print(f"    {component:<25} {score}")

    # --- Recommendations ---
    recommendations = category_recommendations(category_summary, category_truth)
    if len(recommendations) > 0:
        print(f"\n--- Category Recommendations ---")
        for _, rec in recommendations.iterrows():
            print(f"  [{rec['priority']}] {rec['category']}: {rec['recommendation']}")

    # --- Export ---
    print(f"\n--- Exporting ---")
    export_results(category_summary, team_summary, chi2_result, category_truth,
                   learning_curve, trends, maturity, recommendations)

    # --- Summary ---
    best_category = category_summary.index[0]
    worst_power_category = category_summary['median_power'].idxmin()

    print("\n" + "=" * 60)
    print("FINDINGS SUMMARY")
    print("=" * 60)
    print(f"""
  Category Insights:
  • Best ship rate: {best_category} ({category_summary.loc[best_category, 'ship_rate']:.0%})
  • Lowest power:   {worst_power_category} ({category_summary.loc[worst_power_category, 'median_power']:.0%} median)
  • Chi-squared:    {'Significant' if chi2_result['significant_difference'] else 'No significant'} difference across categories

  Org Learning:
  • Power trend:        {trends.get('median_power', {}).get('direction', 'N/A')}
  • Peeking trend:      {trends.get('peeking_rate', {}).get('direction', 'N/A')}
  • Ship rate trend:    {trends.get('ship_rate', {}).get('direction', 'N/A')}

  Maturity Score: {maturity['total_score']}/100 ({maturity['maturity_level']})

  RECOMMENDATION: Focus experimentation investment on categories with
  high real-positive rates but low detection efficiency. Use the maturity
  score as a quarterly KPI to track program improvement.
    """)


if __name__ == '__main__':
    main()
