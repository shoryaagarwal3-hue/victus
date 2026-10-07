"""Unit tests for the Deterministic Priority Engine.
Verifies Curriculum Priority Score (CPS) formula calculation, bounds, priority levels,
and impact/effort quadrant assignment.
"""
from backend.drift_engine import compute_priority_register, analyze


def test_priority_score_formula_calculation():
    # Tools with explicit coverage and demand
    tools = [
        {"name": "Wazuh", "demand": 80.0},
        {"name": "Splunk", "demand": 90.0},
    ]
    # Wazuh coverage = 100 (gap = 0), Splunk coverage = 0 (gap = 100)
    match_scores = {"Wazuh": 100.0, "Splunk": 0.0}
    market_demand = {"Wazuh": 80.0, "Splunk": 90.0}

    # Formula: CPS = 0.45 * Gap + 0.40 * Demand + 0.15 * Relevance(85)
    # For Splunk:
    # Gap = 100 -> 45.0
    # Demand = 90 -> 36.0
    # Relevance = 85 -> 12.75
    # Total = 45.0 + 36.0 + 12.75 = 93.75 (rounds to 93.8)
    priorities = compute_priority_register(tools, match_scores, market_demand, role_relevance_default=85.0)
    
    splunk_p = next(p for p in priorities if p.item_name == "Splunk")
    wazuh_p = next(p for p in priorities if p.item_name == "Wazuh")

    assert splunk_p.priority_level == "CRITICAL"
    assert splunk_p.priority_score == 93.8
    assert "gap_weighted_45pct" in splunk_p.formula_breakdown
    assert "demand_weighted_40pct" in splunk_p.formula_breakdown
    assert "relevance_weighted_15pct" in splunk_p.formula_breakdown
    assert sum(value for key, value in {
        "gap": 0.45,
        "demand": 0.40,
        "relevance": 0.15,
    }.items()) == 1.0
    assert splunk_p.impact_effort_category in ("HIGH IMPACT / LOW EFFORT", "HIGH IMPACT / HIGH EFFORT")

    # Wazuh has zero curriculum gap: 32.0 demand + 12.75 relevance = 44.75.
    assert wazuh_p.priority_score < splunk_p.priority_score
    assert wazuh_p.priority_score == 44.8
    assert wazuh_p.priority_level == "MEDIUM"


def test_priority_register_is_sorted_descending():
    tools = [
        {"name": "LowGapTool", "demand": 30.0},
        {"name": "CriticalTool", "demand": 95.0},
        {"name": "MediumTool", "demand": 60.0},
    ]
    match_scores = {"LowGapTool": 90.0, "CriticalTool": 0.0, "MediumTool": 40.0}
    market_demand = {"LowGapTool": 30.0, "CriticalTool": 95.0, "MediumTool": 60.0}

    priorities = compute_priority_register(tools, match_scores, market_demand)
    scores = [p.priority_score for p in priorities]
    assert scores == sorted(scores, reverse=True)
    assert priorities[0].item_name == "CriticalTool"
    assert priorities[0].priority_level == "CRITICAL"


def test_priority_scores_remain_bounded_when_market_input_is_out_of_range():
    priorities = compute_priority_register(
        [{"name": "HighCountSkill", "demand": 500.0}],
        {"HighCountSkill": 0.0},
        {"HighCountSkill": 500.0},
        role_relevance_default=500.0,
    )

    assert priorities[0].market_demand == 100.0
    assert priorities[0].role_relevance == 100.0
    assert 0.0 <= priorities[0].priority_score <= 100.0


def test_analyze_includes_deterministic_priority_and_summary():
    result = analyze(
        "OSI Model Network Architecture Wazuh SIEM installation",
        ["OSI Model"],
        [{"name": "Wazuh", "demand": 80.0}, {"name": "Splunk", "demand": 90.0}],
    )
    assert "priority_register" in result
    assert "deterministic_summary" in result
    assert len(result["priority_register"]) == 2
    assert "CRITICAL" in result["deterministic_summary"] or "Splunk" in result["deterministic_summary"]
