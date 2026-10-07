from backend.drift_engine import analyze, tool_coverage
from backend.models import PatchBundle
from backend.parser import parse_text
from backend.market_extractor import extract_market_profile, normalize_market_profile


def test_drift_math():
    result = analyze("OSI Model and access control Wazuh", ["OSI Model", "Access Control Theory"],
                     ["Wazuh", "Splunk"], 0.4, 0.6)
    assert result["matched_tools"] == ["Wazuh"]
    assert result["missing_tools"] == ["Splunk"]
    assert result["drift_rate"] == 50.0
    assert 0 <= result["health_score"] <= 100


def test_empty_tools_is_safe():
    assert tool_coverage("", []) == ([], [], {})


def test_parser_returns_one_unified_corpus_for_scoring():
    corpus = parse_text(
        "UNIT I Network Security\nOSI model and cryptography\n"
        "LIST OF EXPERIMENTS\nInstall Wazuh and inspect alerts"
    )
    assert "OSI model" in corpus.corpus_text
    assert "Install Wazuh" in corpus.corpus_text
    assert "Network Security" in corpus.subjects[0].corpus_text
    assert "OSI model" in corpus.subjects[0].corpus_text
    assert corpus.fingerprint


def test_tool_alias_is_accepted_as_evidence():
    matched, missing, scores = tool_coverage("Deploy K8s and inspect workloads", ["Kubernetes"])
    assert matched == ["Kubernetes"]
    assert missing == []
    assert scores["Kubernetes"] == 82.0


def test_market_demand_is_normalized_and_preserved():
    profile = extract_market_profile(["K8s Kubernetes", "Kubernetes"], [], ["Kubernetes"], limit=10)
    assert profile.demand == {"Kubernetes": 100.0}
    assert profile.provenance.metric == "posting_prevalence_percent"
    assert profile.provenance.denominator == 2
    assert "Kubernetes" in profile.foundation_concepts + profile.toolchain


def test_csv_market_prevalence_uses_posting_denominator():
    profile = extract_market_profile(["Kubernetes " * 125, "no tool mentioned"], [], ["Kubernetes"], limit=10)

    normalized = normalize_market_profile(profile.model_dump(), demand_scale=False)

    assert normalized["toolchain"][0]["demand"] == 50


def test_market_csv_preserves_unmentioned_terms_and_their_categories():
    profile = extract_market_profile(["OSI model"], ["OSI Model"], ["Kubernetes"], limit=10)

    assert profile.foundation_concepts == ["OSI Model"]
    assert profile.toolchain == ["Kubernetes"]
    assert profile.demand == {"OSI Model": 100.0, "Kubernetes": 0.0}


def test_market_csv_keeps_concepts_and_tools_in_their_configured_groups():
    profile = extract_market_profile(
        ["Kubernetes " * 3 + " OSI Model"],
        ["OSI Model"],
        ["Kubernetes"],
    )

    assert profile.foundation_concepts == ["OSI Model"]
    assert profile.toolchain == ["Kubernetes"]


def test_unverified_market_profile_cannot_keep_claimed_confidence():
    profile = normalize_market_profile({
        "provenance": {
            "source_type": "INSUFFICIENT EVIDENCE",
            "confidence": 0.95,
        },
        "toolchain": [{
            "name": "Kubernetes",
            "demand": 86,
            "source_type": "INSUFFICIENT EVIDENCE",
            "confidence": 0.95,
        }],
    })

    assert profile["provenance"]["confidence"] == 0.0
    assert profile["toolchain"][0]["provenance"]["confidence"] == 0.0


def test_different_syllabus_evidence_changes_results():
    market_tools = ["Wazuh", "Splunk", "Suricata", "MITRE ATT&CK"]
    concepts = ["incident response", "security operations"]
    security = analyze(
        "Incident Response Lifecycle Security Operations Center SIEM Splunk Suricata MITRE ATT&CK",
        concepts,
        market_tools,
    )
    systems = analyze(
        "Compiler Design Operating Systems Computer Architecture Database Management Systems SQL",
        concepts,
        market_tools,
    )
    assert security["skill_coverage"] != systems["skill_coverage"]
    assert security["matched_tools"] != systems["matched_tools"]
    assert security["drift_rate"] != systems["drift_rate"]
    assert security["health_score"] != systems["health_score"]


def test_unified_corpus_scores_concepts_and_tools_from_same_text():
    corpus = "Network Security OSI Model Access Control Splunk SIEM"
    result = analyze(corpus, ["OSI Model", "Access Control"], ["Splunk"])

    assert result["stability_index"] > 0
    assert result["drift_rate"] == 0
    assert result["matched_tools"] == ["Splunk"]


def test_patch_schema_rejects_unknown_fields():
    payload = {
        "elective_module": {"title": "Security", "credits": 2},
        "faculty_enablement": {},
        "copo_mapping": [],
        "unexpected": True,
    }
    try:
        PatchBundle.model_validate(payload)
    except ValueError:
        return
    raise AssertionError("unknown Gemini fields must be rejected")
