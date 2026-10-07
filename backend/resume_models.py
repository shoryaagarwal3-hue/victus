"""Pydantic schemas and typed data contracts for Resume Intelligence, Skill Gap Analysis,
Career Matching, Learning Roadmaps, and Audit Reports.
"""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class ContactInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = "Candidate"
    email: str = "Not detected"
    phone: str = "Not detected"
    linkedin: str = "Not detected"
    github: str = "Not detected"
    portfolio: str = "Not detected"


class EducationEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    degree: str = "Degree"
    field_of_study: str = "Field of Study"
    institution: str = "Institution"
    graduation_year: str = "Not detected"
    gpa_or_grade: str = "Not detected"


class ExperienceEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    organization: str = "Organization"
    role: str = "Role"
    duration: str = "Duration"
    estimated_years: float = 0.0
    responsibilities: list[str] = Field(default_factory=list)
    technologies_used: list[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = "Project"
    description: str = ""
    technologies_used: list[str] = Field(default_factory=list)
    measurable_outcomes: list[str] = Field(default_factory=list)
    has_demonstrated_skills: bool = False


class ExtractedSkill(BaseModel):
    model_config = ConfigDict(extra="ignore")
    raw_text: str
    normalized_name: str
    category: str  # Programming Languages, Machine Learning, Data Visualization, etc.
    source_section: str  # Skills, Projects, Experience, Education, Certifications
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_demonstrated: bool = False  # True if found in Projects or Experience with context
    context_snippet: str = ""


class ParsedResume(BaseModel):
    model_config = ConfigDict(extra="ignore")
    file_name: str
    file_type: Literal["PDF", "DOCX", "TEXT"]
    raw_text: str
    character_count: int
    word_count: int
    contact: ContactInfo = Field(default_factory=ContactInfo)
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    extracted_skills: list[ExtractedSkill] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    total_experience_years: float = 0.0
    parse_status: Literal["SUCCESS", "PARTIAL", "EMPTY_OR_UNREADABLE", "FAILED"] = "SUCCESS"
    parse_notes: list[str] = Field(default_factory=list)


class JobDescriptionRequirement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role_title: str = "Custom Role"
    raw_text: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    supporting_skills: list[str] = Field(default_factory=list)
    min_experience_years: float = 0.0
    preferred_education: str = "Bachelor's or Master's in STEM / CS / Quantitative field"
    responsibilities_summary: list[str] = Field(default_factory=list)


class SkillMatchDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    skill_name: str
    category: str
    status: Literal["PRESENT_DEMONSTRATED", "PRESENT_MENTIONED", "MISSING_REQUIRED", "MISSING_PREFERRED", "MISSING_SUPPORTING"]
    importance_tier: Literal["REQUIRED", "PREFERRED", "SUPPORTING"] = "REQUIRED"
    evidence_source: str = "Not detected"
    market_frequency: int = 0
    market_demand_tier: Literal["HIGH OBSERVED DEMAND", "MODERATE OBSERVED DEMAND", "LOW OBSERVED DEMAND", "INSUFFICIENT DATA"] = "INSUFFICIENT DATA"
    jds_association_note: str = ""


class ResumeMatchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    target_role: str
    overall_match_score: float = Field(ge=0.0, le=100.0)
    required_skill_match_pct: float = Field(ge=0.0, le=100.0)
    preferred_skill_match_pct: float = Field(ge=0.0, le=100.0)
    experience_fit_score: float = Field(ge=0.0, le=100.0)
    education_fit_score: float = Field(ge=0.0, le=100.0)
    project_evidence_score: float = Field(ge=0.0, le=100.0)
    present_skills_count: int
    missing_required_count: int
    missing_preferred_count: int
    weak_evidence_count: int
    all_skill_details: list[SkillMatchDetail] = Field(default_factory=list)
    scoring_formula_breakdown: dict[str, float] = Field(default_factory=dict)


class PrioritySkillGap(BaseModel):
    model_config = ConfigDict(extra="ignore")
    skill_name: str
    category: str
    priority_level: Literal["HIGH", "MEDIUM", "LOW"]
    primary_reason: str
    job_requirement_evidence: str
    market_demand_evidence: str
    jds_career_outcome_evidence: str
    current_resume_status: str
    estimated_learning_effort: Literal["LOW (1-2 Weeks)", "MEDIUM (3-6 Weeks)", "HIGH (7-12 Weeks)"] = "MEDIUM (3-6 Weeks)"


class LearningRoadmapStep(BaseModel):
    model_config = ConfigDict(extra="ignore")
    skill_name: str
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    why_it_matters: str
    prerequisites: list[str] = Field(default_factory=list)
    foundation_topics: list[str] = Field(default_factory=list)
    intermediate_topics: list[str] = Field(default_factory=list)
    advanced_topics: list[str] = Field(default_factory=list)
    practice_tasks: list[str] = Field(default_factory=list)
    mini_project: str
    main_portfolio_project: str
    validation_milestone: str
    portfolio_evidence_criteria: list[str] = Field(default_factory=list)
    resume_bullet_template: str


class ResumeImprovementTip(BaseModel):
    model_config = ConfigDict(extra="ignore")
    section: str  # Header, Experience, Projects, Skills, Education
    finding_observation: str
    actionable_advice: str
    before_example: str
    after_example: str


class CompleteResumeAnalysisBundle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    parsed_resume: ParsedResume
    job_requirement: JobDescriptionRequirement
    match_result: ResumeMatchResult
    priority_gaps: list[PrioritySkillGap] = Field(default_factory=list)
    learning_roadmaps: list[LearningRoadmapStep] = Field(default_factory=list)
    resume_improvement_tips: list[ResumeImprovementTip] = Field(default_factory=list)
    executive_summary: str = ""
    timestamp: str = ""
