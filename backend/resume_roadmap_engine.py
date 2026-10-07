"""Actionable Learning Roadmap & Resume Improvement Generator.
Produces structured learning milestones (Foundation -> Practice -> Project -> Portfolio Evidence)
and concrete bullet-point improvement suggestions.
"""
from typing import Any
from .resume_models import (
    LearningRoadmapStep,
    ParsedResume,
    PrioritySkillGap,
    ResumeImprovementTip,
)


ROADMAP_TEMPLATES: dict[str, dict[str, Any]] = {
    "SQL": {
        "why_it_matters": "Universal data extraction language; essential for translating raw transactional databases into analytical features.",
        "prerequisites": ["Basic understanding of relational tables", "Data types"],
        "foundation": ["SELECT", "WHERE filter clauses", "ORDER BY", "GROUP BY", "HAVING", "COUNT, SUM, AVG, MIN, MAX aggregations"],
        "intermediate": ["INNER JOIN, LEFT/RIGHT JOIN, FULL OUTER JOIN", "CASE WHEN conditional logic", "Subqueries & Correlated Subqueries", "Common Table Expressions (CTEs)"],
        "advanced": ["Window Functions (ROW_NUMBER, RANK, DENSE_RANK, LEAD, LAG)", "Cumulative Aggregations (SUM OVER)", "Query Optimization & Indexing", "Analytical Partitioning"],
        "practice": ["Solve 25+ LeetCode/HackerRank SQL problems focusing on self-joins and window functions", "Write complex multi-table analytics queries on Northwind/E-Commerce DB"],
        "mini_project": "Customer Retention Cohort Analysis: Build SQL script to calculate Monthly Active Users (MAU) and churn rates.",
        "main_project": "End-to-End Retail Sales Intelligence Pipeline: Schema design, ETL transformation scripts, indexing, and complex analytical CTE queries answering 10 executive business questions.",
        "validation_milestone": "Execute multi-stage CTEs with window partitioning and explain execution plan runtime optimizations.",
        "portfolio_evidence": ["Public GitHub repository with clean .sql scripts", "README explaining business findings with result tables", "ER diagram illustrating schema design"],
        "bullet_template": "Engineered analytical SQL pipelines utilizing CTEs and Window Functions on 500K+ records, reducing query latency by 35% and identifying key customer churn cohorts.",
    },
    "Python": {
        "why_it_matters": "Primary programming language for data engineering, exploratory data analysis, and production machine learning.",
        "prerequisites": ["Basic computer science concepts", "Logic and control flow"],
        "foundation": ["Data structures (Lists, Dicts, Sets, Tuples)", "Functions & Comprehensions", "File I/O", "OOP Fundamentals", "Virtual Environments & pip"],
        "intermediate": ["NumPy array operations and broadcasting", "Pandas DataFrame manipulation, merging, groupby, and pivot", "Data cleaning & type coercion", "Regular Expressions"],
        "advanced": ["Vectorized computations & performance profiling", "Object-oriented modular design", "Building modular Python packages", "Unit testing with Pytest"],
        "practice": ["Implement custom data manipulation functions without external libraries", "Clean messy raw CSV datasets with inconsistent date/string formats"],
        "mini_project": "Automated Financial Data Scraper & Analyzer: Extract, clean, and summarize quarterly metrics using Pandas.",
        "main_project": "Production-Ready Data Processing Engine: Modular object-oriented Python package with automated data validation (Pydantic), logging, and 95%+ Pytest test coverage.",
        "validation_milestone": "Write modular, PEP 8 compliant, type-annotated code with comprehensive unit tests running on sample data.",
        "portfolio_evidence": ["GitHub repository with pyproject.toml / requirements.txt", "Automated GitHub Actions CI workflow", "Comprehensive unit test suite"],
        "bullet_template": "Architected modular Python analytics package with automated Pydantic validation and 95% Pytest coverage, processing 100K+ records/minute.",
    },
    "Machine Learning": {
        "why_it_matters": "Enables predictive modeling, pattern extraction, and automated decision-support from structured tabular data.",
        "prerequisites": ["Python (NumPy/Pandas)", "Linear Algebra", "Introductory Statistics"],
        "foundation": ["Supervised vs Unsupervised learning paradigms", "Train/Test Splits", "Bias-Variance Tradeoff", "Loss Functions", "Evaluation Metrics (Accuracy, Precision, Recall, F1, ROC-AUC)"],
        "intermediate": ["Linear & Logistic Regression", "Decision Trees & Random Forests", "Gradient Boosting (XGBoost, LightGBM)", "Cross-Validation (Stratified K-Fold)", "Hyperparameter Tuning (Grid/Random Search)"],
        "advanced": ["Feature Engineering (Target Encoding, Interactions)", "Imbalanced Data Handling (SMOTE, Class Weights)", "SHAP / LIME Model Explainability", "Preventing Data Leakage"],
        "practice": ["Train baseline Logistic Regression and tune XGBoost on Kaggle datasets (e.g. Titanic, Credit Risk, Telco Churn)", "Decompose error matrices and analyze False Positives/Negatives"],
        "mini_project": "Credit Default Risk Classifier: Train, evaluate, and interpret a regularized Logistic Regression model with odds ratios.",
        "main_project": "End-to-End Enterprise Churn Prediction System: Data preprocessing pipeline, XGBoost model training with 5-fold cross-validation, hyperparameter tuning, SHAP explainability dashboard, and business impact estimation.",
        "validation_milestone": "Achieve statistically validated cross-validation performance with full confusion matrix and SHAP feature importance charts.",
        "portfolio_evidence": ["Jupyter notebooks showing reproducible EDA and CV iterations", "Modular training scripts (.py)", "SHAP summary plots demonstrating feature impact"],
        "bullet_template": "Trained and cross-validated an XGBoost classification pipeline achieving 89% F1-score across 5-fold CV, leveraging SHAP to quantify top feature drivers.",
    },
    "Statistics & Probability": {
        "why_it_matters": "Guarantees scientific rigor in evaluating experimental results and guards against false discoveries.",
        "prerequisites": ["High-school mathematics", "Basic calculus"],
        "foundation": ["Descriptive Statistics (Mean, Median, Std, IQR, Skewness)", "Probability Distributions (Normal, Binomial, Poisson)", "Central Limit Theorem", "Standard Error & Confidence Intervals"],
        "intermediate": ["Hypothesis Testing Framework (Null vs Alternative, Type I & II errors)", "One-sample & Two-sample t-tests", "Mann-Whitney U (Non-parametric tests)", "Chi-Square Test of Independence", "Cohen's d Effect Size"],
        "advanced": ["A/B Testing experimental design (Sample size determination, Power analysis, Minimum Detectable Effect)", "Multiple testing corrections (Bonferroni, FDR)", "Bayesian vs Frequentist inference", "ANOVA & MANOVA"],
        "practice": ["Conduct two-sample hypothesis tests in SciPy verifying normality with Shapiro-Wilk test", "Design an end-to-end A/B test with sample size power calculation"],
        "mini_project": "E-Commerce Conversion A/B Test Evaluation: Compute p-value, statistical power, and 95% confidence interval for conversion lift.",
        "main_project": "Comprehensive Statistical Investigation & Empirical Approach Note: Rigorous hypothesis testing across multiple cohorts, normality verification, effect sizes (Cohen's d), and business limitation documentation.",
        "validation_milestone": "Document assumptions, test statistics, p-values, effect sizes, and practical business interpretations without causal overreach.",
        "portfolio_evidence": ["Reproducible Python/R statistical analysis notebook", "Statistical power calculation report", "Data visualization charts displaying confidence intervals"],
        "bullet_template": "Designed and evaluated A/B testing protocols (N=25K) using SciPy, computing statistical power, Cohen's d effect sizes, and 95% CIs to guide product decisions.",
    },
    "Data Storytelling & Dashboards": {
        "why_it_matters": "Bridges the gap between raw data science algorithms and executive business decisions.",
        "prerequisites": ["Data understanding", "Basic visualization principles"],
        "foundation": ["Chart selection principles (Bar, Line, Scatter, Heatmap, Box plot)", "Color palettes & visual hierarchy", "KPI Card design", "Filtering and interactivity"],
        "intermediate": ["Building interactive dashboards in Streamlit / Plotly / Tableau / Power BI", "Drill-down views", "Executive summaries", "Structuring a business narrative"],
        "advanced": ["Designing for stakeholder personas (Execs vs Technical)", "Optimizing dashboard render latency", "Embedding statistical confidence into visual graphs", "User testing & feedback loops"],
        "practice": ["Re-design a cluttered multi-chart spreadsheet into a clean 3-panel executive view", "Build interactive Plotly visualizations with custom tooltips"],
        "mini_project": "Sales KPI Executive Cockpit: Interactive 4-card KPI summary with dynamic filtering by region and time.",
        "main_project": "Comprehensive Career Intelligence & Executive Decision-Support Dashboard: End-to-end interactive Streamlit application featuring distribution charts, ML confusion matrices, and dynamic recommendation cards.",
        "validation_milestone": "Deliver a fully responsive interactive dashboard with intuitive navigation and sub-second filtering.",
        "portfolio_evidence": ["Live deployed Streamlit/Tableau public dashboard link", "High-resolution dashboard screenshots", "Executive 1-page summary PDF"],
        "bullet_template": "Built interactive Plotly/Streamlit executive dashboard tracking 15+ KPIs across 17K+ records, enabling leadership to identify critical market patterns.",
    },
}


def generate_learning_roadmaps_for_gaps(gaps: list[PrioritySkillGap]) -> list[LearningRoadmapStep]:
    """Generate tailored step-by-step learning roadmaps for every high and medium priority skill gap."""
    roadmaps = []
    
    for gap in gaps:
        template = ROADMAP_TEMPLATES.get(gap.skill_name)
        if not template:
            # Fallback dynamic template based on category
            template = {
                "why_it_matters": f"Core competency in {gap.category} required by industry practitioners.",
                "prerequisites": ["Basic quantitative and computing principles"],
                "foundation": [f"Core syntax and foundational concepts of {gap.skill_name}", "Environment setup and standard tooling"],
                "intermediate": [f"Applied workflows and data transformations using {gap.skill_name}", "Integration with standard analytics pipelines"],
                "advanced": [f"Performance optimization, error handling, and production best practices in {gap.skill_name}", "Advanced domain applications"],
                "practice": [f"Solve 15+ guided exercises focusing on {gap.skill_name} core functionalities"],
                "mini_project": f"{gap.skill_name} Implementation Benchmark: Build a working script demonstrating core features.",
                "main_project": f"End-to-End {gap.skill_name} Applied Solution: Design, implement, and document a full-scale project solving a practical business problem.",
                "validation_milestone": f"Demonstrate working implementation of {gap.skill_name} with clean code and verifiable results.",
                "portfolio_evidence": [f"Public GitHub repository containing {gap.skill_name} code", "Technical documentation README", "Output charts or metrics"],
                "bullet_template": f"Implemented {gap.skill_name} solution to automate data workflows, improving operational efficiency and analytical accuracy.",
            }
            
        roadmaps.append(
            LearningRoadmapStep(
                skill_name=gap.skill_name,
                priority=gap.priority_level,
                why_it_matters=template["why_it_matters"],
                prerequisites=template["prerequisites"],
                foundation_topics=template["foundation"],
                intermediate_topics=template["intermediate"],
                advanced_topics=template["advanced"],
                practice_tasks=template["practice"],
                mini_project=template["mini_project"],
                main_portfolio_project=template["main_project"],
                validation_milestone=template["validation_milestone"],
                portfolio_evidence_criteria=template["portfolio_evidence"],
                resume_bullet_template=template["bullet_template"],
            )
        )
    return roadmaps


def generate_resume_improvement_recommendations(parsed_resume: ParsedResume) -> list[ResumeImprovementTip]:
    """Generate concrete, actionable resume bullet-point and formatting improvement advice."""
    tips = []
    
    # 1. Action Verbs Optimization
    tips.append(
        ResumeImprovementTip(
            section="Bullet Points & Impact",
            finding_observation="Enhance passive duty statements with high-impact technical action verbs.",
            actionable_advice="Begin every bullet point with strong action verbs: 'Architected', 'Engineered', 'Optimized', 'Trained', 'Cross-validated'.",
            before_example="Responsible for making charts and running scripts.",
            after_example="Engineered automated Plotly visualizations to track model error matrices and feature drift across evaluation cycles.",
        )
    )
    
    # 2. Measurable Outcomes & Quantified Results
    tips.append(
        ResumeImprovementTip(
            section="Projects & Experience",
            finding_observation="Ensure every project bullet includes measurable quantitative outcomes (accuracy %, latency, scale).",
            actionable_advice="Incorporate quantifiable metrics using the Google XYZ formula: 'Accomplished [X], measured by [Y], by doing [Z]'.",
            before_example="Worked on machine learning model to predict customer churn.",
            after_example="Developed an XGBoost churn prediction model (N=50K) achieving 87% F1-score across 5-fold CV, identifying high-risk accounts.",
        )
    )
    
    # 3. Technical Alignment & Tool Context
    tips.append(
        ResumeImprovementTip(
            section="Technical Skills Section",
            finding_observation="Group technical skills by domain and ensure each skill is evidenced in project descriptions.",
            actionable_advice="Structure skills into distinct categories (Languages, ML/AI, Visualization, Cloud) and reference them in project workflows.",
            before_example="Skills: Python, SQL, ML, Tableau, AWS, Git.",
            after_example="Languages: Python, SQL | ML/AI: Scikit-Learn, XGBoost | BI: Tableau, Plotly | Cloud: AWS, Docker",
        )
    )
    
    # 4. Professional Portfolio Proof
    if parsed_resume.contact.github == "Not detected" or parsed_resume.contact.linkedin == "Not detected":
        tips.append(
            ResumeImprovementTip(
                section="Header / Contact Info",
                finding_observation="Professional profile links (GitHub / LinkedIn) should be prominently visible in the header.",
                actionable_advice="Add active GitHub and LinkedIn profile URLs to provide immediate verifiable proof of code quality and project execution.",
                before_example="John Doe | john@email.com | (555) 019-2834",
                after_example="John Doe | john@email.com | github.com/johndoe | linkedin.com/in/johndoe",
            )
        )
    
    return tips
