"""Pydantic schemas and typed data contracts for SAS Data Science Career Intelligence & Decision-Support System.
Supports data profiling, statistical testing, machine learning evaluations, evidence provenance,
analytical frameworks, and evidence-grounded recommendations.
"""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class ColumnProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    column_name: str
    dtype: str
    total_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int
    is_constant: bool = False
    is_target: bool = False
    numeric_stats: dict[str, float] | None = None
    top_categories: dict[str, int] | None = None
    outlier_count_iqr: int = 0
    anomalies_detected: list[str] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    dataset_name: str
    file_type: str
    row_count: int
    column_count: int
    duplicate_rows: int
    missing_cells_total: int
    missing_cells_percentage: float
    columns: list[ColumnProfile] = Field(default_factory=list)
    class_imbalance: dict[str, Any] | None = None
    data_quality_score: float = Field(default=100.0, ge=0.0, le=100.0)
    data_quality_notes: list[str] = Field(default_factory=list)


class DataQualityAudit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    dataset_profiles: dict[str, DatasetProfile] = Field(default_factory=dict)
    cross_dataset_integrity_notes: list[str] = Field(default_factory=list)
    overall_quality_assessment: str = "HIGH QUALITY — Validated against official SAS specifications"


class PrepTransformation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    dataset_name: str
    step_name: str
    records_affected: int
    reason: str
    rule_applied: str
    reversible: bool = True


class PrepResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    cleaned_datasets: list[str] = Field(default_factory=list)
    transformations: list[PrepTransformation] = Field(default_factory=list)
    initial_rows: dict[str, int] = Field(default_factory=dict)
    final_rows: dict[str, int] = Field(default_factory=dict)
    target_distributions: dict[str, dict[str, int]] = Field(default_factory=dict)


class ResearchQuestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    rq_id: str
    question: str
    target_dataset: str
    analytical_method: str
    business_context: str
    empirical_status: Literal["TESTED_WITH_DATA", "PROPOSED", "ILLUSTRATIVE"] = "TESTED_WITH_DATA"


class Hypothesis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    h_id: str
    hypothesis_statement: str
    null_hypothesis: str
    alternative_hypothesis: str
    target_dataset: str
    tested_variables: list[str] = Field(default_factory=list)
    status: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "REJECTED", "UNTESTED"] = "UNTESTED"
    p_value: float | None = None
    effect_size: float | None = None
    statistical_evidence: str = ""


class AnalyticalFramework(BaseModel):
    model_config = ConfigDict(extra="ignore")
    problem_title: str
    analytics_objective: str
    secondary_objective: str
    market_objective: str
    research_questions: list[ResearchQuestion] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    methodology_steps: list[str] = Field(default_factory=list)
    evaluation_standards: list[str] = Field(default_factory=list)
    scientific_limitations: list[str] = Field(default_factory=list)


class StatisticalTestResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    test_id: str
    research_question_ref: str
    variable_name: str
    group_variable: str
    test_type: str  # Mann-Whitney U, Welch's t-test, Chi-Square, etc.
    assumptions_checked: dict[str, bool] = Field(default_factory=dict)
    normality_p_value_low: float | None = None
    normality_p_value_high: float | None = None
    test_statistic: float
    p_value: float
    is_statistically_significant: bool
    significance_threshold: float = 0.05
    effect_size_type: str  # Cohen's d, Rank Biserial, Cramér's V
    effect_size_value: float
    confidence_interval_95: tuple[float, float] | None = None
    group_low_mean: float | None = None
    group_low_median: float | None = None
    group_low_std: float | None = None
    group_high_mean: float | None = None
    group_high_median: float | None = None
    group_high_std: float | None = None
    interpretation: str
    causation_disclaimer: str = "Observational data: Indicates statistical association, NOT causal effect."


class ClassificationMetrics(BaseModel):
    model_config = ConfigDict(extra="ignore")
    accuracy: float = Field(ge=0.0, le=1.0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1_score: float = Field(ge=0.0, le=1.0)
    roc_auc: float | None = Field(default=None, ge=0.0, le=1.0)
    log_loss_value: float | None = None
    balanced_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)


class ConfusionMatrixData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    true_negatives: int
    false_positives: int
    false_negatives: int
    true_positives: int
    specificity: float = Field(ge=0.0, le=1.0)
    negative_predictive_value: float = Field(ge=0.0, le=1.0)


class FeatureImportanceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    feature_name: str
    importance_metric: str  # Odds Ratio, Coefficient, Gini Importance, Permutation Importance
    importance_value: float
    std_error: float | None = None
    p_value: float | None = None
    odds_ratio: float | None = None
    odds_ratio_ci_95: tuple[float, float] | None = None
    rank: int = 1
    interpretation: str = ""


class CrossValidationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    cv_folds: int = 5
    strategy: str = "StratifiedKFold"
    accuracy_scores: list[float] = Field(default_factory=list)
    f1_scores: list[float] = Field(default_factory=list)
    roc_auc_scores: list[float] = Field(default_factory=list)
    mean_accuracy: float
    std_accuracy: float
    mean_f1: float
    std_f1: float
    mean_roc_auc: float | None = None
    std_roc_auc: float | None = None


class ErrorAnalysisCase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    record_id: int
    true_label: int
    predicted_label: int
    predicted_probability: float
    error_type: Literal["FALSE_POSITIVE", "FALSE_NEGATIVE"]
    skill_profile: dict[str, float] = Field(default_factory=dict)
    contributing_factors: str = ""


class ModelResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model_name: str
    target_variable: str
    features_used: list[str] = Field(default_factory=list)
    train_size: int
    test_size: int
    train_metrics: ClassificationMetrics
    test_metrics: ClassificationMetrics
    cv_results: CrossValidationResult | None = None
    confusion_matrix: ConfusionMatrixData
    feature_importances: list[FeatureImportanceItem] = Field(default_factory=list)
    error_analysis: list[ErrorAnalysisCase] = Field(default_factory=list)
    model_stability_notes: str = ""
    hyperparameters: dict[str, Any] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    evidence_id: str
    claim_or_finding: str
    dataset_source: str
    columns_involved: list[str] = Field(default_factory=list)
    filter_or_subset: str = "All records"
    method_applied: str
    calculated_metric_name: str
    calculated_metric_value: float | str
    sample_size: int
    statistical_significance: bool | None = None
    p_value: float | None = None
    evidence_strength: Literal["STRONG", "MODERATE", "EMERGING", "INCONCLUSIVE"] = "MODERATE"
    interpretation: str
    limitations: str
    status_tag: Literal["ACTUAL", "PROPOSED", "ILLUSTRATIVE"] = "ACTUAL"


class RecommendationItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    rec_id: str
    target_stakeholder: Literal[
        "Junior Data Scientists",
        "Hiring Managers & Industry Leaders",
        "Academic & Training Institutions",
    ]
    finding_summary: str
    evidence_citation: str
    evidence_strength: Literal["STRONG", "MODERATE", "EMERGING", "INCONCLUSIVE"] = "MODERATE"
    action_type: str
    recommended_action: str
    expected_impact: str
    practical_effort: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    status_label: Literal["EVIDENCE_SUPPORTED", "EXPLORATORY", "DATASET_LIMITED"] = "EVIDENCE_SUPPORTED"
    causation_warning: str = "Implementation should be monitored iteratively; observational association does not guarantee guaranteed salary returns."


class MarketDistributionSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    total_postings_analyzed: int
    unique_companies: int
    top_hiring_companies: dict[str, int] = Field(default_factory=dict)
    experience_bands: dict[str, int] = Field(default_factory=dict)
    top_key_skills: dict[str, int] = Field(default_factory=dict)
    top_locations: dict[str, int] = Field(default_factory=dict)
    salary_summary_lakhs: dict[str, float] = Field(default_factory=dict)


class SASFullPipelineResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    framework: AnalyticalFramework
    data_quality_audit: DataQualityAudit
    data_prep_result: PrepResult
    statistical_results: list[StatisticalTestResult] = Field(default_factory=list)
    jds_models: list[ModelResult] = Field(default_factory=list)
    sds_models: list[ModelResult] = Field(default_factory=list)
    market_summary: MarketDistributionSummary
    evidence_register: list[EvidenceItem] = Field(default_factory=list)
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    executive_summary: str = ""
    ai_interpretation_provenance: Literal["AI-ASSISTED (GEMINI)", "DETERMINISTIC VERIFIED FALLBACK"] = "DETERMINISTIC VERIFIED FALLBACK"
