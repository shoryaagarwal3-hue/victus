"""Data Loader for official SAS Hackathon Datasets.
Loads:
1. Analytics Jobs.csv
2. DataScience Jobs.csv
3. JDS Skill Traits.xlsx
4. SDS Personality Traits.xlsx
Provides strict schema validation and path resolution.
"""
from pathlib import Path
from typing import NamedTuple
import pandas as pd

# Default relative paths from project root
BASE_DIR = Path(__file__).resolve().parents[1]
SAS_DATA_DIR = BASE_DIR / "SAS Data Problem Statement and Instructions Hackathon"

ANALYTICS_JOBS_FILE = SAS_DATA_DIR / "Analytics Jobs.csv"
DATASCIENCE_JOBS_FILE = SAS_DATA_DIR / "DataScience Jobs.csv"
JDS_SKILLS_FILE = SAS_DATA_DIR / "JDS Skill Traits.xlsx"
SDS_PERSONALITY_FILE = SAS_DATA_DIR / "SDS Personality Traits.xlsx"


class SASDatasets(NamedTuple):
    analytics_jobs: pd.DataFrame
    datascience_jobs: pd.DataFrame
    jds_skills: pd.DataFrame
    sds_personality: pd.DataFrame


def load_analytics_jobs(path: Path | str | None = None) -> pd.DataFrame:
    """Load Analytics Jobs CSV dataset."""
    file_path = Path(path) if path else ANALYTICS_JOBS_FILE
    if not file_path.exists():
        raise FileNotFoundError(f"Analytics Jobs dataset not found at {file_path}")
    
    df = pd.read_csv(file_path)
    expected_cols = ["s_no", "experience", "job_description", "job_desig", "job_type", "key_skills", "location", "salary"]
    for col in expected_cols:
        if col not in df.columns:
            raise ValueError(f"Expected column '{col}' missing from Analytics Jobs dataset")
    return df


def load_datascience_jobs(path: Path | str | None = None) -> pd.DataFrame:
    """Load DataScience Jobs CSV dataset."""
    file_path = Path(path) if path else DATASCIENCE_JOBS_FILE
    if not file_path.exists():
        raise FileNotFoundError(f"DataScience Jobs dataset not found at {file_path}")
    
    df = pd.read_csv(file_path)
    expected_cols = ["reference_no", "company_name", "job_title", "min_experience", "avg_salary", "min_salary", "max_salary", "num_of_jobs"]
    for col in expected_cols:
        if col not in df.columns:
            raise ValueError(f"Expected column '{col}' missing from DataScience Jobs dataset")
    return df


def load_jds_skills(path: Path | str | None = None) -> pd.DataFrame:
    """Load Junior Data Scientist (JDS) Skill Traits Excel dataset."""
    file_path = Path(path) if path else JDS_SKILLS_FILE
    if not file_path.exists():
        raise FileNotFoundError(f"JDS Skill Traits dataset not found at {file_path}")
    
    df = pd.read_excel(file_path)
    expected_cols = ["id", "big_data_skills", "maths-stats_skills", "coding_skills", "ai_and_ml_skills", "dashboard_and_storytelling_skills", "salary_hike_high_or_low"]
    for col in expected_cols:
        if col not in df.columns:
            raise ValueError(f"Expected column '{col}' missing from JDS Skill Traits dataset")
    return df


def load_sds_personality(path: Path | str | None = None) -> pd.DataFrame:
    """Load Senior Data Scientist (SDS) Personality Traits Excel dataset.
    Normalizes column whitespace cleanly while maintaining data integrity.
    """
    file_path = Path(path) if path else SDS_PERSONALITY_FILE
    if not file_path.exists():
        raise FileNotFoundError(f"SDS Personality Traits dataset not found at {file_path}")
    
    df = pd.read_excel(file_path)
    # Strip whitespace from column names to handle raw file inconsistencies like ' extraversion'
    df.columns = [c.strip() for c in df.columns]
    
    # Normalize success classification column name
    rename_map = {}
    for col in df.columns:
        if "success" in col.lower() and "classification" in col.lower():
            rename_map[col] = "success_classification_high_low"
    if rename_map:
        df = df.rename(columns=rename_map)
        
    expected_cols = ["id", "neuroticism", "extraversion", "openness_to_experience", "agreeableness", "conscientiousness", "success_classification_high_low"]
    for col in expected_cols:
        if col not in df.columns:
            raise ValueError(f"Expected column '{col}' missing from normalized SDS Personality Traits dataset")
    return df


def load_all_datasets(custom_dir: Path | str | None = None) -> SASDatasets:
    """Load all 4 official SAS datasets into memory."""
    target_dir = Path(custom_dir) if custom_dir else SAS_DATA_DIR
    return SASDatasets(
        analytics_jobs=load_analytics_jobs(target_dir / "Analytics Jobs.csv"),
        datascience_jobs=load_datascience_jobs(target_dir / "DataScience Jobs.csv"),
        jds_skills=load_jds_skills(target_dir / "JDS Skill Traits.xlsx"),
        sds_personality=load_sds_personality(target_dir / "SDS Personality Traits.xlsx"),
    )
