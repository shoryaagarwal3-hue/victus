"""AppTest integration test for SAS Career Intelligence & Resume Analysis Streamlit App.
"""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

BASE = Path(__file__).resolve().parents[1]


def test_sas_streamlit_app_startup():
    """Verify that Streamlit app starts cleanly with 0 exceptions and renders default panel."""
    at = AppTest.from_file(str(BASE / "app.py"), default_timeout=30)
    at.run()
    assert len(at.exception) == 0, f"App threw exception on startup: {[e.value for e in at.exception]}"
    
    # Verify title text is present
    assert any("SAS DATA SCIENCE CAREER INTELLIGENCE" in t.value for t in at.markdown)


@pytest.mark.parametrize("page_name", [
    "📄 Resume Scanner & Parser",
    "🎯 Job Match & Requirement Fit",
    "🔍 Skill Gap & Prioritization",
    "🗺️ Actionable Learning Roadmap",
    "💡 Resume Improvement Tips",
    "📊 SAS Market Intelligence",
    "📈 JDS Technical Skill Analytics",
    "🧠 SDS Personality Analytics",
    "🤖 ML Benchmarks & Validation",
    "📑 Audit Report & PDF Export",
    "⚙️ Settings & System Health",
])
def test_sas_streamlit_page_navigation(page_name):
    """Verify each page renders without throwing exceptions."""
    at = AppTest.from_file(str(BASE / "app.py"), default_timeout=30)
    at.run()
    assert len(at.exception) == 0
    at.sidebar.radio[0].set_value(page_name).run()
    assert len(at.exception) == 0, f"Page '{page_name}' threw exception: {[e.value for e in at.exception]}"

