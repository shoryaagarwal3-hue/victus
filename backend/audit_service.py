"""Audit Service & In-Memory Context Provider for Google ADK Tools.
Maintains verified audit evidence and provides read-only query capabilities for the ADK agent.
Includes a deterministic fallback recommender for offline and API-unavailable modes.
"""
import threading
from typing import Any
from .models import (
    CourseSubject,
    PriorityItem,
    RecommendationResponse,
    SubjectReviewRecommendation,
    NewSubjectRecommendation,
    ActionPlanItem,
    FacultyEnablement,
    COPOMapping,
)
from .drift_engine import TOOL_ALIASES

_LOCAL_CONTEXT = threading.local()


def set_active_audit(
    college: str,
    role: str,
    result: dict[str, Any],
    subjects: list[CourseSubject] | None = None,
    cert_catalog: dict[str, Any] | None = None,
    po_definitions: dict[str, Any] | None = None,
) -> None:
    """Register current verified audit evidence into thread-local context for ADK tools."""
    _LOCAL_CONTEXT.audit = {
        "college": college,
        "role": role,
        "result": result,
        "subjects": subjects or (result.get("corpus").subjects if result.get("corpus") else []),
        "cert_catalog": cert_catalog or {},
        "po_definitions": po_definitions or {},
    }


def get_active_audit() -> dict[str, Any]:
    """Retrieve active audit evidence."""
    return getattr(_LOCAL_CONTEXT, "audit", {})


def clear_active_audit() -> None:
    """Discard session evidence after the ADK invocation finishes."""
    if hasattr(_LOCAL_CONTEXT, "audit"):
        del _LOCAL_CONTEXT.audit


def get_active_evidence() -> dict[str, Any]:
    """Read-only tool: Summarizes quantified drift and stability metrics."""
    audit = get_active_audit()
    if not audit:
        return {"status": "INSUFFICIENT EVIDENCE", "message": "No active audit session found."}
    res = audit.get("result", {})
    return {
        "college": audit.get("college", "Unknown Institution"),
        "target_role": audit.get("role", "Unknown Role"),
        "stability_index": res.get("stability_index", 0.0),
        "drift_rate": res.get("drift_rate", 0.0),
        "health_score": res.get("health_score", 0.0),
        "matched_tools": res.get("matched_tools", []),
        "missing_tools": res.get("missing_tools", []),
        "subjects_count": len(audit.get("subjects", [])),
    }


def get_active_subjects(course_code: str = "") -> list[dict[str, Any]]:
    """Read-only tool: Inspect verified CourseSubject records extracted from syllabus."""
    audit = get_active_audit()
    subjects = audit.get("subjects", [])
    if not subjects:
        return []
    records = []
    for s in subjects:
        if isinstance(s, CourseSubject):
            data = s.model_dump()
        elif isinstance(s, dict):
            data = s
        else:
            continue
        if not course_code or data.get("course_code", "").lower() == course_code.lower():
            records.append({
                "course_code": data.get("course_code"),
                "course_name": data.get("course_name"),
                "credits": data.get("credits"),
                "semester": data.get("semester"),
                "corpus_text": data.get("corpus_text", ""),
                "units": [
                    {
                        "unit_no": unit.get("unit_no"),
                        "title": unit.get("title"),
                        "topics": unit.get("topics", []),
                    }
                    for unit in data.get("units", [])
                ],
                "topics": data.get("topics", [])[:10],
                "learning_outcomes": data.get("learning_outcomes", []),
                "source_pages": data.get("source_pages", []),
                "confidence_level": data.get("confidence_level"),
                "extraction_confidence": data.get("extraction_confidence"),
            })
    return records


def get_active_market() -> dict[str, Any]:
    """Read-only tool: Retrieve market demand indicators and provenance."""
    audit = get_active_audit()
    res = audit.get("result", {})
    profile = res.get("profile", {})
    return {
        "role": audit.get("role"),
        "foundation_concepts": profile.get("foundation_concepts", []),
        "provenance": profile.get("provenance", {}),
        "toolchain": [
            {
                "name": t.get("name") if isinstance(t, dict) else str(t),
                "demand": t.get("demand") if isinstance(t, dict) else res.get("market_demand", {}).get(str(t), 0),
                "provenance": t.get("provenance", {}) if isinstance(t, dict) else {},
            }
            for t in profile.get("toolchain", [])
        ],
        "skill_coverage": res.get("skill_coverage", {}),
    }


def get_active_priorities() -> list[dict[str, Any]]:
    """Read-only tool: Return deterministic priority metrics computed by the priority engine."""
    audit = get_active_audit()
    res = audit.get("result", {})
    return res.get("priority_register", [])


def get_active_certs(tool_name: str = "") -> dict[str, Any]:
    """Read-only tool: Grounded certification options from data/cert_catalog.json."""
    audit = get_active_audit()
    catalog = audit.get("cert_catalog", {})
    if tool_name:
        return {tool_name: catalog.get(tool_name, [])}
    missing = audit.get("result", {}).get("missing_tools", [])
    return {tool: catalog.get(tool, []) for tool in missing}


def build_deterministic_recommendations(
    college: str,
    role: str,
    result: dict[str, Any],
    subjects: list[CourseSubject] | None = None,
    cert_catalog: dict[str, Any] | None = None,
    po_definitions: dict[str, Any] | None = None,
) -> RecommendationResponse:
    """Generate evidence-grounded recommendations without external API dependency.
    Guarantees deterministic results when API is unconfigured or rate-limited.
    """
    subjects = subjects or (result.get("corpus").subjects if result.get("corpus") else [])
    missing_tools = result.get("missing_tools", [])
    priorities = result.get("priority_register", [])
    # 1. Prioritization summary
    top_critical = [p["item_name"] for p in priorities if p.get("priority_level") == "CRITICAL"]
    top_high = [p["item_name"] for p in priorities if p.get("priority_level") == "HIGH"]

    if top_critical:
        lead = f"The deterministic priority register flags these CRITICAL toolchain gaps: {', '.join(top_critical)}."
    elif top_high:
        lead = f"The deterministic priority register flags these HIGH-priority toolchain gaps: {', '.join(top_high)}."
    elif missing_tools:
        lead = f"Review the detected curriculum coverage gaps for {', '.join(missing_tools)}."
    else:
        lead = "No missing toolchain skills were detected in the selected market profile."

    summary = (
        f"DETERMINISTIC CURRICULUM PRIORITIZATION for {college} ({role}):\n"
        f"{lead} "
        f"Composite Health Score is {result.get('health_score', 0):.1f}% with Drift Rate of {result.get('drift_rate', 0):.1f}%. "
        "Treat the deterministic priority register as a screening aid; available evidence does not establish course capacity "
        "or prove that a new elective is necessary."
    )

    # 2. Subject reviews
    subject_reviews: list[SubjectReviewRecommendation] = []
    if not subjects:
        subject_reviews.append(SubjectReviewRecommendation(
            course_code="N/A",
            course_name="General Curriculum Corpus",
            action="INSUFFICIENT_EVIDENCE",
            reason="No individual course subjects could be distinctly delineated from the PDF.",
            target_role=role,
            missing_skills=missing_tools[:3],
            foundational_importance="Medium",
            confidence=0.0,
        ))
    else:
        for s in subjects:
            code = s.course_code
            name = s.course_name
            conf = s.extraction_confidence
            relevant_gaps: list[str] = []

            if conf < 0.35:
                action = "INSUFFICIENT_EVIDENCE"
                reason = f"Extraction confidence is low ({conf:.2f}). Supporting syllabus evidence is incomplete."
            else:
                profile_aliases = {
                    str(tool.get("name", "")).casefold(): tool.get("aliases", [])
                    for tool in result.get("profile", {}).get("toolchain", [])
                    if isinstance(tool, dict)
                }
                subject_evidence = " ".join([
                    name,
                    code,
                    *s.topics,
                    *[unit.title for unit in s.units],
                    *[topic for unit in s.units for topic in unit.topics],
                    *s.learning_outcomes,
                ]).casefold()
                relevant_gaps = [
                    tool for tool in missing_tools
                    if any(
                        term.casefold() in subject_evidence
                        for term in (
                            tool,
                            *profile_aliases.get(tool.casefold(), []),
                            *TOOL_ALIASES.get(tool, ()),
                        )
                        if term
                    )
                ]
                if relevant_gaps:
                    action = "UPDATE"
                    reason = f"Subject content relates to {', '.join(relevant_gaps)}; review its coverage of those skills."
                else:
                    action = "KEEP"
                    reason = "No direct evidence links this subject to the current missing toolchain skills."

            # Find matching missing skills
            subj_missing = relevant_gaps if conf >= 0.35 else []

            subject_reviews.append(SubjectReviewRecommendation(
                course_code=code,
                course_name=name,
                action=action,
                reason=reason,
                target_role=role,
                missing_skills=subj_missing,
                foundational_importance="High" if any(w in name.lower() for w in ["network", "security", "operating", "crypto", "database"]) else "Medium",
                confidence=conf,
            ))

    # Offline evidence cannot establish whether a new course is necessary.
    new_subjects: list[NewSubjectRecommendation] = []

    # 5. Action Plan (NOW, NEXT, LATER)
    action_plan: list[ActionPlanItem] = []
    for p in priorities[:6]:
        item_name = p.get("item_name")
        quadrant = p.get("impact_effort_category", "HIGH IMPACT / LOW EFFORT")
        if quadrant == "HIGH IMPACT / LOW EFFORT":
            horizon = "NOW"
        elif quadrant == "HIGH IMPACT / HIGH EFFORT":
            horizon = "NEXT"
        else:
            horizon = "LATER"
        expected_impact = {
            "NOW": "Potential near-term improvement in practical coverage; verify after implementation.",
            "NEXT": "Potential improvement through a planned syllabus revision; evaluate before adoption.",
            "LATER": "Maintain as a lower-impact item for later review.",
        }[horizon]

        action_plan.append(ActionPlanItem(
            horizon=horizon,
            affected_subject_or_skill=item_name,
            action_type="Curriculum Update" if horizon == "NOW" else "Curriculum Revision",
            reason=f"Priority score {p.get('priority_score', 0):.1f} ({p.get('priority_level')}). {p.get('evidence_summary')}",
            evidence=(
                f"Market metric {p.get('market_demand')}; "
                f"curriculum match gap score {p.get('curriculum_gap')}/100."
            ),
            expected_impact=expected_impact,
            effort=p.get("effort_estimate", "MEDIUM"),
            impact_effort_quadrant=quadrant,
            confidence=0.88,
        ))

    # 6. Faculty Enablement
    faculty_plan = FacultyEnablement(
        steps=[
            "Review the updated subject outcomes and map them to the selected role's skill coverage.",
            "Prepare faculty development materials for adopted subjects and the tools they cover.",
            "Coordinate course updates with existing teaching plans and assessment outcomes.",
        ],
        implementation_notes="Plan faculty preparation and course-material updates before adopting recommendations.",
        reference_docs=[],
    )

    copo_items: list[COPOMapping] = []

    return RecommendationResponse(
        prioritization_summary=summary,
        subject_reviews=subject_reviews,
        new_subjects=new_subjects,
        action_plan=action_plan,
        faculty_enablement=faculty_plan,
        copo_mapping=copo_items,
        evidence_provenance="DETERMINISTIC FALLBACK",
    )
