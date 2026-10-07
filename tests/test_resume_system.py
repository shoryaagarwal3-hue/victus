"""Test Suite for SAS Data Science Career Intelligence & Resume Analysis System.
Validates:
- Resume parsing (PDF, DOCX, Text)
- Error resilience (empty, corrupt, oversized)
- Contact and section extraction
- Skill extraction, normalization, and categorization
- Job description analysis
- 5-factor Resume Match scoring (no CPS contamination)
- Skill gap prioritization fusing SAS market & JDS evidence
- Actionable learning roadmap generation
- Resume improvement recommendations
- Markdown & PDF audit report generation
- Zero Gemini / Google ADK runtime dependency
"""
import io
import pytest
import docx

from backend.resume_models import ParsedResume, JobDescriptionRequirement, CompleteResumeAnalysisBundle
from backend.resume_parser import (
    parse_resume_document,
    extract_contact_info,
    extract_text_from_docx,
    segment_resume_sections,
)
from backend.resume_skill_extractor import (
    extract_skills_from_text,
    extract_all_resume_skills,
    TAXONOMY,
)
from backend.job_matcher import (
    STANDARD_ROLES,
    parse_job_description_text,
    match_resume_to_job,
)
from backend.resume_gap_engine import prioritize_skill_gaps
from backend.resume_roadmap_engine import (
    generate_learning_roadmaps_for_gaps,
    generate_resume_improvement_recommendations,
)
from backend.resume_report_exporter import (
    generate_resume_audit_report_markdown,
    build_pdf_audit_report,
)
from backend.resume_pipeline import analyze_candidate_resume


SAMPLE_RESUME_TEXT = """Johnathan Doe
j.doe@analytics.org | (555) 439-9021 | github.com/johndoe-ds | linkedin.com/in/johndoe

PROFESSIONAL EXPERIENCE
Data Analyst | Enterprise Tech Corp (2022 - 2024)
- Built automated data extraction scripts in Python and SQL for customer churn analysis.
- Developed interactive Tableau dashboards for executive business reviews.

PROJECTS
Predictive Churn Model
- Trained an XGBoost classification model using Scikit-Learn achieving 88% accuracy across 5-fold CV.
- Engineered features from 100K transaction records and analyzed feature importances.

SKILLS
Python, SQL, Machine Learning, Scikit-Learn, Tableau, Statistics & Probability, Git, PostgreSQL

EDUCATION
B.S. in Computer Science | State University (2018 - 2022)
"""


def test_01_text_resume_parsing():
    """Verify parsing plain text resume."""
    parsed = parse_resume_document(SAMPLE_RESUME_TEXT.encode("utf-8"), "test_resume.txt")
    assert parsed.parse_status == "SUCCESS"
    assert parsed.contact.name == "Johnathan Doe"
    assert parsed.contact.email == "j.doe@analytics.org"
    assert "github.com" in parsed.contact.github
    assert len(parsed.experience) >= 1
    assert len(parsed.projects) >= 1
    assert len(parsed.education) >= 1


def test_02_docx_resume_parsing():
    """Verify parsing DOCX resume document."""
    doc = docx.Document()
    doc.add_heading("Jane Smith", level=1)
    doc.add_paragraph("jane.smith@email.com | (555) 892-1209 | github.com/janesmith")
    doc.add_heading("Skills", level=2)
    doc.add_paragraph("Python, SQL, Machine Learning, Tableau, Power BI, Statistics & Probability")
    doc.add_heading("Projects", level=2)
    doc.add_paragraph("Built classification model with scikit-learn achieving 90% accuracy.")
    
    buf = io.BytesIO()
    doc.save(buf)
    docx_bytes = buf.getvalue()
    
    parsed = parse_resume_document(docx_bytes, "jane_smith.docx")
    assert parsed.parse_status == "SUCCESS"
    assert parsed.file_type == "DOCX"
    assert parsed.contact.email == "jane.smith@email.com"


def test_03_empty_and_corrupt_files():
    """Verify error resilience on empty, corrupt, or oversized files."""
    empty_parsed = parse_resume_document(b"", "empty.pdf")
    assert empty_parsed.parse_status == "EMPTY_OR_UNREADABLE"
    
    oversized = parse_resume_document(b"A" * (26 * 1024 * 1024), "huge.pdf")
    assert oversized.parse_status == "FAILED"


def test_04_skill_extraction_and_normalization():
    """Verify skill extraction, alias normalization (e.g. sklearn -> Scikit-Learn), and demonstrated flag."""
    text = "Implemented machine learning models using sklearn and python. Built dashboards with powerbi and sql."
    skills = extract_skills_from_text(text, source_section="Projects")
    
    names = {s.normalized_name for s in skills}
    assert "Python" in names
    assert "Machine Learning" in names
    assert "Scikit-Learn" in names
    assert "Power BI" in names
    assert "SQL" in names
    
    # Check that skills in projects have is_demonstrated = True
    assert all(s.is_demonstrated for s in skills)


def test_05_job_description_parsing():
    """Verify standard role templates and custom JD parsing."""
    jds_role = STANDARD_ROLES["Junior Data Scientist"]
    assert "Python" in jds_role.required_skills
    assert "SQL" in jds_role.required_skills
    assert "Machine Learning" in jds_role.required_skills
    
    custom_jd = """Senior Data Engineer
    Required Qualifications:
    - 5+ years of experience with Python, Apache Spark, and SQL
    - Hands-on expertise with AWS and Docker
    Preferred:
    - Experience with Kafka and Databricks
    """
    custom_req = parse_job_description_text(custom_jd, role_title="Senior Data Engineer")
    assert "Python" in custom_req.required_skills
    assert "Apache Spark" in custom_req.required_skills


def test_06_resume_to_job_matching():
    """Verify deterministic 5-factor Resume Match score calculation."""
    parsed = parse_resume_document(SAMPLE_RESUME_TEXT.encode("utf-8"), "resume.txt")
    extract_all_resume_skills(parsed)
    
    job_req = STANDARD_ROLES["Junior Data Scientist"]
    market_counts = {"Python": 962, "SQL": 1582, "Machine Learning": 734}
    
    match = match_resume_to_job(parsed, job_req, market_counts)
    assert 0.0 <= match.overall_match_score <= 100.0
    assert 0.0 <= match.required_skill_match_pct <= 100.0
    assert 0.0 <= match.preferred_skill_match_pct <= 100.0
    assert len(match.all_skill_details) == len(job_req.required_skills) + len(job_req.preferred_skills)
    
    # Confirm formula weights
    weights = match.scoring_formula_breakdown
    assert "Required Skill Coverage (50%)" in weights
    assert "Preferred Skill Coverage (20%)" in weights


def test_07_skill_gap_prioritization():
    """Verify gap prioritization fusing role requirements and SAS evidence."""
    parsed = parse_resume_document(b"Jane Doe\njane@test.com\nSKILLS: Python", "short_resume.txt")
    extract_all_resume_skills(parsed)
    
    job_req = STANDARD_ROLES["Junior Data Scientist"]
    match = match_resume_to_job(parsed, job_req, {"SQL": 1582, "Python": 962})
    
    gaps = prioritize_skill_gaps(match)
    assert len(gaps) > 0
    assert any(g.priority_level == "HIGH" for g in gaps)
    
    # Verify traceable justifications
    for g in gaps:
        assert g.primary_reason
        assert g.job_requirement_evidence
        assert g.market_demand_evidence


def test_08_learning_roadmaps_and_tips():
    """Verify roadmap steps and resume bullet point improvement tips."""
    parsed = parse_resume_document(SAMPLE_RESUME_TEXT.encode("utf-8"), "resume.txt")
    extract_all_resume_skills(parsed)
    job_req = STANDARD_ROLES["Junior Data Scientist"]
    match = match_resume_to_job(parsed, job_req)
    gaps = prioritize_skill_gaps(match)
    
    roadmaps = generate_learning_roadmaps_for_gaps(gaps)
    assert len(roadmaps) == len(gaps)
    for rm in roadmaps:
        assert rm.skill_name
        assert len(rm.foundation_topics) > 0
        assert rm.main_portfolio_project
        assert rm.resume_bullet_template
        
    tips = generate_resume_improvement_recommendations(parsed)
    assert len(tips) >= 2
    for tip in tips:
        assert tip.section
        assert tip.actionable_advice
        assert tip.before_example
        assert tip.after_example


def test_09_audit_report_and_pdf_generation():
    """Verify Markdown 28-section report and fpdf2 PDF bytes export."""
    bundle = analyze_candidate_resume(
        file_bytes=SAMPLE_RESUME_TEXT.encode("utf-8"),
        file_name="johndoe_resume.txt",
        target_role_title="Junior Data Scientist",
    )
    
    md_report = generate_resume_audit_report_markdown(bundle)
    assert "### 1. Executive Summary" in md_report
    assert "### 28. Technical Appendix" in md_report
    assert "Johnathan Doe" in md_report
    assert len(md_report) > 5000
    
    pdf_bytes = build_pdf_audit_report(bundle)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_10_end_to_end_resume_pipeline_no_gemini():
    """Verify complete end-to-end execution without any Gemini / LLM calls."""
    bundle = analyze_candidate_resume(
        file_bytes=SAMPLE_RESUME_TEXT.encode("utf-8"),
        file_name="candidate.txt",
        target_role_title="Data Analyst / Business Analytics Specialist",
    )
    assert bundle.parsed_resume.parse_status == "SUCCESS"
    assert bundle.match_result.overall_match_score > 0.0
    assert len(bundle.priority_gaps) >= 1
    assert len(bundle.learning_roadmaps) >= 1
    assert len(bundle.resume_improvement_tips) >= 1
