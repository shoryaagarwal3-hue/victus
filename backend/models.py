"""Pydantic models for Curriculum Drift & Market-Alignment Engine.
Defines schemas for PDF parsing, subject extraction, market provenance,
priority ranking, and AI recommendations.
"""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class CourseUnit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    unit_no: int | str = 1
    title: str = ""
    topics: list[str] = Field(default_factory=list)


class CourseSubject(BaseModel):
    model_config = ConfigDict(extra="ignore")
    course_code: str = "N/A"
    course_name: str = "Unnamed Subject"
    credits: float | None = None
    semester: str = "N/A"
    course_type: str = "Unspecified"
    units: list[CourseUnit] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    corpus_text: str = ""
    learning_outcomes: list[str] = Field(default_factory=list)
    source_pages: list[int] = Field(default_factory=list)
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_level: str = "INSUFFICIENT EVIDENCE"
    low_confidence_reasons: list[str] = Field(default_factory=list)


class Corpus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    corpus_text: str = ""
    subjects: list[CourseSubject] = Field(default_factory=list)
    page_count: int = 0
    source_name: str = ""
    diagnostics: list[str] = Field(default_factory=list)
    fingerprint: str = ""
    extracted_characters: int = 0
    non_empty_lines: int = 0
    sections_detected: int = 0
    parse_quality: str = "unknown"


class MarketProvenance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    metric: str = "demand_score"
    source: str = "Unverified curated baseline"
    source_type: Literal["VERIFIED", "SIMULATED", "DERIVED", "INSUFFICIENT EVIDENCE"] = "INSUFFICIENT EVIDENCE"
    date: str = "undocumented"
    denominator: int | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class MarketTool(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    demand: float = 0.0
    aliases: list[str] = Field(default_factory=list)
    provenance: MarketProvenance = Field(default_factory=MarketProvenance)


class MarketProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    foundation_concepts: list[str] = Field(default_factory=list)
    toolchain: list[str | dict[str, Any]] = Field(default_factory=list)
    demand: dict[str, int | float] = Field(default_factory=dict)
    provenance: MarketProvenance = Field(default_factory=MarketProvenance)


class PriorityItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    item_name: str
    item_type: Literal["skill", "subject"] = "skill"
    priority_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    priority_score: float = Field(default=0.0, ge=0.0, le=100.0)
    market_demand: float = Field(default=0.0, ge=0.0, le=100.0)
    curriculum_gap: float = Field(default=0.0, ge=0.0, le=100.0)
    role_relevance: float = Field(default=0.0, ge=0.0, le=100.0)
    trend_momentum: float = Field(default=0.0, ge=0.0, le=100.0)
    effort_estimate: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    impact_effort_category: Literal[
        "HIGH IMPACT / LOW EFFORT",
        "HIGH IMPACT / HIGH EFFORT",
        "LOW IMPACT / LOW EFFORT",
        "LOW IMPACT / HIGH EFFORT",
    ] = "HIGH IMPACT / HIGH EFFORT"
    formula_breakdown: dict[str, float] = Field(default_factory=dict)
    evidence_summary: str = ""


class SubjectReviewRecommendation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    course_code: str
    course_name: str
    action: Literal["KEEP", "UPDATE", "MERGE", "RECONSIDER", "INSUFFICIENT_EVIDENCE"]
    reason: str
    target_role: str
    missing_skills: list[str] = Field(default_factory=list)
    foundational_importance: str = "High"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class NewSubjectRecommendation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    reason: str
    target_role: str
    missing_skills: list[str] = Field(default_factory=list)
    market_evidence: str
    affected_gap: str
    prerequisites: list[str] = Field(default_factory=list)
    credits: int = 3
    units_topics: list[dict[str, Any]] = Field(default_factory=list)
    learning_outcomes: list[str] = Field(default_factory=list)
    effort: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "HIGH"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class ActionPlanItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    horizon: Literal["NOW", "NEXT", "LATER"]
    affected_subject_or_skill: str
    action_type: str
    reason: str
    evidence: str
    expected_impact: str
    effort: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    impact_effort_quadrant: Literal[
        "HIGH IMPACT / LOW EFFORT",
        "HIGH IMPACT / HIGH EFFORT",
        "LOW IMPACT / LOW EFFORT",
        "LOW IMPACT / HIGH EFFORT",
    ] = "HIGH IMPACT / LOW EFFORT"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class ElectiveModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    credits: int = 2
    units: list[dict[str, object]] = Field(default_factory=list)
    course_outcomes: list[str] = Field(default_factory=list)


class FacultyEnablement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    steps: list[str] = Field(default_factory=list)
    implementation_notes: str = ""
    reference_docs: list[str] = Field(default_factory=list)


class COPOMapping(BaseModel):
    model_config = ConfigDict(extra="ignore")
    course_outcome: str
    mapped_pos: list[dict[str, object]] = Field(default_factory=list)


class PatchBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    elective_module: ElectiveModule = Field(default_factory=lambda: ElectiveModule(title="Elective"))
    faculty_enablement: FacultyEnablement = Field(default_factory=FacultyEnablement)
    copo_mapping: list[COPOMapping] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    prioritization_summary: str = ""
    subject_reviews: list[SubjectReviewRecommendation] = Field(default_factory=list)
    new_subjects: list[NewSubjectRecommendation] = Field(default_factory=list)
    action_plan: list[ActionPlanItem] = Field(default_factory=list)
    faculty_enablement: FacultyEnablement = Field(default_factory=FacultyEnablement)
    copo_mapping: list[COPOMapping] = Field(default_factory=list)
    evidence_provenance: Literal["AI-ASSISTED", "DETERMINISTIC FALLBACK"] = "AI-ASSISTED"
