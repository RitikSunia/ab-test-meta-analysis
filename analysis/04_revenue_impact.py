"""
Stage 5: Revenue Left on the Table

Key question: How much annual revenue did bad experimentation practices cost
a media/content platform?

Scenarios quantified:
1. Real winners missed due to peeking / early stopping
2. Real winners missed due to underpowering
3. Value already captured from shipped winners
4. Potential value if experimentation program ran at 80% power

Outputs:
- Revenue waterfall summary
- Experiment-level opportunity cost detail
- Exports for Power BI
"""

import os
import numpy as np
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiments.csv')
EXPORT_PATH = os.path.join(os.path.dirname(__file__), '..', 'exports')

# --- Business assumptions for a mid-size media/content platform ---
# These are documented assumptions you can tune in Power BI or here.
BUSINESS_ASSUMPTIONS = {
    'monthly_active_users': 2_500_000,
    'monthly_revenue_usd': 8_500_000,          # subscriptions + ads
    'annual_revenue_usd': 8_500_000 * 12,
    'avg_subscription_value_annual': 72,        # $6/month plan
    'avg_ad_revenue_per_user_annual': 18,       # display + video ads
    'experiments_per_year': 100,
    'avg_experiment_traffic_share': 0.15,       # 15% of MAU exposed per test
}

# How each metric type translates to revenue impact
METRIC_REVENUE_MODEL = {
    'signup_conversion': {
        'label': 'New subscriber acquisition',
        'revenue_per_unit_lift': BUSINESS_ASSUMPTIONS['avg_subscription_value_annual'],
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 0.02,  # 2% new signups/month
    },
    'trial_start_rate': {
        'label': 'Trial starts',
        'revenue_per_unit_lift': BUSINESS_ASSUMPTIONS['avg_subscription_value_annual'] * 0.35,  # 35% trial-to-paid
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 0.03,
    },
    'referral_rate': {
        'label': 'Referral signups',
        'revenue_per_unit_lift': BUSINESS_ASSUMPTIONS['avg_subscription_value_annual'] * 0.5,
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 0.005,
    },
    'article_completion_rate': {
        'label': 'Article completions (ad inventory)',
        'revenue_per_unit_lift': BUSINESS_ASSUMPTIONS['avg_ad_revenue_per_user_annual'] / 12 / 30,
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 20,  # 20 articles/user/month
    },
    'session_duration_above_5min': {
        'label': 'Engaged sessions',
        'revenue_per_unit_lift': BUSINESS_ASSUMPTIONS['avg_ad_revenue_per_user_annual'] / 12 / 10,
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 8,
    },
    'daily_active_rate': {
        'label': 'Daily active users',
        'revenue_per_unit_lift': BUSINESS_ASSUMPTIONS['avg_ad_revenue_per_user_annual'] / 365,
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'],
    },
    'subscription_conversion': {
        'label': 'Subscription conversions',
        'revenue_per_unit_lift': BUSINESS_ASSUMPTIONS['avg_subscription_value_annual'],
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 0.015,
    },
    'ad_click_rate': {
        'label': 'Ad clicks',
        'revenue_per_unit_lift': 0.45,  # avg CPC
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 50,
    },
    'upsell_rate': {
        'label': 'Premium upsells',
        'revenue_per_unit_lift': 48,  # annual premium delta
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 0.01,
    },
    'content_click_through': {
        'label': 'Content clicks',
        'revenue_per_unit_lift': BUSINESS_ASSUMPTIONS['avg_ad_revenue_per_user_annual'] / 12 / 40,
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 30,
    },
    'watch_completion_rate': {
        'label': 'Video completions',
        'revenue_per_unit_lift': BUSINESS_ASSUMPTIONS['avg_ad_revenue_per_user_annual'] / 12 / 15,
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 12,
    },
    'playlist_add_rate': {
        'label': 'Playlist adds (retention proxy)',
        'revenue_per_unit_lift': BUSINESS_ASSUMPTIONS['avg_subscription_value_annual'] * 0.15,
        'monthly_units': BUSINESS_ASSUMPTIONS['monthly_active_users'] * 0.05,
    },
}


def load_data():
    return pd.read_csv(DATA_PATH)


def estimate_annual_revenue_impact(row):
    """
    Estimate annual revenue impact of a true effect for one experiment.
    Uses relative lift applied to monthly units affected by the metric.
    """
    metric = row['primary_metric']
    model = METRIC_REVENUE_MODEL.get(metric)

    if model is None:
        return 0.0

    relative_lift = row['true_effect']
    monthly_units = model['monthly_units']
    revenue_per_unit = model['revenue_per_unit_lift']

    # Traffic share: only users exposed to the experiment benefit
    traffic_share = BUSINESS_ASSUMPTIONS['avg_experiment_traffic_share']

    additional_monthly_units = monthly_units * relative_lift * traffic_share
    annual_revenue = additional_monthly_units * revenue_per_unit * 12

    return max(annual_revenue, 0.0)


def build_opportunity_detail(df):
    """Calculate per-experiment revenue opportunity for all real positive effects."""
    real_positives = df[df['true_effect_type'].isin(['small_positive', 'medium_positive'])].copy()
    real_positives['annual_revenue_opportunity'] = real_positives.apply(estimate_annual_revenue_impact, axis=1)
    real_positives['was_shipped'] = real_positives['decision'] == 'ship'
    real_positives['missed_due_to_peeking'] = (
        (~real_positives['was_shipped']) & (real_positives['was_peeked'] == True)
    )
    real_positives['missed_due_to_underpowering'] = (
        (~real_positives['was_shipped']) & (real_positives['statistical_power'] < 0.50)
    )
    real_positives['missed_due_to_bad_luck'] = (
        (~real_positives['was_shipped']) &
        (~real_positives['missed_due_to_peeking']) &
        (~real_positives['missed_due_to_underpowering'])
    )

    return real_positives


def revenue_waterfall(df, opportunity_df):
    """Build the revenue waterfall: total opportunity -> captured -> lost."""
    total_opportunity = opportunity_df['annual_revenue_opportunity'].sum()

    captured = opportunity_df[opportunity_df['was_shipped']]['annual_revenue_opportunity'].sum()

    missed_peeking = opportunity_df[opportunity_df['missed_due_to_peeking']]['annual_revenue_opportunity'].sum()
    missed_underpowered = opportunity_df[
        opportunity_df['missed_due_to_underpowering'] & ~opportunity_df['missed_due_to_peeking']
    ]['annual_revenue_opportunity'].sum()
    missed_other = opportunity_df[opportunity_df['missed_due_to_bad_luck']]['annual_revenue_opportunity'].sum()

    total_missed = missed_peeking + missed_underpowered + missed_other

    # Post-ship degradation: shipped experiments where production lift < 50% of test lift
    shipped = df[df['decision'] == 'ship'].copy()
    shipped['production_lift'] = shipped['post_ship_lift']
    shipped['test_lift'] = shipped['true_effect']
    shipped['lift_retention'] = shipped['production_lift'] / shipped['test_lift']
    shipped['annual_revenue_at_test'] = shipped.apply(estimate_annual_revenue_impact, axis=1)

    degradation_loss = 0.0
    for _, row in shipped.iterrows():
        if pd.notna(row['production_lift']) and row['production_lift'] < row['test_lift']:
            full_value = row['annual_revenue_at_test']
            actual_value = full_value * (row['production_lift'] / row['test_lift'])
            degradation_loss += (full_value - actual_value)

    # Potential at 80% power: ~80% of total opportunity captured
    potential_at_80_power = total_opportunity * 0.80
    additional_at_80_power = potential_at_80_power - captured

    waterfall = pd.DataFrame([
        {'category': 'Total Revenue Opportunity (All Real Winners)', 'amount_usd': round(total_opportunity, 0), 'type': 'total'},
        {'category': 'Revenue Captured (Shipped Winners)', 'amount_usd': round(captured, 0), 'type': 'captured'},
        {'category': 'Lost: Missed Due to Peeking', 'amount_usd': round(missed_peeking, 0), 'type': 'loss'},
        {'category': 'Lost: Missed Due to Underpowering', 'amount_usd': round(missed_underpowered, 0), 'type': 'loss'},
        {'category': 'Lost: Missed (Sampling Noise / Other)', 'amount_usd': round(missed_other, 0), 'type': 'loss'},
        {'category': 'Lost: Post-Ship Lift Degradation', 'amount_usd': round(degradation_loss, 0), 'type': 'loss'},
        {'category': 'Net Captured After Degradation', 'amount_usd': round(captured - degradation_loss, 0), 'type': 'net'},
        {'category': 'Potential at 80% Power Program', 'amount_usd': round(potential_at_80_power, 0), 'type': 'potential'},
        {'category': 'Additional Upside at 80% Power', 'amount_usd': round(additional_at_80_power, 0), 'type': 'upside'},
    ])

    summary = {
        'total_opportunity_usd': round(total_opportunity, 0),
        'captured_usd': round(captured, 0),
        'total_missed_usd': round(total_missed, 0),
        'missed_peeking_usd': round(missed_peeking, 0),
        'missed_underpowered_usd': round(missed_underpowered, 0),
        'missed_other_usd': round(missed_other, 0),
        'degradation_loss_usd': round(degradation_loss, 0),
        'capture_rate': round(captured / total_opportunity, 4) if total_opportunity > 0 else 0,
        'potential_at_80_power_usd': round(potential_at_80_power, 0),
        'additional_at_80_power_usd': round(additional_at_80_power, 0),
        'pct_of_annual_revenue_missed': round(total_missed / BUSINESS_ASSUMPTIONS['annual_revenue_usd'], 4),
    }

    return waterfall, summary


def revenue_by_group(opportunity_df):
    """Break down missed revenue by team, category, and quarter."""
    missed = opportunity_df[~opportunity_df['was_shipped']]

    results = {}
    for group_col in ['team', 'feature_category', 'quarter']:
        grouped = missed.groupby(group_col).agg(
            missed_experiments=('experiment_id', 'count'),
            missed_revenue_usd=('annual_revenue_opportunity', 'sum'),
            avg_true_effect=('true_effect', 'mean'),
            avg_power=('statistical_power', 'mean'),
        ).round(2)
        grouped = grouped.sort_values('missed_revenue_usd', ascending=False)
        results[group_col] = grouped

    return results


def top_missed_opportunities(opportunity_df, n=10):
    """Top missed revenue opportunities for executive attention."""
    missed = opportunity_df[~opportunity_df['was_shipped']].copy()
    missed = missed.sort_values('annual_revenue_opportunity', ascending=False)

    return missed[[
        'experiment_id', 'experiment_name', 'team', 'feature_category',
        'primary_metric', 'true_effect', 'statistical_power', 'was_peeked',
        'p_value', 'decision', 'annual_revenue_opportunity',
        'missed_due_to_peeking', 'missed_due_to_underpowering',
    ]].head(n)


def export_results(waterfall, summary, opportunity_df, by_group, top_missed, assumptions):
    """Export revenue impact data for Power BI."""
    os.makedirs(EXPORT_PATH, exist_ok=True)

    waterfall.to_csv(os.path.join(EXPORT_PATH, 'revenue_waterfall.csv'), index=False)
    pd.DataFrame([summary]).to_csv(os.path.join(EXPORT_PATH, 'revenue_summary.csv'), index=False)
    pd.DataFrame([assumptions]).to_csv(os.path.join(EXPORT_PATH, 'business_assumptions.csv'), index=False)

    opportunity_df.to_csv(os.path.join(EXPORT_PATH, 'revenue_opportunity_detail.csv'), index=False)
    top_missed.to_csv(os.path.join(EXPORT_PATH, 'top_missed_opportunities.csv'), index=False)

    for group_name, group_df in by_group.items():
        group_df.to_csv(os.path.join(EXPORT_PATH, f'revenue_missed_by_{group_name}.csv'))

    print(f"  Exported 8 files to {EXPORT_PATH}/")


def format_usd(amount):
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:.0f}"


def main():
    print("=" * 60)
    print("STAGE 5: REVENUE LEFT ON THE TABLE")
    print("=" * 60)

    df = load_data()

    print(f"\n--- Business Assumptions ---")
    print(f"  Monthly active users:     {BUSINESS_ASSUMPTIONS['monthly_active_users']:,}")
    print(f"  Monthly revenue:          {format_usd(BUSINESS_ASSUMPTIONS['monthly_revenue_usd'])}")
    print(f"  Annual revenue:           {format_usd(BUSINESS_ASSUMPTIONS['annual_revenue_usd'])}")
    print(f"  Avg experiment traffic:   {BUSINESS_ASSUMPTIONS['avg_experiment_traffic_share']:.0%} of MAU")

    # --- Per-experiment opportunity ---
    opportunity_df = build_opportunity_detail(df)
    print(f"\n--- Revenue Opportunity (Real Positive Experiments) ---")
    print(f"  Real positive experiments:  {len(opportunity_df)}")
    print(f"  Total annual opportunity:   {format_usd(opportunity_df['annual_revenue_opportunity'].sum())}")
    print(f"  Shipped (captured):         {format_usd(opportunity_df[opportunity_df['was_shipped']]['annual_revenue_opportunity'].sum())}")
    print(f"  Missed:                     {format_usd(opportunity_df[~opportunity_df['was_shipped']]['annual_revenue_opportunity'].sum())}")

    # --- Waterfall ---
    waterfall, summary = revenue_waterfall(df, opportunity_df)
    print(f"\n--- Revenue Waterfall ---")
    for _, row in waterfall.iterrows():
        print(f"  {row['category']:<45} {format_usd(row['amount_usd'])}")

    print(f"\n--- Key Metrics ---")
    print(f"  Capture rate:               {summary['capture_rate']:.0%}")
    print(f"  Missed as % of annual rev:  {summary['pct_of_annual_revenue_missed']:.2%}")
    print(f"  Potential at 80% power:     {format_usd(summary['potential_at_80_power_usd'])}")
    print(f"  Additional upside:          {format_usd(summary['additional_at_80_power_usd'])}")

    # --- By Group ---
    by_group = revenue_by_group(opportunity_df)
    print(f"\n--- Missed Revenue by Team ---")
    print(by_group['team'].to_string())
    print(f"\n--- Missed Revenue by Category ---")
    print(by_group['feature_category'].to_string())

    # --- Top Missed ---
    top_missed = top_missed_opportunities(opportunity_df)
    print(f"\n--- Top 5 Missed Opportunities ---")
    for _, row in top_missed.head(5).iterrows():
        print(f"  {row['experiment_id']} | {row['experiment_name'][:40]:<40} | "
              f"+{row['true_effect']:.1%} | {format_usd(row['annual_revenue_opportunity'])}")

    # --- Export ---
    print(f"\n--- Exporting ---")
    export_results(waterfall, summary, opportunity_df, by_group, top_missed, BUSINESS_ASSUMPTIONS)

    print("\n" + "=" * 60)
    print("FINDINGS SUMMARY")
    print("=" * 60)
    print(f"""
  This media platform left {format_usd(summary['total_missed_usd'])} on the table annually.

  Breakdown of losses:
  • Peeking / early stopping:  {format_usd(summary['missed_peeking_usd'])}
  • Underpowering:             {format_usd(summary['missed_underpowered_usd'])}
  • Other (sampling noise):    {format_usd(summary['missed_other_usd'])}
  • Post-ship degradation:     {format_usd(summary['degradation_loss_usd'])}

  Only {summary['capture_rate']:.0%} of available revenue opportunity was captured.
  Fixing the experimentation program to 80% power could unlock
  an additional {format_usd(summary['additional_at_80_power_usd'])} per year.

  RECOMMENDATION: Present this waterfall to leadership as the ROI case
  for investing in experimentation infrastructure and governance.
    """)


if __name__ == '__main__':
    main()
