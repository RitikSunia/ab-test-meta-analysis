"""
Shared statistical utility functions for the A/B Test Meta-Analysis Engine.
"""

import numpy as np
from scipy import stats


def two_proportion_z_test(successes_a, n_a, successes_b, n_b):
    """
    Two-proportion z-test. Returns z-statistic and two-sided p-value.
    """
    p_a = successes_a / n_a
    p_b = successes_b / n_b
    pooled = (successes_a + successes_b) / (n_a + n_b)
    se = np.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))

    if se == 0:
        return 0.0, 1.0

    z = (p_b - p_a) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    return z, p_value


def calculate_power(base_rate, relative_mde, n_per_group, alpha=0.05):
    """
    Approximate power for a two-proportion z-test using the arcsine transformation.
    """
    p1 = base_rate
    p2 = base_rate * (1 + relative_mde)

    if p2 <= 0 or p2 >= 1 or p1 <= 0 or p1 >= 1:
        return np.nan

    effect_size = 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_power = abs(effect_size) * np.sqrt(n_per_group) - z_alpha
    power = stats.norm.cdf(z_power)
    return np.clip(power, 0, 1)


def required_sample_size(base_rate, relative_mde, power=0.80, alpha=0.05):
    """
    Required sample size per group for a two-proportion z-test.
    """
    p1 = base_rate
    p2 = base_rate * (1 + relative_mde)

    if p2 <= 0 or p2 >= 1:
        return np.nan

    effect_size = 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))

    if effect_size == 0:
        return np.inf

    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    n = ((z_alpha + z_beta) / effect_size) ** 2
    return int(np.ceil(n))


def confidence_interval_for_lift(p_control, p_treatment, n_control, n_treatment, alpha=0.05):
    """
    Confidence interval for the absolute difference (treatment - control).
    """
    diff = p_treatment - p_control
    se = np.sqrt(p_control * (1 - p_control) / n_control +
                 p_treatment * (1 - p_treatment) / n_treatment)
    z = stats.norm.ppf(1 - alpha / 2)
    return diff - z * se, diff + z * se


def benjamini_hochberg(p_values, alpha=0.05):
    """
    Benjamini-Hochberg procedure for controlling False Discovery Rate.
    Returns a boolean array indicating which hypotheses are rejected.
    """
    p_values = np.asarray(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    thresholds = alpha * np.arange(1, n + 1) / n
    max_reject_idx = -1

    for i in range(n):
        if sorted_p[i] <= thresholds[i]:
            max_reject_idx = i

    rejected = np.zeros(n, dtype=bool)
    if max_reject_idx >= 0:
        rejected[sorted_indices[:max_reject_idx + 1]] = True

    return rejected
