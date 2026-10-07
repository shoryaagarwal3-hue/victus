"""Skill Extraction & Normalization Service for Resumes and Job Descriptions.
Maps raw terms, abbreviations, and multi-word phrases to standardized canonical skills,
categorizes them into tech domains, and distinguishes mentioned vs demonstrated proficiency.
"""
import re
from typing import NamedTuple
from .resume_models import ExtractedSkill, ParsedResume


class SkillTaxonomyEntry(NamedTuple):
    canonical_name: str
    category: str
    aliases: list[str]
    regex_pattern: str


# Comprehensive Data Science & Analytics Taxonomy
TAXONOMY: list[SkillTaxonomyEntry] = [
    # 1. Programming Languages
    SkillTaxonomyEntry("Python", "Programming Languages", ["python", "python3", "py"], r"\b(?:python\s*3?|py)\b"),
    SkillTaxonomyEntry("R", "Programming Languages", ["r language", "r programming", "r-project"], r"\b(?:r\s+(?:programming|language|scripting)|r-project)\b|,\s*R\s*[,/|\n]"),
    SkillTaxonomyEntry("SQL", "Programming Languages", ["sql", "structured query language", "t-sql", "pl/sql"], r"\b(?:sql|t-sql|pl/sql|structured\s+query\s+language)\b"),
    SkillTaxonomyEntry("SAS", "Programming Languages", ["sas", "sas base", "sas enterprise"], r"\b(?:sas(?:\s+(?:base|enterprise|viya|studio))?)\b"),
    SkillTaxonomyEntry("Scala", "Programming Languages", ["scala"], r"\bscala\b"),
    SkillTaxonomyEntry("Java", "Programming Languages", ["java", "core java"], r"\b(?:core\s+)?java\b"),
    SkillTaxonomyEntry("C++", "Programming Languages", ["c++", "cpp"], r"\b(?:c\+\+|cpp)\b"),
    SkillTaxonomyEntry("Julia", "Programming Languages", ["julia"], r"\bjulia\b"),
    SkillTaxonomyEntry("MATLAB", "Programming Languages", ["matlab"], r"\bmatlab\b"),
    SkillTaxonomyEntry("Bash / Shell", "Programming Languages", ["bash", "shell scripting", "sh"], r"\b(?:bash|shell\s+scripting|sh)\b"),

    # 2. Machine Learning & AI
    SkillTaxonomyEntry("Machine Learning", "Machine Learning & AI", ["machine learning", "ml", "statistical learning"], r"\b(?:machine\s+learning|statistical\s+learning|\bml\b)\b"),
    SkillTaxonomyEntry("Deep Learning", "Machine Learning & AI", ["deep learning", "dl", "neural nets"], r"\b(?:deep\s+learning|\bdl\b|neural\s+networks?)\b"),
    SkillTaxonomyEntry("Scikit-Learn", "Machine Learning & AI", ["scikit-learn", "sklearn", "scikit"], r"\b(?:scikit-learn|sklearn|scikit)\b"),
    SkillTaxonomyEntry("PyTorch", "Machine Learning & AI", ["pytorch", "torch"], r"\b(?:pytorch|torch)\b"),
    SkillTaxonomyEntry("TensorFlow", "Machine Learning & AI", ["tensorflow", "tf", "keras"], r"\b(?:tensorflow|\btf\b|keras)\b"),
    SkillTaxonomyEntry("XGBoost", "Machine Learning & AI", ["xgboost", "lightgbm", "catboost", "gradient boosting"], r"\b(?:xgboost|lightgbm|catboost|gradient\s+boosting|gbm)\b"),
    SkillTaxonomyEntry("Natural Language Processing (NLP)", "Machine Learning & AI", ["nlp", "natural language processing", "text mining"], r"\b(?:natural\s+language\s+processing|\bnlp\b|text\s+mining|sentiment\s+analysis)\b"),
    SkillTaxonomyEntry("Computer Vision", "Machine Learning & AI", ["computer vision", "cv", "opencv", "image processing"], r"\b(?:computer\s+vision|opencv|image\s+processing|\bcv\b)\b"),
    SkillTaxonomyEntry("Large Language Models (LLMs)", "Machine Learning & AI", ["llm", "large language models", "genai", "rag", "transformers"], r"\b(?:large\s+language\s+models?|\bllms?\b|generative\s+ai|\bgenai\b|\brag\b|transformers?|langchain|llamaindex)\b"),
    SkillTaxonomyEntry("Supervised & Unsupervised Learning", "Machine Learning & AI", ["clustering", "classification", "regression", "random forest", "decision trees", "svm", "logistic regression"], r"\b(?:classification|clustering|k-means|random\s+forest|decision\s+trees?|svm|support\s+vector|logistic\s+regression)\b"),

    # 3. Quantitative & Statistical Analysis
    SkillTaxonomyEntry("Statistics & Probability", "Quantitative & Statistics", ["statistics", "probability", "statistical modeling"], r"\b(?:statistics|probability|statistical\s+modeling|biostatistics)\b"),
    SkillTaxonomyEntry("Hypothesis Testing & A/B Testing", "Quantitative & Statistics", ["hypothesis testing", "a/b testing", "experimentation", "p-value", "t-test", "anova"], r"\b(?:hypothesis\s+testing|a/b\s+testing|experimentation|t-tests?|anova|chi-square|mann-whitney)\b"),
    SkillTaxonomyEntry("Time Series Analysis", "Quantitative & Statistics", ["time series", "arima", "prophet", "forecasting"], r"\b(?:time\s+series|forecasting|arima|sarima|prophet)\b"),
    SkillTaxonomyEntry("Linear Algebra & Calculus", "Quantitative & Statistics", ["linear algebra", "multivariate calculus", "optimization"], r"\b(?:linear\s+algebra|calculus|matrix\s+decomposition|optimization)\b"),

    # 4. Big Data & Distributed Computing
    SkillTaxonomyEntry("Apache Spark", "Big Data & Distributed Systems", ["spark", "pyspark", "spark sql"], r"\b(?:apache\s+spark|pyspark|spark(?:\s+sql)?)\b"),
    SkillTaxonomyEntry("Hadoop & Hive", "Big Data & Distributed Systems", ["hadoop", "hive", "mapreduce", "hdfs"], r"\b(?:hadoop|hive|mapreduce|hdfs)\b"),
    SkillTaxonomyEntry("Apache Kafka", "Big Data & Distributed Systems", ["kafka", "streaming", "event streaming"], r"\b(?:apache\s+kafka|kafka|event\s+streaming)\b"),
    SkillTaxonomyEntry("Apache Airflow", "Big Data & Distributed Systems", ["airflow", "workflow orchestration", "data pipelines"], r"\b(?:apache\s+airflow|airflow|dag\s+orchestration)\b"),
    SkillTaxonomyEntry("Databricks & Snowflake", "Big Data & Distributed Systems", ["databricks", "snowflake", "bigquery", "redshift"], r"\b(?:databricks|snowflake|bigquery|redshift|synapse)\b"),

    # 5. Data Visualization & Storytelling
    SkillTaxonomyEntry("Tableau", "Data Visualization & Storytelling", ["tableau", "tableau desktop", "tableau server"], r"\btableau(?:\s+(?:desktop|server|public))?\b"),
    SkillTaxonomyEntry("Power BI", "Data Visualization & Storytelling", ["power bi", "powerbi", "dax", "power query"], r"\b(?:power\s*bi|dax|power\s+query)\b"),
    SkillTaxonomyEntry("Matplotlib & Seaborn", "Data Visualization & Storytelling", ["matplotlib", "seaborn", "plotly", "ggplot"], r"\b(?:matplotlib|seaborn|plotly|ggplot2?)\b"),
    SkillTaxonomyEntry("Excel & Advanced Analytics", "Data Visualization & Storytelling", ["excel", "vlookup", "pivot tables", "vba", "advanced excel"], r"\b(?:advanced\s+excel|microsoft\s+excel|pivot\s+tables?|vba|vlookup)\b"),
    SkillTaxonomyEntry("Data Storytelling & Dashboards", "Data Visualization & Storytelling", ["data storytelling", "dashboard design", "kpi reporting", "business intelligence"], r"\b(?:data\s+storytelling|dashboard\s+design|kpi\s+reporting|business\s+intelligence|\bbi\b)\b"),

    # 6. Databases & Data Engineering
    SkillTaxonomyEntry("PostgreSQL", "Databases & Data Engineering", ["postgresql", "postgres"], r"\b(?:postgresql|postgres)\b"),
    SkillTaxonomyEntry("MySQL", "Databases & Data Engineering", ["mysql"], r"\bmysql\b"),
    SkillTaxonomyEntry("MongoDB & NoSQL", "Databases & Data Engineering", ["mongodb", "nosql", "cassandra", "dynamodb", "redis"], r"\b(?:mongodb|nosql|cassandra|dynamodb|redis)\b"),
    SkillTaxonomyEntry("ETL & Data Warehousing", "Databases & Data Engineering", ["etl", "elt", "data warehousing", "data modeling", "dbt"], r"\b(?:etl|elt|data\s+warehousing|data\s+modeling|\bdbt\b|star\s+schema)\b"),

    # 7. Cloud, DevOps & MLOps
    SkillTaxonomyEntry("AWS", "Cloud & MLOps", ["aws", "amazon web services", "s3", "ec2", "sagemaker"], r"\b(?:aws|amazon\s+web\s+services|s3|ec2|sagemaker|lambda)\b"),
    SkillTaxonomyEntry("Microsoft Azure", "Cloud & MLOps", ["azure", "azure ml", "azure devops"], r"\b(?:azure|azure\s+ml|azure\s+devops|blob\s+storage)\b"),
    SkillTaxonomyEntry("Google Cloud Platform (GCP)", "Cloud & MLOps", ["gcp", "google cloud", "vertex ai"], r"\b(?:gcp|google\s+cloud|vertex\s+ai)\b"),
    SkillTaxonomyEntry("Docker & Kubernetes", "Cloud & MLOps", ["docker", "kubernetes", "k8s", "containerization"], r"\b(?:docker|kubernetes|k8s|containers?)\b"),
    SkillTaxonomyEntry("Git & GitHub", "Cloud & MLOps", ["git", "github", "gitlab", "version control"], r"\b(?:git|github|gitlab|version\s+control)\b"),
    SkillTaxonomyEntry("MLOps & Model Deployment", "Cloud & MLOps", ["mlops", "model deployment", "fastapi", "flask", "streamlit", "mlflow"], r"\b(?:mlops|model\s+deployment|fastapi|flask|streamlit|mlflow|dvc|ci/cd)\b"),
]


def extract_skills_from_text(text: str, source_section: str = "General") -> list[ExtractedSkill]:
    """Extract and normalize all skills occurring in text."""
    extracted = []
    text_lower = text.lower()
    
    # Action verbs indicating demonstrated project work
    demo_verbs = ["built", "developed", "trained", "deployed", "implemented", "optimized", "engineered", "designed", "analyzed", "evaluated"]
    is_section_demonstrated = source_section.lower() in ("projects", "experience")
    
    for entry in TAXONOMY:
        match = re.search(entry.regex_pattern, text, re.IGNORECASE)
        if match:
            matched_snippet = text[max(0, match.start() - 30) : min(len(text), match.end() + 30)].strip()
            
            # Check if demonstrated with action verbs or in projects/experience
            is_demo = is_section_demonstrated or any(verb in text_lower for verb in demo_verbs)
            
            extracted.append(
                ExtractedSkill(
                    raw_text=match.group(0),
                    normalized_name=entry.canonical_name,
                    category=entry.category,
                    source_section=source_section,
                    confidence=1.0,
                    is_demonstrated=is_demo,
                    context_snippet=matched_snippet,
                )
            )
            
    return extracted


def extract_all_resume_skills(parsed_resume: ParsedResume) -> list[ExtractedSkill]:
    """Scan all resume sections and aggregate unique normalized skills with highest evidence level."""
    skill_map: dict[str, ExtractedSkill] = {}
    
    # 1. Skills from Projects (High evidence)
    for proj in parsed_resume.projects:
        proj_text = f"{proj.title} {proj.description}"
        proj_skills = extract_skills_from_text(proj_text, source_section="Projects")
        for s in proj_skills:
            s.is_demonstrated = True
            skill_map[s.normalized_name] = s
            proj.technologies_used.append(s.normalized_name)
            
    # 2. Skills from Experience (High evidence)
    for exp in parsed_resume.experience:
        exp_text = f"{exp.role} {exp.organization} {' '.join(exp.responsibilities)}"
        exp_skills = extract_skills_from_text(exp_text, source_section="Experience")
        for s in exp_skills:
            s.is_demonstrated = True
            if s.normalized_name not in skill_map or not skill_map[s.normalized_name].is_demonstrated:
                skill_map[s.normalized_name] = s
            exp.technologies_used.append(s.normalized_name)
            
    # 3. Skills from raw resume text (Catches skills section, headers, etc.)
    all_text_skills = extract_skills_from_text(parsed_resume.raw_text, source_section="Skills Section")
    for s in all_text_skills:
        if s.normalized_name not in skill_map:
            skill_map[s.normalized_name] = s
            
    unique_skills = list(skill_map.values())
    parsed_resume.extracted_skills = unique_skills
    return unique_skills
