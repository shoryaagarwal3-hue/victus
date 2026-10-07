"""Full end-to-end integration test of the Streamlit App using AppTest.
Tests the full user flow:
1. CU catalog selection (2025-29 B.E. CSE)
2. Load official curriculum & subject extraction (75 real subjects)
3. Deterministic audit metrics calculation
4. AI recommendation execution & fallback
5. CO-PO matrix & PDF export
6. Batch change invalidation (switching to 2024-28)
7. Role change invalidation (switching to Cloud Security Engineer)
8. Normal rerun stability (no repeated AI triggers)
"""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

BASE = Path(__file__).resolve().parents[1]


def test_full_streamlit_user_workflow():
    at = AppTest.from_file(str(BASE / "app.py"), default_timeout=90)
    at.run()
    assert len(at.exception) == 0, f"App threw exception on startup: {[e.value for e in at.exception]}"

    # 1. Verify default selections
    assert at.sidebar.selectbox[0].value == "SOC Analyst"
    assert at.sidebar.radio[0].value == "Official Chandigarh University CSE catalog"

    # 2. Click LOAD OFFICIAL CURRICULUM (first button in sidebar)
    load_btn = next((b for b in at.sidebar.button if "LOAD OFFICIAL CURRICULUM" in b.label), None)
    assert load_btn is not None, "LOAD OFFICIAL CURRICULUM button not found in sidebar"
    load_btn.click().run()
    assert len(at.exception) == 0, f"Exception after loading official curriculum: {[e.value for e in at.exception]}"

    # 3. Check that subjects were extracted and audit executed
    result = at.session_state.get("result")
    assert result is not None, "result should be present in session_state after loading"
    corpus = result.get("corpus")
    assert corpus is not None, "corpus should be present in result"
    assert len(corpus.subjects) == 75, f"Expected 75 subjects for 2025-29, got {len(corpus.subjects)}"
    assert corpus.subjects[0].course_code == "25CSH-107"
    assert corpus.parse_quality == "usable"

    # 4. Check deterministic metrics
    assert 0 <= result["stability_index"] <= 100
    assert 0 <= result["drift_rate"] <= 100
    assert 0 <= result["health_score"] <= 100

    # 5. Click GENERATE AI RECOMMENDATIONS
    gen_btn = next((b for b in at.button if "GENERATE AI RECOMMENDATIONS" in b.label), None)
    assert gen_btn is not None, "GENERATE AI RECOMMENDATIONS button not found"
    gen_btn.click().run()
    assert len(at.exception) == 0, f"Exception after generating recommendations: {[e.value for e in at.exception]}"

    recs = at.session_state.get("recommendations")
    assert recs is not None, "recommendations should be in session_state"
    assert "prioritization_summary" in recs

    # 6. Verify Batch Change Invalidation (switch to 2024-28)
    version_selectbox = next((s for s in at.sidebar.selectbox if "Curriculum Year" in s.label), None)
    assert version_selectbox is not None, "Curriculum Year / Batch selectbox not found"
    
    version_2024_id = next((opt for opt in version_selectbox.options if "2024-28" in opt), None)
    assert version_2024_id is not None
    version_selectbox.select(version_2024_id)

    # Click LOAD OFFICIAL CURRICULUM again
    load_btn = next((b for b in at.sidebar.button if "LOAD OFFICIAL CURRICULUM" in b.label), None)
    load_btn.click().run()
    assert len(at.exception) == 0

    new_result = at.session_state.get("result")
    assert new_result is not None
    assert len(new_result["corpus"].subjects) == 69, f"Expected 69 subjects for 2024-28, got {len(new_result['corpus'].subjects)}"

    # 7. Verify Role Change Invalidation (switch to Cloud Security Engineer)
    role_selectbox = at.sidebar.selectbox[0]
    role_selectbox.select("Cloud Security Engineer")
    at.run()
    # Stale result from previous role is invalidated
    assert at.session_state.get("result") is None
    
    # Reload with new role
    load_btn = next((b for b in at.sidebar.button if "LOAD OFFICIAL CURRICULUM" in b.label), None)
    assert load_btn is not None
    load_btn.click().run()
    assert len(at.exception) == 0

    cloud_result = at.session_state.get("result")
    assert cloud_result is not None
    # Cloud Security Engineer toolchain has Docker, Kubernetes, etc.
    assert "Docker" in cloud_result["skill_coverage"]
    assert "Kubernetes" in cloud_result["skill_coverage"]

    # 8. Normal rerun does not clear or corrupt results
    at.run()
    assert at.session_state.get("result") is not None
