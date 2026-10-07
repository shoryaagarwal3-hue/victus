from types import SimpleNamespace

from app import _analysis_input_key, _recommendation_cache_key, _sync_analysis_inputs


def test_analysis_key_tracks_every_audit_input():
    inputs = ("pdf", "SOC Analyst", "Static curated baseline", "csv", 0.4, "institution", "market-catalog")
    key = _analysis_input_key(*inputs)

    for index, changed_value in (
        (0, "different pdf"),
        (1, "Cloud Security Engineer"),
        (2, "Job postings CSV"),
        (3, "different csv"),
        (4, 0.5),
        (5, "another institution"),
        (6, "changed market catalog"),
    ):
        changed = list(inputs)
        changed[index] = changed_value
        assert _analysis_input_key(*changed) != key


def test_changed_inputs_clear_stale_result_but_keep_contextual_cache():
    session_state = {
        "analysis_input_key": "old",
        "result": {"health_score": 42},
        "patches": {"elective_module": {"title": "Elective"}},
        "patch_key": "old-cache-key",
        "gemini_cache": {"valid-for-another-input": {"elective_module": {"title": "Elective"}}},
    }

    _sync_analysis_inputs(session_state, "new")

    assert "result" not in session_state
    assert "patches" not in session_state
    assert "patch_key" not in session_state
    assert "valid-for-another-input" in session_state["gemini_cache"]


def test_ai_cache_key_tracks_market_evidence():
    result = {
        "missing_tools": ["Kubernetes"],
        "corpus": SimpleNamespace(corpus_text="Network security syllabus", subjects=[]),
        "profile": {"foundation_concepts": ["OSI Model"]},
        "market_demand": {"Kubernetes": 12},
        "market_evidence": {"source_type": "uploaded_csv", "source": "jobs.csv"},
    }
    initial_key = _recommendation_cache_key("analysis", result)

    changed_market_data = {**result, "market_demand": {"Kubernetes": 13}}

    assert _recommendation_cache_key("analysis", changed_market_data) != initial_key
