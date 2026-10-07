"""Read-only Google ADK Tools for Curriculum Audit Agent.
Provides access to verified syllabus subjects, market demand, and deterministic priority metrics.
These tools are strictly read-only and cannot mutate persistent state.
"""
from typing import Any
from backend.audit_service import (
    get_active_evidence,
    get_active_subjects,
    get_active_market,
    get_active_priorities,
    get_active_certs,
)


def get_audit_evidence() -> dict[str, Any]:
    """Retrieve verified high-level audit evidence: Stability Index, Drift Rate, Health Score, and missing tools.
    
    Returns:
        dict: High-level quantitative metrics and gap overview.
    """
    return get_active_evidence()


def get_subject_details(course_code: str = "") -> list[dict[str, Any]]:
    """Inspect structured CourseSubject records extracted from the syllabus PDF.
    
    Args:
        course_code: Optional course code filter (e.g. 'CS401'). If empty, returns all subjects.
        
    Returns:
        list[dict]: Extracted course units, hours, learning outcomes, and extraction confidence.
    """
    return get_active_subjects(course_code)


def get_market_evidence() -> dict[str, Any]:
    """Retrieve verified market demand metrics, foundation concepts, and toolchains for the target role.
    
    Returns:
        dict: Market demand indices and provenance metadata.
    """
    return get_active_market()


def get_priority_metrics() -> list[dict[str, Any]]:
    """Retrieve deterministic priority scores (CPS) and impact/effort classifications for all evaluated skills.
    
    Returns:
        list[dict]: Ranked priority register with mathematical breakdown.
    """
    return get_active_priorities()


def get_certification_options(tool_name: str = "") -> dict[str, Any]:
    """Retrieve accredited certification mappings from the verified catalog (data/cert_catalog.json).
    
    Args:
        tool_name: Optional tool name filter (e.g. 'Splunk', 'Kubernetes').
        
    Returns:
        dict: Tool to certification details mapping.
    """
    return get_active_certs(tool_name)
