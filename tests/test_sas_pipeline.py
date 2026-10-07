"""Comprehensive Test Suite for SAS Data Science Career Intelligence & Decision-Support System.
Tests:
- Dataset loading and schema validation
- Data profiling and IQR outlier detection
- Auditable data preparation and salary parsing
- Independence of JDS, SDS, and Market datasets (no unsupported joins)
- Statistical hypothesis testing (Mann-Whitney U, Welch t-test, Cohen's d, CIs)
- Supervised ML models with Stratified 5-Fold Cross-Validation
- Confusion Matrix and Error Analysis (False Positives & Negatives)
- Feature Importance and Logistic Regression Odds Ratios
- Evidence layer assembly and provenance
- Recommendation engine grounding
- Grounded AI interpretation and deterministic fallback
- End-to-end pipeline execution
"""
import pytest
import pandas as pd
import numpy as np

from backend.sas_data_loader import (
    load_analytics_jobs,
    load_datascience_jobs,
    load_jds_skills,
    load_sds_personality,
    load_all_datasets,
)
from backend.sas_profiler import profile_dataset, build_full_quality_audit
from backend.sas_prep import (
    prepare_jds_skills,
    prepare_sds_personality,
    prepare_datascience_jobs,
    prepare_analytics_jobs,
    run_full_preparation,
)
from backend.sas_framework import get_analytical_framework
from backend.sas_stats import (
    calculate_cohens_d,
    calculate_confidence_interval_mean_diff,
    run_group_comparison_test,
    run_all_jds_statistical_tests,
    run_all_sds_statistical_tests,
)
from backend.sas_ml import (
    train_and_evaluate_jds_models,
    train_and_evaluate_sds_models,
)
from backend.sas_market import summarize_market_landscape
from backend.sas_evidence import compile_evidence_register
from backend.sas_recommendations import generate_stakeholder_recommendations
from backend.sas_ai_service import build_deterministic_executive_narrative
from backend.sas_report_generator import generate_full_approach_note_markdown
from backend.sas_pipeline import run_full_sas_pipeline


def test_01_sas_data_loading():
    """Verify loading and schema validation of all 4 official SAS datasets."""
    datasets = load_all_datasets()
    assert len(datasets.analytics_jobs) == 15841
    assert len(datasets.datascience_jobs) == 1602
    assert len(datasets.jds_skills) == 139
    assert len(datasets.sds_personality) == 161
    
    # Check JDS columns
    assert "salary_hike_high_or_low" in datasets.jds_skills.columns
    assert "coding_skills" in datasets.jds_skills.columns
    assert "ai_and_ml_skills" in datasets.jds_skills.columns
    
    # Check SDS columns
    assert "success_classification_high_low" in datasets.sds_personality.columns
    assert "extraversion" in datasets.sds_personality.columns
    assert "conscientiousness" in datasets.sds_personality.columns


def test_02_sas_data_profiling():
    """Verify statistical profiling, missingness, and IQR outlier detection."""
    jds_df = load_jds_skills()
    profile = profile_dataset(jds_df, "JDS Skill Traits", "Excel", target_col="salary_hike_high_or_low")
    
    assert profile.row_count == 139
    assert profile.column_count == 7
    assert profile.duplicate_rows == 0
    assert profile.missing_cells_total == 0
    assert profile.data_quality_score == 100.0
    assert profile.class_imbalance is not None
    assert profile.class_imbalance["target_column"] == "salary_hike_high_or_low"
    
    coding_prof = next(c for c in profile.columns if c.column_name == "coding_skills")
    assert coding_prof.numeric_stats is not None
    assert 1.0 <= coding_prof.numeric_stats["mean"] <= 5.0
    assert 1.0 <= coding_prof.numeric_stats["min"] <= coding_prof.numeric_stats["max"] <= 5.0


def test_03_auditable_data_preparation():
    """Verify reproducible preparation, transformation logs, and salary/experience parsing."""
    raw_datasets = load_all_datasets()
    prepared = run_full_preparation(
        raw_datasets.analytics_jobs,
        raw_datasets.datascience_jobs,
        raw_datasets.jds_skills,
        raw_datasets.sds_personality,
    )
    
    assert len(prepared.prep_result.transformations) >= 4
    for tx in prepared.prep_result.transformations:
        assert tx.dataset_name
        assert tx.step_name
        assert tx.reason
        assert tx.rule_applied
        
    # Verify parsed salaries in DataScience Jobs
    assert "avg_salary_lakhs" in prepared.datascience_jobs.columns
    valid_sal = prepared.datascience_jobs["avg_salary_lakhs"].dropna()
    assert len(valid_sal) > 1000
    assert valid_sal.mean() > 0.0


def test_04_no_unsupported_joins():
    """Verify that JDS and SDS maintain independent observational namespaces."""
    jds_df = load_jds_skills()
    sds_df = load_sds_personality()
    
    jds_ids = set(jds_df["id"].values)
    sds_ids = set(sds_df["id"].values)
    
    # Confirm they represent separate cohorts (junior vs senior data scientists)
    assert len(jds_df) == 139
    assert len(sds_df) == 161
    assert len(jds_ids.intersection(sds_ids)) == 0, "JDS and SDS IDs must remain distinct cohorts"


def test_05_analytical_framework():
    """Verify formal problem definition, RQs (RQ1-6), hypotheses (H1-4), and limitations."""
    fw = get_analytical_framework()
    assert fw.problem_title
    assert fw.analytics_objective
    assert len(fw.research_questions) >= 6
    assert any(rq.rq_id == "RQ1" for rq in fw.research_questions)
    assert any(rq.rq_id == "RQ6" for rq in fw.research_questions)
    assert len(fw.hypotheses) >= 4
    assert len(fw.scientific_limitations) >= 4


def test_06_statistical_hypothesis_testing():
    """Verify Mann-Whitney U, Welch's t-test, Cohen's d effect sizes, and p-values."""
    jds_df = load_jds_skills()
    jds_clean, _ = prepare_jds_skills(jds_df)
    
    stats_results = run_all_jds_statistical_tests(jds_clean)
    assert len(stats_results) == 5
    
    for res in stats_results:
        assert res.variable_name in jds_clean.columns
        assert res.test_statistic > 0.0
        assert 0.0 <= res.p_value <= 1.0
        assert res.effect_size_type == "Cohen's d"
        assert res.confidence_interval_95 is not None
        assert "NOT causal" in res.causation_disclaimer
        assert res.group_low_mean is not None
        assert res.group_high_mean is not None


def test_07_supervised_machine_learning_and_cv():
    """Verify Logistic Regression, Random Forest, Decision Tree, 5-Fold Stratified CV, and Confusion Matrix."""
    jds_df = load_jds_skills()
    jds_clean, _ = prepare_jds_skills(jds_df)
    
    models = train_and_evaluate_jds_models(jds_clean)
    assert len(models) == 3
    
    lr_model = next(m for m in models if "Logistic Regression" in m.model_name)
    assert lr_model.train_metrics.accuracy > 0.50
    assert lr_model.test_metrics.accuracy > 0.50
    assert lr_model.cv_results is not None
    assert lr_model.cv_results.cv_folds == 5
    assert lr_model.cv_results.mean_accuracy > 0.50
    
    # Check confusion matrix
    cm = lr_model.confusion_matrix
    assert (cm.true_positives + cm.true_negatives + cm.false_positives + cm.false_negatives) == lr_model.test_size
    assert 0.0 <= cm.specificity <= 1.0
    
    # Check feature importances & Odds Ratios
    assert len(lr_model.feature_importances) == 5
    for fi in lr_model.feature_importances:
        assert fi.feature_name
        assert fi.odds_ratio is not None
        assert fi.odds_ratio > 0.0
        assert fi.rank in range(1, 6)


def test_08_error_analysis_decomposition():
    """Verify false positive and false negative error analysis."""
    jds_df = load_jds_skills()
    jds_clean, _ = prepare_jds_skills(jds_df)
    models = train_and_evaluate_jds_models(jds_clean)
    
    lr_model = next(m for m in models if "Logistic Regression" in m.model_name)
    # Check that error cases (if any) are properly decomposed
    for err in lr_model.error_analysis:
        assert err.error_type in ("FALSE_POSITIVE", "FALSE_NEGATIVE")
        assert err.record_id > 0
        assert 0.0 <= err.predicted_probability <= 1.0
        assert err.contributing_factors


def test_09_evidence_layer_and_recommendations():
    """Verify evidence items and evidence-grounded recommendations."""
    raw_datasets = load_all_datasets()
    prepared = run_full_preparation(
        raw_datasets.analytics_jobs,
        raw_datasets.datascience_jobs,
        raw_datasets.jds_skills,
        raw_datasets.sds_personality,
    )
    jds_stats = run_all_jds_statistical_tests(prepared.jds_skills)
    sds_stats = run_all_sds_statistical_tests(prepared.sds_personality)
    jds_models = train_and_evaluate_jds_models(prepared.jds_skills)
    sds_models = train_and_evaluate_sds_models(prepared.sds_personality)
    mkt = summarize_market_landscape(prepared.analytics_jobs, prepared.datascience_jobs)
    
    evidence = compile_evidence_register(jds_stats + sds_stats, jds_models, sds_models, mkt)
    assert len(evidence) >= 10
    for ev in evidence:
        assert ev.evidence_id.startswith("EV_")
        assert ev.dataset_source
        assert ev.evidence_strength in ("STRONG", "MODERATE", "EMERGING", "INCONCLUSIVE")
        assert ev.status_tag == "ACTUAL"
        
    recs = generate_stakeholder_recommendations(jds_stats, jds_models, sds_models, evidence)
    assert len(recs) >= 3
    for rec in recs:
        assert rec.target_stakeholder in (
            "Junior Data Scientists",
            "Hiring Managers & Industry Leaders",
            "Academic & Training Institutions",
        )
        assert rec.evidence_citation
        assert rec.status_label == "EVIDENCE_SUPPORTED"


def test_10_full_sas_pipeline_end_to_end():
    """Verify complete end-to-end execution of master SAS intelligence pipeline."""
    result = run_full_sas_pipeline()
    assert result.framework is not None
    assert len(result.statistical_results) == 10
    assert len(result.jds_models) == 3
    assert len(result.evidence_register) >= 12
    assert len(result.recommendations) >= 3
    assert len(result.executive_summary) > 200
    
    # Verify full 22-section Approach Note markdown generation
    note = generate_full_approach_note_markdown(result)
    assert "### 1. Executive Summary" in note
    assert "### 22. Hackathon Rubric Mapping" in note
    assert len(note) > 10000
