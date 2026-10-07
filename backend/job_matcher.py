"""Deterministic Job Description Analysis and Resume-to-Job Matching Engine.
Evaluates Required Skills, Preferred Skills, Project Evidence, Experience Fit, and Education Fit.
Does NOT use any legacy curriculum drift or CPS formulas.
"""
import re
from typing import Any
from .resume_models import (
    JobDescriptionRequirement,
    ParsedResume,
    ResumeMatchResult,
    SkillMatchDetail,
)
from .resume_skill_extractor import extract_skills_from_text, TAXONOMY


# Curated Standard Role Templates
STANDARD_ROLES: dict[str, JobDescriptionRequirement] = {
    "Junior Data Scientist": JobDescriptionRequirement(
        role_title="Junior Data Scientist",
        required_skills=["Python", "SQL", "Machine Learning", "Scikit-Learn", "Statistics & Probability", "Data Storytelling & Dashboards"],
        preferred_skills=["Tableau", "Power BI", "Git & GitHub", "Supervised & Unsupervised Learning", "Matplotlib & Seaborn"],
        supporting_skills=["Apache Spark", "Docker & Kubernetes", "AWS", "Deep Learning"],
        min_experience_years=0.0,
        preferred_education="Bachelor's in Computer Science, Data Science, Statistics, Mathematics, or STEM",
        responsibilities_summary=[
            "Develop, validate, and document machine learning classification and regression models.",
            "Write robust SQL queries and Python scripts for data manipulation and exploratory analysis.",
            "Build interactive dashboards and translate analytical findings into business presentations.",
        ],
    ),
    "Senior Data Scientist": JobDescriptionRequirement(
        role_title="Senior Data Scientist",
        required_skills=["Python", "SQL", "Machine Learning", "Deep Learning", "Statistics & Probability", "Hypothesis Testing & A/B Testing", "MLOps & Model Deployment"],
        preferred_skills=["PyTorch", "TensorFlow", "Apache Spark", "AWS", "Docker & Kubernetes", "Databricks & Snowflake"],
        supporting_skills=["Natural Language Processing (NLP)", "Large Language Models (LLMs)", "Time Series Analysis"],
        min_experience_years=5.0,
        preferred_education="Master's or Ph.D. in Data Science, Computer Science, Statistics, or Quantitative discipline",
        responsibilities_summary=[
            "Lead end-to-end data science initiatives from problem formulation to production deployment.",
            "Mentor junior data scientists and collaborate with executive stakeholders on model governance.",
            "Design rigorous A/B testing frameworks and maintain production MLOps pipelines.",
        ],
    ),
    "Data Analyst / Business Analytics Specialist": JobDescriptionRequirement(
        role_title="Data Analyst / Business Analytics Specialist",
        required_skills=["SQL", "Excel & Advanced Analytics", "Tableau", "Power BI", "Data Storytelling & Dashboards", "Statistics & Probability"],
        preferred_skills=["Python", "PostgreSQL", "ETL & Data Warehousing", "Matplotlib & Seaborn"],
        supporting_skills=["SAS", "R", "Git & GitHub", "Time Series Analysis"],
        min_experience_years=1.0,
        preferred_education="Bachelor's in Business Analytics, Economics, Computer Science, or Quantitative field",
        responsibilities_summary=[
            "Extract, clean, and analyze transactional and customer data using advanced SQL.",
            "Build, publish, and maintain executive Tableau and Power BI KPI dashboards.",
            "Perform ad-hoc statistical investigations and present findings to leadership.",
        ],
    ),
    "Machine Learning Engineer": JobDescriptionRequirement(
        role_title="Machine Learning Engineer",
        required_skills=["Python", "PyTorch", "TensorFlow", "Scikit-Learn", "Docker & Kubernetes", "MLOps & Model Deployment", "Git & GitHub", "SQL"],
        preferred_skills=["AWS", "Microsoft Azure", "Apache Kafka", "Apache Spark", "Large Language Models (LLMs)"],
        supporting_skills=["C++", "Scala", "ETL & Data Warehousing", "Computer Vision"],
        min_experience_years=2.0,
        preferred_education="Bachelor's or Master's in Computer Science, Software Engineering, or Machine Learning",
        responsibilities_summary=[
            "Design, containerize, and deploy scalable machine learning inference microservices via FastAPI/Docker.",
            "Maintain automated CI/CD and MLOps model monitoring pipelines using MLflow.",
            "Optimize model latency, throughput, and GPU utilization for production workloads.",
        ],
    ),
}


def parse_job_description_text(jd_text: str, role_title: str = "Custom Job Requirement") -> JobDescriptionRequirement:
    """Extract required and preferred skills from raw Job Description text."""
    if not jd_text.strip():
        return STANDARD_ROLES.get("Junior Data Scientist", list(STANDARD_ROLES.values())[0])
        
    extracted = extract_skills_from_text(jd_text, source_section="Job Description")
    skill_names = [s.normalized_name for s in extracted]
    
    # Heuristic segmentation of required vs preferred
    lines = jd_text.split("\n")
    req_skills = []
    pref_skills = []
    supp_skills = []
    
    is_preferred_section = False
    for line in lines:
        l_lower = line.lower()
        if any(h in l_lower for h in ["preferred", "nice to have", "plus", "bonus", "optional"]):
            is_preferred_section = True
        elif any(h in l_lower for h in ["required", "must have", "qualifications", "core skills", "responsibilities"]):
            is_preferred_section = False
            
        line_skills = [s.normalized_name for s in extract_skills_from_text(line)]
        for s in line_skills:
            if is_preferred_section:
                if s not in pref_skills:
                    pref_skills.append(s)
            else:
                if s not in req_skills:
                    req_skills.append(s)
                    
    # Balance if everything fell into required
    if not pref_skills and len(req_skills) > 4:
        pref_skills = req_skills[4:]
        req_skills = req_skills[:4]
    elif not req_skills and pref_skills:
        req_skills = pref_skills[:3]
        pref_skills = pref_skills[3:]
    elif not req_skills and not pref_skills:
        # Fallback to standard JDS skills if JD has no recognized keywords
        req_skills = ["Python", "SQL", "Machine Learning", "Statistics & Probability"]
        pref_skills = ["Tableau", "Power BI", "Scikit-Learn"]
        
    # Extract minimum experience if mentioned
    exp_match = re.search(r"(\d+)\+?\s*(?:to\s*\d+)?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)", jd_text, re.IGNORECASE)
    min_exp = float(exp_match.group(1)) if exp_match else 1.0
    
    return JobDescriptionRequirement(
        role_title=role_title,
        raw_text=jd_text,
        required_skills=req_skills,
        preferred_skills=pref_skills,
        supporting_skills=supp_skills,
        min_experience_years=min_exp,
        preferred_education="Bachelor's or Master's in CS / Quantitative discipline",
    )


def match_resume_to_job(
    parsed_resume: ParsedResume,
    job_req: JobDescriptionRequirement,
    market_skill_counts: dict[str, int] | None = None,
) -> ResumeMatchResult:
    """Compute deterministic Resume Match Score across 5 auditable dimensions."""
    market_counts = market_skill_counts or {}
    
    # Candidate skills mapping
    resume_skills_map = {s.normalized_name: s for s in parsed_resume.extracted_skills}
    
    req_skills = job_req.required_skills
    pref_skills = job_req.preferred_skills
    
    # 1. Required Skill Coverage
    matched_req = [s for s in req_skills if s in resume_skills_map]
    req_pct = (len(matched_req) / len(req_skills) * 100.0) if req_skills else 100.0
    
    # 2. Preferred Skill Coverage
    matched_pref = [s for s in pref_skills if s in resume_skills_map]
    pref_pct = (len(matched_pref) / len(pref_skills) * 100.0) if pref_skills else 100.0
    
    # 3. Project Evidence Score
    # Evaluates whether skills are demonstrated with measurable project context
    demonstrated_skills = [s for s in parsed_resume.extracted_skills if s.is_demonstrated]
    has_metrics = any(len(p.measurable_outcomes) > 0 for p in parsed_resume.projects)
    proj_evidence_score = min(len(demonstrated_skills) * 15.0 + (25.0 if has_metrics else 0.0), 100.0)
    
    # 4. Experience Fit Score
    exp_diff = parsed_resume.total_experience_years - job_req.min_experience_years
    if job_req.min_experience_years == 0.0 or exp_diff >= 0:
        exp_score = 100.0
    elif exp_diff >= -1.0:
        exp_score = 75.0
    else:
        exp_score = max(50.0 + exp_diff * 15.0, 20.0)
        
    # 5. Education Fit Score
    edu_score = 90.0 if parsed_resume.education else 60.0
    
    # Overall Weighted Resume Match Score
    # Weights: Required (50%) + Preferred (20%) + Projects (15%) + Experience (10%) + Education (5%)
    overall_score = round(
        (0.50 * req_pct) + (0.20 * pref_pct) + (0.15 * proj_evidence_score) + (0.10 * exp_score) + (0.05 * edu_score),
        1,
    )
    overall_score = min(max(overall_score, 0.0), 100.0)
    
    # Build detailed SkillMatchDetail list for all job requirements
    all_details = []
    
    # Check Required Skills
    for s_name in req_skills:
        cat = next((e.category for e in TAXONOMY if e.canonical_name == s_name), "Technical Skills")
        freq = market_counts.get(s_name, 0)
        
        tier = "INSUFFICIENT DATA"
        if freq > 500:
            tier = "HIGH OBSERVED DEMAND"
        elif freq > 100:
            tier = "MODERATE OBSERVED DEMAND"
        elif freq > 0:
            tier = "LOW OBSERVED DEMAND"
            
        jds_note = "Directly associated with junior salary-hike progression in SAS JDS cohort." if s_name in ("Python", "SQL", "Machine Learning", "Scikit-Learn", "Statistics & Probability", "Data Storytelling & Dashboards", "Tableau", "Power BI") else ""
        
        if s_name in resume_skills_map:
            s_obj = resume_skills_map[s_name]
            status = "PRESENT_DEMONSTRATED" if s_obj.is_demonstrated else "PRESENT_MENTIONED"
            ev_source = s_obj.source_section
        else:
            status = "MISSING_REQUIRED"
            ev_source = "Not detected in candidate resume"
            
        all_details.append(
            SkillMatchDetail(
                skill_name=s_name,
                category=cat,
                status=status,
                importance_tier="REQUIRED",
                evidence_source=ev_source,
                market_frequency=freq,
                market_demand_tier=tier,
                jds_association_note=jds_note,
            )
        )
        
    # Check Preferred Skills
    for s_name in pref_skills:
        cat = next((e.category for e in TAXONOMY if e.canonical_name == s_name), "Technical Skills")
        freq = market_counts.get(s_name, 0)
        tier = "HIGH OBSERVED DEMAND" if freq > 500 else ("MODERATE OBSERVED DEMAND" if freq > 100 else "LOW OBSERVED DEMAND")
        
        if s_name in resume_skills_map:
            s_obj = resume_skills_map[s_name]
            status = "PRESENT_DEMONSTRATED" if s_obj.is_demonstrated else "PRESENT_MENTIONED"
            ev_source = s_obj.source_section
        else:
            status = "MISSING_PREFERRED"
            ev_source = "Not detected in candidate resume"
            
        all_details.append(
            SkillMatchDetail(
                skill_name=s_name,
                category=cat,
                status=status,
                importance_tier="PREFERRED",
                evidence_source=ev_source,
                market_frequency=freq,
                market_demand_tier=tier,
            )
        )
        
    present_cnt = sum(1 for d in all_details if d.status in ("PRESENT_DEMONSTRATED", "PRESENT_MENTIONED"))
    missing_req_cnt = sum(1 for d in all_details if d.status == "MISSING_REQUIRED")
    missing_pref_cnt = sum(1 for d in all_details if d.status == "MISSING_PREFERRED")
    weak_cnt = sum(1 for d in all_details if d.status == "PRESENT_MENTIONED")
    
    formula_breakdown = {
        "Required Skill Coverage (50%)": round(req_pct, 1),
        "Preferred Skill Coverage (20%)": round(pref_pct, 1),
        "Project & Practical Evidence (15%)": round(proj_evidence_score, 1),
        "Experience Fit (10%)": round(exp_score, 1),
        "Education Fit (5%)": round(edu_score, 1),
        "Overall Composite Score": overall_score,
    }
    
    return ResumeMatchResult(
        target_role=job_req.role_title,
        overall_match_score=overall_score,
        required_skill_match_pct=round(req_pct, 1),
        preferred_skill_match_pct=round(pref_pct, 1),
        experience_fit_score=round(exp_score, 1),
        education_fit_score=round(edu_score, 1),
        project_evidence_score=round(proj_evidence_score, 1),
        present_skills_count=present_cnt,
        missing_required_count=missing_req_cnt,
        missing_preferred_count=missing_pref_cnt,
        weak_evidence_count=weak_cnt,
        all_skill_details=all_details,
        scoring_formula_breakdown=formula_breakdown,
    )
