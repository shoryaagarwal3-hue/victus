"""Market Analytics Service for SAS Datasets.
Analyzes:
1. DataScience Jobs (Company hiring volumes, average salaries in Lakhs, experience requirements)
2. Analytics Jobs (Location distributions, experience bands, key skill frequencies, salary brackets)
"""
import re
from collections import Counter
from typing import Any
import pandas as pd
import numpy as np

from .sas_models import MarketDistributionSummary


def extract_skill_frequencies(key_skills_series: pd.Series, top_n: int = 25) -> dict[str, int]:
    """Tokenize and count skill frequencies from comma/pipe/whitespace delimited skill strings."""
    tokens = []
    # Curated canonical skill matcher for tech/analytics
    canonical_skills = [
        "python", "sql", "sas", "r", "machine learning", "tableau", "power bi",
        "excel", "spark", "aws", "azure", "deep learning", "nlp", "statistics",
        "big data", "hadoop", "c++", "java", "data mining", "data analysis",
        "scikit-learn", "tensorflow", "pytorch", "git", "scala", "docker",
    ]
    
    for text in key_skills_series.dropna():
        text_lower = str(text).lower()
        for skill in canonical_skills:
            if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                tokens.append(skill.title() if len(skill) > 3 else skill.upper())
                
    counts = Counter(tokens)
    return dict(counts.most_common(top_n))


def extract_experience_bands(exp_series: pd.Series) -> dict[str, int]:
    """Classify raw experience strings into standardized industry experience bands."""
    bands = {
        "Entry Level (0-2 yrs)": 0,
        "Mid Level (3-5 yrs)": 0,
        "Senior Level (6-10 yrs)": 0,
        "Lead / Principal (10+ yrs)": 0,
    }
    
    for val in exp_series.dropna():
        v_str = str(val).lower()
        # Find first number
        nums = [int(n) for n in re.findall(r"\d+", v_str)]
        if nums:
            min_exp = nums[0]
            if min_exp <= 2:
                bands["Entry Level (0-2 yrs)"] += 1
            elif min_exp <= 5:
                bands["Mid Level (3-5 yrs)"] += 1
            elif min_exp <= 10:
                bands["Senior Level (6-10 yrs)"] += 1
            else:
                bands["Lead / Principal (10+ yrs)"] += 1
        else:
            bands["Entry Level (0-2 yrs)"] += 1
            
    return bands


def extract_location_distributions(loc_series: pd.Series, top_n: int = 10) -> dict[str, int]:
    """Count postings by primary metropolitan tech clusters."""
    locs = []
    clusters = ["Bengaluru", "Hyderabad", "Pune", "Mumbai", "Delhi", "Chennai", "Kolkata", "Noida", "Gurgaon", "Ahmedabad"]
    
    for val in loc_series.dropna():
        v_str = str(val).title()
        for c in clusters:
            if c.lower() in v_str.lower():
                locs.append(c)
                break
                
    counts = Counter(locs)
    return dict(counts.most_common(top_n))


def summarize_market_landscape(analytics_df: pd.DataFrame, ds_jobs_df: pd.DataFrame) -> MarketDistributionSummary:
    """Generate comprehensive market distribution summary."""
    total_postings = len(analytics_df) + len(ds_jobs_df)
    
    # Top hiring companies from DataScience Jobs (weighted by num_of_jobs if present)
    if "num_of_jobs" in ds_jobs_df.columns and "company_name" in ds_jobs_df.columns:
        comp_counts = ds_jobs_df.groupby("company_name")["num_of_jobs"].sum().sort_values(ascending=False).head(10).to_dict()
    else:
        comp_counts = ds_jobs_df["company_name"].value_counts().head(10).to_dict()
    top_companies = {str(k): int(v) for k, v in comp_counts.items()}
    unique_companies = int(ds_jobs_df["company_name"].nunique()) if "company_name" in ds_jobs_df.columns else 0
    
    exp_bands = extract_experience_bands(analytics_df["experience"] if "experience" in analytics_df.columns else pd.Series())
    top_skills = extract_skill_frequencies(analytics_df["key_skills"] if "key_skills" in analytics_df.columns else pd.Series())
    top_locations = extract_location_distributions(analytics_df["location"] if "location" in analytics_df.columns else pd.Series())
    
    # Salary statistics from DataScience Jobs
    salary_stats = {}
    if "avg_salary_lakhs" in ds_jobs_df.columns:
        valid_sal = ds_jobs_df["avg_salary_lakhs"].dropna()
        if len(valid_sal) > 0:
            salary_stats = {
                "mean_salary_lakhs": round(float(valid_sal.mean()), 2),
                "median_salary_lakhs": round(float(valid_sal.median()), 2),
                "min_salary_lakhs": round(float(valid_sal.min()), 2),
                "max_salary_lakhs": round(float(valid_sal.max()), 2),
                "q25_salary_lakhs": round(float(np.percentile(valid_sal, 25)), 2),
                "q75_salary_lakhs": round(float(np.percentile(valid_sal, 75)), 2),
            }
            
    return MarketDistributionSummary(
        total_postings_analyzed=total_postings,
        unique_companies=unique_companies,
        top_hiring_companies=top_companies,
        experience_bands=exp_bands,
        top_key_skills=top_skills,
        top_locations=top_locations,
        salary_summary_lakhs=salary_stats,
    )
