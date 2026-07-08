"""
Generate a realistic corpus of A/B test experiments for a media/content platform.

Context: A streaming + news media company running experiments on engagement,
subscriptions, ad revenue, and content recommendations.

Run this script to produce 'experiments.csv' in the same folder.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
from scipy import stats
from analysis.utils import two_proportion_z_test, calculate_power

SEED = 42
N_EXPERIMENTS = 100

# --- Domain Configuration (Media / Content Platform) ---

TEAMS = ['Growth', 'Engagement', 'Monetization', 'Content-Algo']

FEATURE_CATEGORIES = [
    'UI/UX',
    'Recommendation-Algo',
    'Pricing/Paywall',
    'Content-Format',
    'Notifications',
    'Onboarding-Flow',
]

METRICS = {
    'Growth': {
        'primary_metrics': ['signup_conversion', 'trial_start_rate', 'referral_rate'],
        'base_rates': [0.08, 0.12, 0.03],
    },
    'Engagement': {
        'primary_metrics': ['article_completion_rate', 'session_duration_above_5min', 'daily_active_rate'],
        'base_rates': [0.35, 0.28, 0.45],
    },
    'Monetization': {
        'primary_metrics': ['subscription_conversion', 'ad_click_rate', 'upsell_rate'],
        'base_rates': [0.04, 0.015, 0.06],
    },
    'Content-Algo': {
        'primary_metrics': ['content_click_through', 'watch_completion_rate', 'playlist_add_rate'],
        'base_rates': [0.22, 0.40, 0.08],
    },
}

EXPERIMENT_NAMES = {
    'UI/UX': [
        'Dark mode default for night readers',
        'Floating video player on scroll',
        'Simplified article header layout',
        'Bottom nav bar redesign',
        'Reading progress indicator',
        'Card-based feed vs list view',
    ],
    'Recommendation-Algo': [
        'Collaborative filtering v2 rollout',
        'Cold-start user recs via trending',
        'Diversity injection in feed (20%)',
        'Time-decay weighting for recency',
        'Cross-category recommendations',
        'Similar-author suggestions widget',
    ],
    'Pricing/Paywall': [
        'Annual plan discount (30% vs 20%)',
        'Soft paywall at 5 articles vs 3',
        'Free weekend pass experiment',
        'Student tier pricing test',
        'Remove ads upsell placement',
        'Trial extension offer at day 6',
    ],
    'Content-Format': [
        'Short-form video summaries on articles',
        'Audio narration toggle for articles',
        'Interactive data viz in reports',
        'Newsletter digest format change',
        'Headline A/B: question vs statement',
        'Thumbnail size increase (1.5x)',
    ],
    'Notifications': [
        'Push notification frequency (2x vs 1x daily)',
        'Personalized send-time optimization',
        'Breaking news vs digest bundling',
        'Re-engagement push after 3 days inactive',
        'Email subject line: emoji vs no emoji',
        'In-app notification center redesign',
    ],
    'Onboarding-Flow': [
        'Topic preference quiz at signup',
        'Skip onboarding option test',
        'Guided tour vs self-explore',
        'Social proof (X readers joined today)',
        'Onboarding email drip: 3-day vs 7-day',
        'First-session content sampler',
    ],
}

QUARTERS = ['2023-Q1', '2023-Q2', '2023-Q3', '2023-Q4', '2024-Q1', '2024-Q2']


def generate_experiment_corpus(n=N_EXPERIMENTS, seed=SEED):
    np.random.seed(seed)
    experiments = []

    for i in range(n):
        team = np.random.choice(TEAMS)
        category = np.random.choice(FEATURE_CATEGORIES)
        quarter = np.random.choice(QUARTERS)

        metric_idx = np.random.randint(len(METRICS[team]['primary_metrics']))
        primary_metric = METRICS[team]['primary_metrics'][metric_idx]
        base_rate = METRICS[team]['base_rates'][metric_idx]

        names = EXPERIMENT_NAMES.get(category, EXPERIMENT_NAMES['UI/UX'])
        experiment_name = np.random.choice(names)

        # --- Ground truth: most experiments have no real effect ---
        true_effect_type = np.random.choice(
            ['no_effect', 'small_positive', 'medium_positive', 'negative'],
            p=[0.52, 0.25, 0.12, 0.11]
        )
        true_effect = {
            'no_effect': 0.0,
            'small_positive': np.random.uniform(0.02, 0.05),
            'medium_positive': np.random.uniform(0.05, 0.12),
            'negative': np.random.uniform(-0.08, -0.02),
        }[true_effect_type]

        # --- Sample size planning (often insufficient) ---
        planned_n_per_group = int(np.random.choice(
            [3000, 8000, 15000, 30000, 60000],
            p=[0.12, 0.28, 0.30, 0.20, 0.10]
        ))
        planned_duration_days = np.random.choice([7, 10, 14, 21, 28], p=[0.15, 0.20, 0.35, 0.20, 0.10])

        # --- Peeking / early stopping (40% of experiments) ---
        was_peeked = np.random.random() < 0.40
        if was_peeked:
            actual_fraction = np.random.uniform(0.40, 0.80)
            actual_n_per_group = int(planned_n_per_group * actual_fraction)
            actual_duration_days = int(planned_duration_days * actual_fraction)
        else:
            actual_fraction = np.random.uniform(0.90, 1.10)
            actual_n_per_group = int(planned_n_per_group * actual_fraction)
            actual_duration_days = int(planned_duration_days * np.random.uniform(0.95, 1.05))

        actual_duration_days = max(actual_duration_days, 3)

        # --- Simulate observed data ---
        n_control = actual_n_per_group
        n_treatment = actual_n_per_group + int(np.random.normal(0, actual_n_per_group * 0.02))
        n_treatment = max(n_treatment, 100)

        control_conversions = np.random.binomial(n_control, base_rate)
        treatment_rate_true = base_rate * (1 + true_effect)
        treatment_rate_true = np.clip(treatment_rate_true, 0.001, 0.999)
        treatment_conversions = np.random.binomial(n_treatment, treatment_rate_true)

        control_rate_obs = control_conversions / n_control
        treatment_rate_obs = treatment_conversions / n_treatment

        # --- Statistical test ---
        z_stat, p_value = two_proportion_z_test(
            control_conversions, n_control, treatment_conversions, n_treatment
        )

        observed_lift_abs = treatment_rate_obs - control_rate_obs
        observed_lift_rel = observed_lift_abs / control_rate_obs if control_rate_obs > 0 else 0

        ci_lower, ci_upper = _confidence_interval(control_rate_obs, treatment_rate_obs, n_control, n_treatment)

        power_achieved = calculate_power(base_rate, true_effect, actual_n_per_group)

        # --- Decision (mimics real org behavior with biases) ---
        decision, decision_maker = _simulate_decision(
            p_value, observed_lift_rel, was_peeked, team
        )

        # --- Post-ship validation (only for shipped experiments) ---
        post_ship_lift = None
        if decision == 'ship':
            post_ship_lift = true_effect + np.random.normal(0, 0.015)

        # --- MDE that was planned ---
        planned_mde = np.random.choice([0.03, 0.05, 0.08, 0.10], p=[0.15, 0.40, 0.30, 0.15])

        experiments.append({
            'experiment_id': f'EXP-{i+1:04d}',
            'experiment_name': experiment_name,
            'team': team,
            'feature_category': category,
            'quarter': quarter,
            'primary_metric': primary_metric,
            'base_rate': round(base_rate, 4),
            'planned_mde': planned_mde,
            'planned_n_per_group': planned_n_per_group,
            'planned_duration_days': int(planned_duration_days),
            'actual_n_control': n_control,
            'actual_n_treatment': n_treatment,
            'actual_duration_days': actual_duration_days,
            'was_peeked': was_peeked,
            'control_rate': round(control_rate_obs, 6),
            'treatment_rate': round(treatment_rate_obs, 6),
            'observed_lift_absolute': round(observed_lift_abs, 6),
            'observed_lift_relative': round(observed_lift_rel, 6),
            'p_value': round(p_value, 6),
            'ci_lower': round(ci_lower, 6),
            'ci_upper': round(ci_upper, 6),
            'z_statistic': round(z_stat, 4),
            'statistical_power': round(power_achieved, 4) if not np.isnan(power_achieved) else None,
            'decision': decision,
            'decision_maker': decision_maker,
            'true_effect': round(true_effect, 6),
            'true_effect_type': true_effect_type,
            'post_ship_lift': round(post_ship_lift, 6) if post_ship_lift is not None else None,
        })

    return pd.DataFrame(experiments)


def _confidence_interval(p_c, p_t, n_c, n_t, alpha=0.05):
    diff = p_t - p_c
    se = np.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    z = stats.norm.ppf(1 - alpha / 2)
    return diff - z * se, diff + z * se


def _simulate_decision(p_value, lift_rel, was_peeked, team):
    """
    Simulate realistic decision-making with common org biases:
    - PMs sometimes ship marginally significant results
    - Leadership sometimes overrides based on gut feel
    - Peeked experiments are more likely to be shipped (confirmation bias)
    """
    if p_value < 0.05 and lift_rel > 0:
        decision = 'ship'
        decision_maker = np.random.choice(['PM', 'Data', 'Leadership'], p=[0.50, 0.35, 0.15])
    elif p_value < 0.05 and lift_rel < 0:
        decision = 'kill'
        decision_maker = np.random.choice(['PM', 'Data'], p=[0.40, 0.60])
    elif p_value < 0.10 and lift_rel > 0:
        if was_peeked:
            decision = np.random.choice(['ship', 'inconclusive'], p=[0.45, 0.55])
        else:
            decision = np.random.choice(['ship', 'inconclusive'], p=[0.20, 0.80])
        decision_maker = np.random.choice(['PM', 'Leadership'], p=[0.60, 0.40])
    else:
        decision = np.random.choice(['kill', 'inconclusive'], p=[0.35, 0.65])
        decision_maker = np.random.choice(['PM', 'Data', 'Leadership'], p=[0.30, 0.50, 0.20])

    return decision, decision_maker


if __name__ == '__main__':
    print("Generating experiment corpus...")
    df = generate_experiment_corpus()

    output_path = os.path.join(os.path.dirname(__file__), 'experiments.csv')
    df.to_csv(output_path, index=False)

    print(f"Generated {len(df)} experiments -> {output_path}")
    print(f"\nDistribution of true effects:")
    print(df['true_effect_type'].value_counts())
    print(f"\nDecision distribution:")
    print(df['decision'].value_counts())
    print(f"\nPeeking rate: {df['was_peeked'].mean():.0%}")
    print(f"Median power: {df['statistical_power'].median():.2%}")
    print(f"Significance rate (p<0.05): {(df['p_value'] < 0.05).mean():.0%}")
