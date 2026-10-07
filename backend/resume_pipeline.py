"""Master Resume Analysis Pipeline Orchestrator.
Connects:
Resume Upload -> Parser -> Skill Extractor -> Job Matcher -> Gap Engine -> Roadmap Engine -> Exporter.
Zero LLM / Gemini API calls. Fully deterministic.
"""
from datetime import datetime
from pathlib import Path
from typing import Any

from .resume_models import (
    CompleteResumeAnalysisBundle,
    JobDescriptionRequirement,
    ParsedResume,
)
from .resume_parser import parse_resume_document
from .resume_skill_extractor import extract_all_resume_skills
from .job_matcher import STANDARD_ROLES, match_resume_to_job, parse_job_description_text
from .resume_gap_engine import prioritize_skill_gaps
from .resume_roadmap_engine import (
    generate_learning_roadmaps_for_gaps,
    generate_resume_improvement_recommendations,
)
from .sas_pipeline import run_full_sas_pipeline
from .sas_models import SASFullPipelineResult

# Cache for SAS pipeline results
_CACHED_SAS_RESULT: SASFullPipelineResult | None = None


def get_cached_sas_pipeline_result() -> SASFullPipelineResult:
    """Retrieve or compute cached SAS analytics pipeline result."""
    global _CACHED_SAS_RESULT
    if _CACHED_SAS_RESULT is None:
        _CACHED_SAS_RESULT = run_full_sas_pipeline()
    return _CACHED_SAS_RESULT


def analyze_candidate_resume(
    file_bytes: bytes,
    file_name: str,
    target_role_title: str = "Junior Data Scientist",
    custom_jd_text: str | None = None,
) -> CompleteResumeAnalysisBundle:
    """Execute complete deterministic resume analysis pipeline."""
    # 1. Parse resume document (PDF / DOCX / TEXT)
    parsed_resume = parse_resume_document(file_bytes, file_name)
    
    # 2. Extract and normalize skills
    extract_all_resume_skills(parsed_resume)
    
    # 3. Retrieve or parse Job Requirement
    if custom_jd_text and len(custom_jd_text.strip()) > 30:
        job_req = parse_job_description_text(custom_jd_text, role_title=target_role_title)
    else:
        job_req = STANDARD_ROLES.get(target_role_title, list(STANDARD_ROLES.values())[0])
        
    # 4. Load SAS analytics evidence
    sas_res = get_cached_sas_pipeline_result()
    market_counts = sas_res.market_summary.top_key_skills
    
    # 5. Deterministic Resume-to-Job Matching
    match_result = match_resume_to_job(parsed_resume, job_req, market_counts)
    
    # 6. Skill Gap Prioritization with JDS and Market Evidence
    priority_gaps = prioritize_skill_gaps(match_result, sas_res.statistical_results, sas_res.jds_models)
    
    # 7. Actionable Step-by-Step Learning Roadmaps
    roadmaps = generate_learning_roadmaps_for_gaps(priority_gaps)
    
    # 8. Resume Bullet and Structure Improvement Recommendations
    tips = generate_resume_improvement_recommendations(parsed_resume)
    
    # 9. Executive summary
    exec_summary = (
        f"Candidate {parsed_resume.contact.name} achieved an overall Resume Match Score of "
        f"{match_result.overall_match_score:.1f}% against target role '{job_req.role_title}'. "
        f"Identified {len(priority_gaps)} prioritized skill gaps ({sum(1 for g in priority_gaps if g.priority_level == 'HIGH')} HIGH priority), "
        f"supported by empirical evidence from {sas_res.market_summary.total_postings_analyzed:,} market postings."
    )
    
    return CompleteResumeAnalysisBundle(
        parsed_resume=parsed_resume,
        job_requirement=job_req,
        match_result=match_result,
        priority_gaps=priority_gaps,
        learning_roadmaps=roadmaps,
        resume_improvement_tips=tips,
        executive_summary=exec_summary,
        timestamp=datetime.now().isoformat(),
    )
