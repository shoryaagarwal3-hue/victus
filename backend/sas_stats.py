"""Statistical Analysis Service for SAS Datasets.
Performs hypothesis testing, normality checks (Shapiro-Wilk), Mann-Whitney U tests,
Welch's t-tests, Cohen's d effect sizes, and 95% confidence intervals.
"""
from typing import Any
import numpy as np
import pandas as pd
from scipy import stats

from .sas_models import StatisticalTestResult


def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d effect size for two independent groups."""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    var1 = np.var(group1, ddof=1)
    var2 = np.var(group2, ddof=1)
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    d = (np.mean(group2) - np.mean(group1)) / pooled_std
    return round(float(d), 3)


def calculate_confidence_interval_mean_diff(group1: np.ndarray, group2: np.ndarray, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate confidence interval for difference in means (Welch's approximation)."""
    n1, n2 = len(group1), len(group2)
    m1, m2 = np.mean(group1), np.mean(group2)
    v1, v2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    se_diff = np.sqrt(v1 / n1 + v2 / n2)
    if se_diff == 0:
        return round(float(m2 - m1), 3), round(float(m2 - m1), 3)
        
    # Welch-Satterthwaite degrees of freedom
    num = (v1 / n1 + v2 / n2) ** 2
    denom = ((v1 / n1) ** 2 / (n1 - 1)) + ((v2 / n2) ** 2 / (n2 - 1))
    df = num / denom if denom > 0 else (n1 + n2 - 2)
    
    t_crit = stats.t.ppf((1 + confidence) / 2, df=df)
    diff = m2 - m1
    ci_lower = diff - t_crit * se_diff
    ci_upper = diff + t_crit * se_diff
    return round(float(ci_lower), 3), round(float(ci_upper), 3)


def run_group_comparison_test(
    df: pd.DataFrame,
    var_name: str,
    group_col: str,
    rq_ref: str = "RQ1",
    alpha: float = 0.05,
) -> StatisticalTestResult:
    """Run thorough two-sample comparison with assumption checks, U test, and effect size."""
    group0 = df[df[group_col] == 0][var_name].dropna().values
    group1 = df[df[group_col] == 1][var_name].dropna().values
    
    if len(group0) < 3 or len(group1) < 3:
        raise ValueError(f"Insufficient samples to compare groups for {var_name}")
        
    # Normality testing
    shapiro_0 = stats.shapiro(group0) if len(group0) >= 3 else (0.0, 0.0)
    shapiro_1 = stats.shapiro(group1) if len(group1) >= 3 else (0.0, 0.0)
    
    norm_0_passed = bool(shapiro_0.pvalue > 0.05)
    norm_1_passed = bool(shapiro_1.pvalue > 0.05)
    
    # Non-parametric Mann-Whitney U test (primary for ordinal/non-normal data)
    u_stat, u_pvalue = stats.mannwhitneyu(group1, group0, alternative="two-sided")
    
    # Parametric Welch's t-test
    t_stat, t_pvalue = stats.ttest_ind(group1, group0, equal_var=False)
    
    # Effect size
    cohen_d = calculate_cohens_d(group0, group1)
    ci_95 = calculate_confidence_interval_mean_diff(group0, group1)
    
    is_sig = bool(u_pvalue < alpha)
    
    # Summary stats
    m0, med0, s0 = float(np.mean(group0)), float(np.median(group0)), float(np.std(group0, ddof=1))
    m1, med1, s1 = float(np.mean(group1)), float(np.median(group1)), float(np.std(group1, ddof=1))
    
    effect_label = "negligible"
    abs_d = abs(cohen_d)
    if abs_d >= 0.8:
        effect_label = "large"
    elif abs_d >= 0.5:
        effect_label = "medium"
    elif abs_d >= 0.2:
        effect_label = "small"
        
    sig_text = "statistically significant" if is_sig else "not statistically significant"
    diff_dir = "higher" if m1 > m0 else "lower"
    interpretation = (
        f"Group 1 (High outcome) scored {diff_dir} in '{var_name}' (Mean={m1:.2f}, Median={med1:.2f}) "
        f"compared to Group 0 (Low outcome, Mean={m0:.2f}, Median={med0:.2f}). "
        f"The Mann-Whitney U test indicates this difference is {sig_text} (U={u_stat:.1f}, p={u_pvalue:.4f}) "
        f"with a {effect_label} effect size (Cohen's d={cohen_d:.2f}, 95% CI: [{ci_95[0]:.2f}, {ci_95[1]:.2f}])."
    )
    
    return StatisticalTestResult(
        test_id=f"TEST_{group_col}_{var_name}",
        research_question_ref=rq_ref,
        variable_name=var_name,
        group_variable=group_col,
        test_type="Mann-Whitney U (Non-Parametric) & Welch's t-test",
        assumptions_checked={
            "normality_group_0_shapiro": norm_0_passed,
            "normality_group_1_shapiro": norm_1_passed,
            "homoscedasticity_checked": False,
            "independent_observations": True,
        },
        normality_p_value_low=round(float(shapiro_0.pvalue), 4),
        normality_p_value_high=round(float(shapiro_1.pvalue), 4),
        test_statistic=round(float(u_stat), 3),
        p_value=round(float(u_pvalue), 5),
        is_statistically_significant=is_sig,
        significance_threshold=alpha,
        effect_size_type="Cohen's d",
        effect_size_value=cohen_d,
        confidence_interval_95=ci_95,
        group_low_mean=round(m0, 3),
        group_low_median=round(med0, 3),
        group_low_std=round(s0, 3),
        group_high_mean=round(m1, 3),
        group_high_median=round(med1, 3),
        group_high_std=round(s1, 3),
        interpretation=interpretation,
    )


def run_all_jds_statistical_tests(jds_df: pd.DataFrame) -> list[StatisticalTestResult]:
    """Run full battery of hypothesis tests on all 5 JDS skill dimensions."""
    skill_cols = [
        "big_data_skills",
        "maths-stats_skills",
        "coding_skills",
        "ai_and_ml_skills",
        "dashboard_and_storytelling_skills",
    ]
    results = []
    for skill in skill_cols:
        res = run_group_comparison_test(
            df=jds_df,
            var_name=skill,
            group_col="salary_hike_high_or_low",
            rq_ref="RQ1 / RQ2",
        )
        results.append(res)
    return results


def run_all_sds_statistical_tests(sds_df: pd.DataFrame) -> list[StatisticalTestResult]:
    """Run full battery of hypothesis tests on all 5 Big Five personality traits in SDS."""
    trait_cols = [
        "neuroticism",
        "extraversion",
        "openness_to_experience",
        "agreeableness",
        "conscientiousness",
    ]
    results = []
    for trait in trait_cols:
        res = run_group_comparison_test(
            df=sds_df,
            var_name=trait,
            group_col="success_classification_high_low",
            rq_ref="RQ_SDS_1",
        )
        results.append(res)
    return results
