"""Formal Analytical Framework for SAS Data Science Career Intelligence.
Defines formal problem definition, analytics objectives, testable research questions,
hypotheses, methodology steps, evaluation standards, and scientific limitations.
"""
from .sas_models import AnalyticalFramework, ResearchQuestion, Hypothesis


def get_analytical_framework() -> AnalyticalFramework:
    """Return the structured, maintainable analytical framework."""
    
    research_questions = [
        ResearchQuestion(
            rq_id="RQ1",
            question="Which technical skill dimensions differ between high and low salary-hike groups among junior data scientists?",
            target_dataset="JDS Skill Traits.xlsx",
            analytical_method="Mann-Whitney U Test & Two-Sample Welch's t-test with Cohen's d effect sizes",
            business_context="Identifies baseline technical differentiation between career progression cohorts.",
            empirical_status="TESTED_WITH_DATA",
        ),
        ResearchQuestion(
            rq_id="RQ2",
            question="Which technical skill dimensions have statistically significant associations with the salary-hike outcome?",
            target_dataset="JDS Skill Traits.xlsx",
            analytical_method="Hypothesis testing (p < 0.05 threshold) with Point-Biserial and Rank Biserial correlation analysis",
            business_context="Separates empirical skill signal from statistical noise.",
            empirical_status="TESTED_WITH_DATA",
        ),
        ResearchQuestion(
            rq_id="RQ3",
            question="Which skills contribute most strongly to predicting junior data scientist salary-hike outcomes?",
            target_dataset="JDS Skill Traits.xlsx",
            analytical_method="Multivariate Logistic Regression (Standardized Coefficients & Odds Ratios) and Random Forest Feature Importance",
            business_context="Determines relative predictive weight of each skill when modeled jointly.",
            empirical_status="TESTED_WITH_DATA",
        ),
        ResearchQuestion(
            rq_id="RQ4",
            question="Does a multivariate model provide useful predictive signal beyond individual skill dimensions?",
            target_dataset="JDS Skill Traits.xlsx",
            analytical_method="Supervised classification comparison (Logistic Regression, Decision Tree, Random Forest) with Stratified 5-Fold Cross-Validation",
            business_context="Evaluates whether skill combinations yield synergistic predictive performance.",
            empirical_status="TESTED_WITH_DATA",
        ),
        ResearchQuestion(
            rq_id="RQ5",
            question="How stable are the model findings under rigorous cross-validation and error analysis?",
            target_dataset="JDS Skill Traits.xlsx",
            analytical_method="Stratified 5-Fold CV stability checks, confusion matrix decomposition, and False Positive/Negative profile analysis",
            business_context="Guards against overfitting in moderate sample sizes (N=139).",
            empirical_status="TESTED_WITH_DATA",
        ),
        ResearchQuestion(
            rq_id="RQ6",
            question="What skill-development recommendations can legitimately be derived from the observed evidence?",
            target_dataset="JDS Skill Traits.xlsx + Market Datasets",
            analytical_method="Evidence-grounded recommendation mapping (Finding -> Evidence -> Interpretation -> Action)",
            business_context="Translates empirical findings into actionable career and institutional guidance without causal overreach.",
            empirical_status="TESTED_WITH_DATA",
        ),
        # SDS Research Questions
        ResearchQuestion(
            rq_id="RQ_SDS_1",
            question="Which Big Five personality trait dimensions (OCEAN) differ significantly between high and low organizational success cohorts in senior data scientists?",
            target_dataset="SDS Personality Traits.xlsx",
            analytical_method="Mann-Whitney U and Welch's t-tests across normalized personality scores",
            business_context="Informs leadership and customer-facing competencies for senior analytics professionals.",
            empirical_status="TESTED_WITH_DATA",
        ),
        ResearchQuestion(
            rq_id="RQ_SDS_2",
            question="What is the predictive capacity of personality dimensions in classifying senior data scientist success?",
            target_dataset="SDS Personality Traits.xlsx",
            analytical_method="Regularized Logistic Regression and Random Forest classification with 5-Fold CV",
            business_context="Tests whether behavioural traits provide discriminative signal for senior career milestones.",
            empirical_status="TESTED_WITH_DATA",
        ),
        # Market Research Questions
        ResearchQuestion(
            rq_id="RQ_MKT_1",
            question="What are the prevailing salary distributions and experience expectations across recruiting companies in the 2024-2025 analytics job market?",
            target_dataset="Analytics Jobs.csv & DataScience Jobs.csv",
            analytical_method="Univariate distribution analysis, salary bracket decomposition, and experience band cross-tabulations",
            business_context="Establishes external market compensation context for data science roles.",
            empirical_status="TESTED_WITH_DATA",
        ),
    ]
    
    hypotheses = [
        Hypothesis(
            h_id="H1",
            hypothesis_statement="Technical skill dimensions are significantly associated with salary-hike outcome among junior data scientists.",
            null_hypothesis="There is no association between junior data scientist technical skill scores and salary-hike outcome.",
            alternative_hypothesis="At least one technical skill dimension has a statistically significant positive association with salary-hike outcome.",
            target_dataset="JDS Skill Traits.xlsx",
            tested_variables=["big_data_skills", "maths-stats_skills", "coding_skills", "ai_and_ml_skills", "dashboard_and_storytelling_skills"],
            status="UNTESTED",
        ),
        Hypothesis(
            h_id="H2",
            hypothesis_statement="Junior data scientists in the high salary-hike group exhibit significantly higher mean skill scores than those in the low salary-hike group.",
            null_hypothesis="The mean technical skill scores for high and low salary-hike groups are equal.",
            alternative_hypothesis="The high salary-hike group has statistically significantly higher mean technical skill scores.",
            target_dataset="JDS Skill Traits.xlsx",
            tested_variables=["big_data_skills", "maths-stats_skills", "coding_skills", "ai_and_ml_skills", "dashboard_and_storytelling_skills"],
            status="UNTESTED",
        ),
        Hypothesis(
            h_id="H3",
            hypothesis_statement="A multivariate technical skill classification model achieves predictive performance significantly above random chance (ROC-AUC > 0.50, F1 > 0.60) on cross-validation.",
            null_hypothesis="A multivariate skill model cannot predict salary-hike outcomes better than chance (ROC-AUC <= 0.50).",
            alternative_hypothesis="A multivariate skill model achieves ROC-AUC > 0.50 and balanced F1 on Stratified 5-Fold CV.",
            target_dataset="JDS Skill Traits.xlsx",
            tested_variables=["Multivariate model feature set"],
            status="UNTESTED",
        ),
        Hypothesis(
            h_id="H4",
            hypothesis_statement="Certain skill dimensions (e.g., Coding, AI/ML, or Math-Stats) contribute disproportionately higher predictive importance relative to others.",
            null_hypothesis="All technical skill dimensions contribute equal predictive importance in multivariate modeling.",
            alternative_hypothesis="Feature importance coefficients and odds ratios vary significantly across skill dimensions.",
            target_dataset="JDS Skill Traits.xlsx",
            tested_variables=["Odds Ratios", "Gini Importance"],
            status="UNTESTED",
        ),
        Hypothesis(
            h_id="H_SDS_1",
            hypothesis_statement="Big Five personality dimensions (e.g., Conscientiousness, Extraversion, Openness) are significantly associated with senior data scientist success classification.",
            null_hypothesis="Personality trait scores do not differ between high and low success senior data scientists.",
            alternative_hypothesis="At least one Big Five trait score is significantly higher in high-success senior data scientists.",
            target_dataset="SDS Personality Traits.xlsx",
            tested_variables=["neuroticism", "extraversion", "openness_to_experience", "agreeableness", "conscientiousness"],
            status="UNTESTED",
        ),
    ]

    methodology_steps = [
        "1. Comprehensive Data Profiling (Missingness, Outliers, Dtypes, Balance)",
        "2. Reproducible Data Preparation & Schema Validation",
        "3. Exploratory Data Analysis & Bivariate Distribution Profiling",
        "4. Assumption-Checked Statistical Hypothesis Testing (Mann-Whitney U, Welch t-test, Cohen's d)",
        "5. Supervised Machine Learning with Stratified K-Fold Cross Validation",
        "6. Error Decomposition (False Positives/Negatives) & Stability Analysis",
        "7. Feature Importance & Odds Ratio Interpretability",
        "8. Immutable Evidence Layer Assembly",
        "9. Actionable, Evidence-Grounded Stakeholder Recommendations",
        "10. Rigorous Limitations & Ethical Boundary Documentation",
    ]
    
    evaluation_standards = [
        "Accuracy, Precision, Recall, F1-Score, Balanced Accuracy, and ROC-AUC",
        "Stratified 5-Fold Cross Validation mean and standard deviation",
        "Confusion Matrix decomposition (Specificity, NPV, False Positive Rate, False Negative Rate)",
        "Odds Ratios with 95% Confidence Intervals for Logistic Regression",
        "Cohen's d and Rank Biserial Effect Size metrics for statistical tests",
    ]
    
    scientific_limitations = [
        "Observational Study Limitation: All analyses indicate statistical association, NOT direct causation.",
        "Sample Size Constraints: JDS (N=139) and SDS (N=161) datasets represent company-level sample cohorts; findings require iterative external validation.",
        "Non-Joinable Dataset Architecture: JDS (junior skills), SDS (senior personality), and Job postings represent separate observational units and must not be joined.",
        "Masked & Self-Reported Metrics: Skill scores (1-5 scale) and personality scores (0-100 normalized) reflect standardized internal evaluation frameworks.",
    ]
    
    return AnalyticalFramework(
        problem_title="SAS Data Science Career Intelligence & Decision-Support System",
        analytics_objective="Identify which technical skill dimensions are most strongly associated with high salary-hike outcomes among junior data scientists, and translate these findings into evidence-based skill-development recommendations.",
        secondary_objective="Analyze the association between Big Five personality dimensions (OCEAN) and organizational success outcomes among senior, customer-facing data scientists.",
        market_objective="Characterize the broader 2024-2025 analytics job market landscape regarding hiring volumes, experience expectations, and salary distributions across recruiting organizations.",
        research_questions=research_questions,
        hypotheses=hypotheses,
        methodology_steps=methodology_steps,
        evaluation_standards=evaluation_standards,
        scientific_limitations=scientific_limitations,
    )
