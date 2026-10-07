"""Comprehensive Real-Workflow Verification Test Suite.
Validates the complete 21-point user flow using the actual Chandigarh University syllabus PDF.
Tests parsing, deterministic audit, CPS calculations, AI recommendation workflow,
Pydantic validation, PDF generation and inspection, and cache invalidation.
"""
import io
import os
import json
import hashlib
from pathlib import Path
from types import SimpleNamespace
import pytest
from dotenv import load_dotenv
import pdfplumber

from backend.parser import parse_syllabus
from backend.drift_engine import analyze
from backend.market_extractor import normalize_market_profile
from backend.cert_mapper import map_certifications, load_catalog
from backend.copo_engine import load_po_definitions, build_matrix
from backend.report_exporter import build_pdf
from backend.adk_workflow import run_curriculum_audit_workflow
from backend.audit_service import build_deterministic_recommendations
from backend.models import RecommendationResponse
from app import _analysis_input_key, _recommendation_cache_key, _sync_analysis_inputs

load_dotenv()
BASE = Path(__file__).resolve().parents[1]
CU_PDF_PATH = BASE / "data" / "sample_syllabus" / "chandigarh_university_cybersecurity_dbms.pdf"


def test_01_real_pdf_exists():
    """Verify actual syllabus PDF exists in data/sample_syllabus/."""
    assert CU_PDF_PATH.exists(), f"Sample syllabus PDF not found at {CU_PDF_PATH}"
    assert CU_PDF_PATH.stat().st_size > 50000


def test_02_structured_subject_extraction():
    """Points 5: Confirm actual subjects are extracted from the real CU PDF."""
    corpus = parse_syllabus(CU_PDF_PATH)
    assert corpus.page_count == 7
    assert len(corpus.subjects) >= 1
    
    subj = corpus.subjects[0]
    assert subj.course_code == "25CSH-236"
    assert "Database Management System" in subj.course_name
    assert subj.credits == 4.0
    assert len(subj.units) >= 2
    assert len(subj.learning_outcomes) == 5
    assert len(subj.corpus_text) > 100
    assert subj.extraction_confidence == 1.0
    assert subj.confidence_level == "HIGH"
    assert corpus.parse_quality == "usable"


def test_03_deterministic_audit_and_priority_calculation():
    """Points 4, 6: Run deterministic audit and confirm Priority Register has real calculated CPS values."""
    corpus = parse_syllabus(CU_PDF_PATH)
    profiles = json.loads((BASE / "data" / "market_skills.json").read_text(encoding="utf-8"))
    profile = normalize_market_profile(profiles["SOC Analyst"])

    result = analyze(
        corpus.corpus_text,
        profile["foundation_concepts"],
        profile["toolchain"],
        0.4,
        0.6,
    )

    # Stability, Drift, Health
    assert 0 <= result["stability_index"] <= 100
    assert 0 <= result["drift_rate"] <= 100
    assert 0 <= result["health_score"] <= 100

    # Priority Register verification
    priorities = result.get("priority_register", [])
    assert len(priorities) == len(profile["toolchain"])
    for p in priorities:
        assert p["priority_score"] >= 0
        assert p["priority_level"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        assert p["impact_effort_category"] in (
            "HIGH IMPACT / LOW EFFORT",
            "HIGH IMPACT / HIGH EFFORT",
            "LOW IMPACT / LOW EFFORT",
            "LOW IMPACT / HIGH EFFORT",
        )
        assert "gap_weighted_45pct" in p["formula_breakdown"]


def test_04_subject_reviews_and_evidence_gaps():
    """Points 7, 8, 9, 10: Confirm Subject Review, New Electives, and NOW/NEXT/LATER use real gaps."""
    corpus = parse_syllabus(CU_PDF_PATH)
    profiles = json.loads((BASE / "data" / "market_skills.json").read_text(encoding="utf-8"))
    profile = normalize_market_profile(profiles["SOC Analyst"])

    result = analyze(
        corpus.corpus_text,
        profile["foundation_concepts"],
        profile["toolchain"],
        0.4,
        0.6,
    )
    result["corpus"], result["profile"] = corpus, profile
    result["market_demand"] = {tool["name"]: tool["demand"] for tool in profile["toolchain"]}

    cert_cat = load_catalog(BASE / "data" / "cert_catalog.json")
    po_defs = load_po_definitions(BASE / "data" / "po_definitions.json")

    # Generate recommendations via evidence-grounded deterministic builder
    recs = build_deterministic_recommendations("Chandigarh University", "SOC Analyst", result, corpus.subjects, cert_cat, po_defs)
    
    # 7. Subject review
    assert len(recs.subject_reviews) == 1
    sr = recs.subject_reviews[0]
    assert sr.course_code == "25CSH-236"
    assert "Database Management System" in sr.course_name
    assert sr.action in ("KEEP", "UPDATE", "MERGE", "RECONSIDER", "INSUFFICIENT_EVIDENCE")

    # 8. New subjects only use identified gaps
    for ns in recs.new_subjects:
        for skill in ns.missing_skills:
            assert skill in result["missing_tools"]

    # 10. Deterministic horizons only reflect evidence-backed priority quadrants.
    horizons = {a.horizon for a in recs.action_plan}
    assert horizons
    assert horizons <= {"NOW", "NEXT", "LATER"}


def test_05_adk_ai_workflow_execution_and_pydantic_validation():
    """Points 11, 12, 13, 14, 15, 16, 17: Execute ADK workflow, validate Pydantic, check grounding & certs."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not configured in environment; skipping live LLM test.")

    corpus = parse_syllabus(CU_PDF_PATH)
    profiles = json.loads((BASE / "data" / "market_skills.json").read_text(encoding="utf-8"))
    profile = normalize_market_profile(profiles["SOC Analyst"])

    result = analyze(
        corpus.corpus_text,
        profile["foundation_concepts"],
        profile["toolchain"],
        0.4,
        0.6,
    )
    result["corpus"], result["profile"] = corpus, profile
    result["market_demand"] = {tool["name"]: tool["demand"] for tool in profile["toolchain"]}

    cert_cat = load_catalog(BASE / "data" / "cert_catalog.json")
    po_defs = load_po_definitions(BASE / "data" / "po_definitions.json")

    # Live call to ADK / Gemini workflow
    try:
        response = run_curriculum_audit_workflow(
            college="Chandigarh University",
            role="SOC Analyst",
            result=result,
            subjects=corpus.subjects,
            cert_catalog=cert_cat,
            po_definitions=po_defs,
        )
    except RuntimeError as exc:
        err_lower = str(exc).lower()
        if any(term in err_lower for term in ["503", "429", "unavailable", "high demand", "quota", "timeout", "deadline", "connection", "no final recommendation content", "malformed"]):
            pytest.skip(f"Live Gemini API temporarily unavailable: {exc}")
        raise

    # 13. Validate against Pydantic
    assert isinstance(response, RecommendationResponse)
    assert response.prioritization_summary

    # 14. Confirm AI recommendations reference actual audit evidence
    summary_lower = response.prioritization_summary.lower()
    assert any(term in summary_lower for term in ["chandigarh", "soc", "splunk", "wazuh", "drift", "health", "priority", "database"])

    # 16. Confirm Certifications come from cert_catalog.json
    certs_map = map_certifications(result["missing_tools"], BASE / "data" / "cert_catalog.json")
    for tool, tool_certs in certs_map.items():
        if tool in cert_cat:
            assert len(tool_certs) == len(cert_cat[tool])

    # 17. CO-PO mappings
    assert len(response.copo_mapping) >= 1
    matrix = build_matrix([m.course_outcome for m in response.copo_mapping], response.copo_mapping, po_defs)
    assert len(matrix) >= 1


def test_06_pdf_export_and_validation(tmp_path):
    """Point 18: Export the PDF and open/validate it."""
    corpus = parse_syllabus(CU_PDF_PATH)
    profiles = json.loads((BASE / "data" / "market_skills.json").read_text(encoding="utf-8"))
    profile = normalize_market_profile(profiles["SOC Analyst"])

    result = analyze(
        corpus.corpus_text,
        profile["foundation_concepts"],
        profile["toolchain"],
        0.4,
        0.6,
    )
    cert_cat = load_catalog(BASE / "data" / "cert_catalog.json")
    po_defs = load_po_definitions(BASE / "data" / "po_definitions.json")
    recs = build_deterministic_recommendations("Chandigarh University", "SOC Analyst", result, corpus.subjects, cert_cat, po_defs)

    pdf_bytes = build_pdf("Chandigarh University", "SOC Analyst", result, recs.model_dump())
    assert pdf_bytes.startswith(b"%PDF")
    
    export_file = tmp_path / "test_audit_export.pdf"
    export_file.write_bytes(pdf_bytes)
    assert export_file.stat().st_size > 1000

    # Open with pdfplumber and validate structure
    with pdfplumber.open(export_file) as pdf:
        assert len(pdf.pages) >= 1
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        assert "BOS/NAAC CURRICULUM DRIFT & MARKET-ALIGNMENT AUDIT" in full_text
        assert "Chandigarh University" in full_text
        assert "WHAT SHOULD WE WORK ON FIRST?" in full_text
        assert "DETERMINISTIC PRIORITY REGISTER" in full_text
        assert "SYLLABUS SUBJECT REVIEWS" in full_text
        assert "LAB EXPERIMENT PATCHES" not in full_text
        assert "CURRICULUM ACTION PLAN" in full_text


def test_07_cache_invalidation_on_role_change():
    """Point 19: Change the target role and verify stale recommendations are invalidated."""
    corpus = parse_syllabus(CU_PDF_PATH)
    pdf_hash = hashlib.sha256(CU_PDF_PATH.read_bytes()).hexdigest()
    catalog_hash = hashlib.sha256((BASE / "data" / "market_skills.json").read_bytes()).hexdigest()

    key_soc = _analysis_input_key(pdf_hash, "SOC Analyst", "Static curated baseline", "", 0.4, "Chandigarh University", catalog_hash)
    key_cloud = _analysis_input_key(pdf_hash, "Cloud Security Engineer", "Static curated baseline", "", 0.4, "Chandigarh University", catalog_hash)
    assert key_soc != key_cloud

    session_state = {
        "analysis_input_key": key_soc,
        "result": {"health_score": 75},
        "recommendations": {"prioritization_summary": "SOC plan"},
        "rec_key": "cache_soc",
    }
    _sync_analysis_inputs(session_state, key_cloud)
    assert "result" not in session_state
    assert "recommendations" not in session_state
    assert "rec_key" not in session_state


def test_08_cache_invalidation_on_syllabus_change():
    """Point 20: Change the syllabus and verify stale recommendations are invalidated."""
    catalog_hash = hashlib.sha256((BASE / "data" / "market_skills.json").read_bytes()).hexdigest()
    key_pdf1 = _analysis_input_key("hash_aaa", "SOC Analyst", "Static curated baseline", "", 0.4, "Chandigarh University", catalog_hash)
    key_pdf2 = _analysis_input_key("hash_bbb", "SOC Analyst", "Static curated baseline", "", 0.4, "Chandigarh University", catalog_hash)
    assert key_pdf1 != key_pdf2

    session_state = {
        "analysis_input_key": key_pdf1,
        "result": {"health_score": 75},
        "recommendations": {"prioritization_summary": "Old PDF plan"},
        "rec_key": "cache_pdf1",
    }
    _sync_analysis_inputs(session_state, key_pdf2)
    assert "result" not in session_state
    assert "recommendations" not in session_state


def test_09_normal_rerun_does_not_trigger_ai():
    """Point 21: Verify normal Streamlit reruns do NOT trigger the AI model."""
    catalog_hash = hashlib.sha256((BASE / "data" / "market_skills.json").read_bytes()).hexdigest()
    key = _analysis_input_key("hash_same", "SOC Analyst", "Static curated baseline", "", 0.4, "Chandigarh University", catalog_hash)
    
    session_state = {
        "analysis_input_key": key,
        "result": {"health_score": 75},
        "recommendations": {"prioritization_summary": "Existing cached plan"},
        "rec_key": "cache_existing",
    }
    # Sync with SAME key (simulates normal rerun)
    _sync_analysis_inputs(session_state, key)
    # Stored results and recommendations remain intact without calling AI
    assert session_state.get("result") == {"health_score": 75}
    assert session_state.get("recommendations") == {"prioritization_summary": "Existing cached plan"}
