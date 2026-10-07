"""Unit tests for Google ADK Agent, tools, and AI recommendation workflow.
Uses mocks to avoid consuming external API quota.
Verifies error resilience (429, timeouts, malformed JSON), cache invalidation, and fallback.
"""
import json
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from unittest.mock import patch, MagicMock, AsyncMock

from backend.models import RecommendationResponse, CourseSubject, PriorityItem
from backend.ai_config import (
    DEFAULT_GEMINI_MODEL,
    gemini_model_name,
    local_endpoint_url,
    local_model_name,
)
from backend.audit_service import (
    set_active_audit,
    get_active_evidence,
    get_active_audit,
    get_active_subjects,
    get_active_priorities,
    get_active_certs,
    build_deterministic_recommendations,
)
from backend.adk_workflow import (
    run_curriculum_audit_workflow,
    convert_recommendations_to_patch_bundle,
)
from agents.curriculum_audit.tools import (
    get_audit_evidence as tool_evidence,
    get_subject_details as tool_subjects,
    get_priority_metrics as tool_priorities,
)
from agents.curriculum_audit.agent import curriculum_recommender


@pytest.fixture
def sample_audit_context():
    subjects = [
        CourseSubject(
            course_code="CS501",
            course_name="Network Security",
            credits=4.0,
            semester="Semester 5",
            units=[],
            topics=["firewalls", "cryptography"],
            corpus_text="Network security fundamentals including firewalls and cryptography",
            learning_outcomes=["Understand network defenses"],
            extraction_confidence=0.85,
            confidence_level="HIGH",
        )
    ]
    result = {
        "stability_index": 82.5,
        "drift_rate": 40.0,
        "health_score": 67.0,
        "matched_tools": ["Wazuh"],
        "missing_tools": ["Splunk", "Suricata"],
        "market_demand": {"Wazuh": 78.0, "Splunk": 84.0, "Suricata": 72.0},
        "priority_register": [
            {
                "item_name": "Splunk",
                "priority_level": "CRITICAL",
                "priority_score": 86.5,
                "market_demand": 84.0,
                "curriculum_gap": 100.0,
                "effort_estimate": "MEDIUM",
                "impact_effort_category": "HIGH IMPACT / HIGH EFFORT",
                "evidence_summary": "Missing applied tools.",
            }
        ],
        "profile": {
            "foundation_concepts": ["OSI Model", "Access Control"],
            "toolchain": [{"name": "Wazuh"}, {"name": "Splunk"}, {"name": "Suricata"}],
        },
        "skill_coverage": {"Wazuh": 100.0, "Splunk": 0.0, "Suricata": 0.0},
    }
    cert_catalog = {
        "Splunk": [{"cert_name": "Splunk Core Certified User", "issuer": "Splunk Inc.", "level": "Entry"}]
    }
    po_definitions = {"PO1": "Engineering knowledge", "PO5": "Modern tool usage"}
    return "Test Institute", "SOC Analyst", result, subjects, cert_catalog, po_definitions


def test_adk_agent_definition():
    assert curriculum_recommender.name == "curriculum_recommender"
    assert len(curriculum_recommender.tools) >= 5


def test_ai_model_and_local_endpoint_configuration(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "configured-model")
    monkeypatch.setenv("OPENAI_MODEL", "local-model")
    monkeypatch.setenv("LOCAL_LLM_ENDPOINT", "http://127.0.0.1:8081/v1")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:8082/v1")

    assert gemini_model_name() == "configured-model"
    assert local_model_name() == "local-model"
    assert local_endpoint_url() == "http://127.0.0.1:8081/v1"


def test_ai_model_default_is_centralized_and_configurable(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert gemini_model_name() == DEFAULT_GEMINI_MODEL
    assert gemini_model_name() != "gemini-2.5-flash"


def test_local_endpoint_payload_includes_configured_model(monkeypatch):
    from backend.adk_workflow import _call_local_endpoint

    monkeypatch.setenv("OPENAI_MODEL", "gemini-web2api-model")
    response = MagicMock()
    response.__enter__.return_value.read.return_value = (
        b'{"choices":[{"message":{"content":"{}"}}]}'
    )
    with patch("backend.adk_workflow.urllib.request.urlopen", return_value=response) as urlopen:
        assert _call_local_endpoint("prompt", "http://127.0.0.1:8081/v1") == "{}"

    request = urlopen.call_args.args[0]
    assert json.loads(request.data)["model"] == "gemini-web2api-model"


def test_adk_tools_read_only_access(sample_audit_context):
    college, role, result, subjects, cert_cat, po_defs = sample_audit_context
    set_active_audit(college, role, result, subjects, cert_cat, po_defs)

    evidence = tool_evidence()
    assert evidence["college"] == "Test Institute"
    assert evidence["stability_index"] == 82.5
    assert evidence["missing_tools"] == ["Splunk", "Suricata"]

    subjs = tool_subjects()
    assert len(subjs) == 1
    assert subjs[0]["course_code"] == "CS501"
    assert subjs[0]["credits"] == 4.0
    assert subjs[0]["source_pages"] == []
    assert "corpus_text" in subjs[0]

    priorities = tool_priorities()
    assert len(priorities) == 1
    assert priorities[0]["item_name"] == "Splunk"

    certs = get_active_certs("Splunk")
    assert "Splunk" in certs
    assert certs["Splunk"][0]["cert_name"] == "Splunk Core Certified User"


def test_adk_workflow_with_mocked_gemini(sample_audit_context, monkeypatch):
    college, role, result, subjects, cert_cat, po_defs = sample_audit_context
    monkeypatch.setenv("GEMINI_API_KEY", "mock-test-key")

    mock_json = {
        "prioritization_summary": "Focus curriculum updates immediately on Splunk SIEM integration.",
        "subject_reviews": [
            {
                "course_code": "CS501",
                "course_name": "Network Security",
                "action": "UPDATE",
                "reason": "Missing hands-on SIEM and log analysis skills.",
                "target_role": "SOC Analyst",
                "missing_skills": ["Splunk"],
                "foundational_importance": "High",
                "confidence": 0.90,
            }
        ],
        "new_subjects": [
            {
                "title": "Applied Security Operations & SIEM",
                "reason": "Bridges core toolchain gap in enterprise telemetry.",
                "target_role": "SOC Analyst",
                "missing_skills": ["Splunk", "Suricata"],
                "market_evidence": "84% demand index in SOC postings.",
                "affected_gap": "Enterprise log monitoring",
                "prerequisites": ["CS501"],
                "credits": 3,
                "units_topics": [{"unit_no": 1, "title": "SIEM Ingestion", "topics": ["Logstash", "Forwarders"]}],
                "learning_outcomes": ["Deploy forwarders and parse alerts"],
                "effort": "MEDIUM",
                "priority": "HIGH",
                "confidence": 0.88,
            }
        ],
        "action_plan": [
            {
                "horizon": "NOW",
                "affected_subject_or_skill": "Splunk",
                "action_type": "Integrate into course labs",
                "reason": "Immediate high-impact quick win.",
                "evidence": "Critical gap",
                "expected_impact": "Industry readiness",
                "effort": "LOW",
                "impact_effort_quadrant": "HIGH IMPACT / LOW EFFORT",
                "confidence": 0.90,
            }
        ],
        "faculty_enablement": {
            "steps": ["Provide instructor Docker images"],
            "implementation_notes": "Pre-configured Docker Compose setup recommended",
            "reference_docs": ["Splunk Docs"],
        },
        "copo_mapping": [
            {
                "course_outcome": "Deploy forwarders and parse alerts",
                "mapped_pos": [{"po": "PO5", "strength": 3, "justification": "Modern tool usage"}],
            }
        ],
    }

    with patch("backend.adk_workflow._run_adk_agent", return_value=json.dumps(mock_json)):
        response = run_curriculum_audit_workflow(
            college, role, result, subjects, cert_cat, po_defs
        )

    assert isinstance(response, RecommendationResponse)
    assert "Splunk" in response.prioritization_summary
    assert len(response.subject_reviews) == 1
    assert response.subject_reviews[0].action == "UPDATE"
    assert len(response.new_subjects) == 1
    assert "84%" not in response.new_subjects[0].market_evidence
    assert "Deterministic priority register" in response.new_subjects[0].market_evidence
    assert response.faculty_enablement.reference_docs == []
    assert response.action_plan[0].horizon == "NOW"
    assert get_active_audit() == {}


def test_adk_rejects_recommendations_for_unknown_syllabus_subject(sample_audit_context, monkeypatch):
    college, role, result, subjects, cert_cat, po_defs = sample_audit_context
    monkeypatch.setenv("GEMINI_API_KEY", "mock-test-key")
    payload = {
        "subject_reviews": [{
            "course_code": "CS999",
            "course_name": "Invented Course",
            "action": "UPDATE",
            "reason": "Unverified",
            "target_role": role,
        }]
    }

    with patch("backend.adk_workflow._run_adk_agent", return_value=json.dumps(payload)):
        with pytest.raises(RuntimeError, match="malformed recommendation response"):
            run_curriculum_audit_workflow(college, role, result, subjects, cert_cat, po_defs)


def test_adk_rejects_recommendations_for_a_different_role(sample_audit_context, monkeypatch):
    college, role, result, subjects, cert_cat, po_defs = sample_audit_context
    monkeypatch.setenv("GEMINI_API_KEY", "mock-test-key")
    payload = {
        "subject_reviews": [{
            "course_code": "CS501",
            "course_name": "Network Security",
            "action": "KEEP",
            "reason": "Role mismatch",
            "target_role": "Penetration Tester",
        }]
    }

    with patch("backend.adk_workflow._run_adk_agent", return_value=json.dumps(payload)):
        with pytest.raises(RuntimeError, match="malformed recommendation response"):
            run_curriculum_audit_workflow(college, role, result, subjects, cert_cat, po_defs)


def test_recommendation_models_reject_out_of_range_confidence_and_scores():
    with pytest.raises(ValidationError):
        RecommendationResponse.model_validate({
            "subject_reviews": [{
                "course_code": "CS501",
                "course_name": "Network Security",
                "action": "KEEP",
                "reason": "Evidence-based",
                "target_role": "SOC Analyst",
                "confidence": 1.01,
            }]
        })

    with pytest.raises(ValidationError):
        PriorityItem(item_name="Splunk", priority_score=100.1)


def test_missing_api_key_raises_runtime_error(sample_audit_context, monkeypatch):
    college, role, result, subjects, cert_cat, po_defs = sample_audit_context
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("LOCAL_LLM_ENDPOINT", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        run_curriculum_audit_workflow(college, role, result, subjects, cert_cat, po_defs)
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)
    assert get_active_audit() == {}


def test_quota_429_error_handling(sample_audit_context, monkeypatch):
    college, role, result, subjects, cert_cat, po_defs = sample_audit_context
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")

    mock_agent = MagicMock(side_effect=Exception("Resource has been exhausted (e.g. check quota). HTTP 429"))

    with patch("backend.adk_workflow._run_adk_agent", mock_agent):
        with pytest.raises(RuntimeError) as exc_info:
            run_curriculum_audit_workflow(college, role, result, subjects, cert_cat, po_defs)
        assert "429" in str(exc_info.value) or "quota" in str(exc_info.value).lower()


def test_malformed_json_triggers_retry_and_handles_error(sample_audit_context, monkeypatch):
    college, role, result, subjects, cert_cat, po_defs = sample_audit_context
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")

    mock_agent = MagicMock(return_value="INVALID JSON CONTENT {{{")

    with patch("backend.adk_workflow._run_adk_agent", mock_agent):
        with pytest.raises(RuntimeError) as exc_info:
            run_curriculum_audit_workflow(college, role, result, subjects, cert_cat, po_defs)
        assert "malformed" in str(exc_info.value).lower()
        assert mock_agent.call_count == 2


@pytest.mark.parametrize("status_code", [429, 503])
def test_transient_gemini_error_retries_with_fallback_model(monkeypatch, status_code):
    from google.genai.errors import APIError

    import backend.adk_workflow as workflow

    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-primary")
    monkeypatch.setenv("GEMINI_FALLBACK_MODEL", "gemini-fallback")
    monkeypatch.setattr(workflow, "local_endpoint_url", lambda: None)
    monkeypatch.setattr(workflow.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        workflow,
        "_validate_recommendation_evidence",
        lambda response, *_: response,
    )
    calls = []

    def mock_agent(prompt, model_name=None):
        calls.append(model_name)
        if len(calls) == 1:
            raise APIError(status_code, {"error": {"message": "temporarily unavailable"}})
        return '{"prioritization_summary": "Recovered on fallback model"}'

    monkeypatch.setattr(workflow, "_run_adk_agent", mock_agent)

    response = workflow._run_curriculum_audit_workflow(
        "Example University",
        "SOC Analyst",
        {},
        subjects=[],
    )

    assert response.prioritization_summary == "Recovered on fallback model"
    assert calls == ["gemini-primary", "gemini-fallback"]


def test_adk_runner_invokes_primary_agent_and_collects_final_text():
    event = SimpleNamespace(
        is_final_response=lambda: True,
        content=SimpleNamespace(parts=[SimpleNamespace(text='{"result": "ok"}')]),
    )

    async def event_stream(**_):
        yield event

    session_service = MagicMock()
    session_service.create_session = AsyncMock(return_value=SimpleNamespace(id="session-1"))
    runner = MagicMock()
    runner.run_async = MagicMock(return_value=event_stream())
    runner.close = AsyncMock()

    with (
        patch("google.adk.runners.Runner", return_value=runner) as runner_factory,
        patch("google.adk.sessions.InMemorySessionService", return_value=session_service),
        patch("backend.adk_workflow.create_curriculum_agent") as agent_factory,
        patch("google.genai.types.Content") as content_factory,
        patch("google.genai.types.Part") as part_factory,
    ):
        from backend.adk_workflow import _run_adk_agent

        output = _run_adk_agent("verified evidence prompt")

    assert output == '{"result": "ok"}'
    assert runner_factory.call_args.kwargs["agent"] is agent_factory.return_value
    assert runner.run_async.call_args.kwargs["session_id"] == "session-1"
    assert content_factory.call_args.kwargs["role"] == "user"
    assert part_factory.call_args.kwargs["text"] == "verified evidence prompt"


def test_deterministic_fallback_recommender(sample_audit_context):
    college, role, result, subjects, cert_cat, po_defs = sample_audit_context
    rec = build_deterministic_recommendations(college, role, result, subjects, cert_cat, po_defs)
    assert isinstance(rec, RecommendationResponse)
    assert rec.prioritization_summary
    assert rec.evidence_provenance == "DETERMINISTIC FALLBACK"
    assert len(rec.subject_reviews) == 1
    assert len(rec.new_subjects) == 0
    assert rec.copo_mapping == []
    assert any(a.horizon == "NEXT" for a in rec.action_plan)


def test_deterministic_fallback_does_not_assign_unrelated_gaps(sample_audit_context):
    college, role, result, _, cert_cat, po_defs = sample_audit_context
    subjects = [
        CourseSubject(
            course_code="CS401",
            course_name="Operating Systems",
            topics=["process scheduling", "memory management"],
            extraction_confidence=0.9,
            confidence_level="HIGH",
        ),
        CourseSubject(
            course_code="CS501",
            course_name="Network Security",
            topics=["log analysis", "cryptography"],
            extraction_confidence=0.9,
            confidence_level="HIGH",
        ),
    ]
    result["missing_tools"] = ["Splunk"]
    result["profile"]["toolchain"] = [
        {"name": "Splunk", "aliases": ["log analysis"]}
    ]

    rec = build_deterministic_recommendations(
        college, role, result, subjects, cert_cat, po_defs
    )

    reviews = {review.course_code: review for review in rec.subject_reviews}
    assert reviews["CS401"].action == "KEEP"
    assert reviews["CS401"].missing_skills == []
    assert reviews["CS501"].action == "UPDATE"
    assert reviews["CS501"].missing_skills == ["Splunk"]
