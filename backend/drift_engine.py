"""Scoring & Deterministic Priority Engine.
Calculates Stability Index, Drift Rate, Health Score, and Deterministic Priority Register.
Uses a transparent mathematical formula without fabricating scores.
"""
import os
import re
from typing import Dict, List, Sequence, Any
from rapidfuzz.fuzz import partial_ratio
from .models import PriorityItem

TOOL_ALIASES = {
    "Wazuh": ("Wazuh", "Wazuh SIEM", "endpoint detection", "host intrusion detection", "HIDS"),
    "Splunk": ("Splunk", "Splunk SIEM", "security information and event management", "log analysis"),
    "Suricata": ("Suricata", "IDS/IPS", "intrusion detection", "network intrusion detection", "network intrusion prevention", "packet inspection"),
    "ELK Stack": ("ELK", "Elasticsearch", "Logstash", "Kibana"),
    "MITRE ATT&CK": ("MITRE ATT&CK", "ATT&CK", "ATTACK", "MITRE", "attack framework", "adversary tactics", "adversary techniques", "tactics techniques procedures", "TTP"),
    "AWS IAM": ("AWS IAM", "IAM", "Identity and Access Management"),
    "Kubernetes": ("Kubernetes", "K8s"),
    "Docker": ("Docker", "container", "containers", "containerization"),
    "Terraform": ("Terraform", "infrastructure as code", "IaC"),
    "Trivy": ("Trivy", "container security", "vulnerability scanner"),
    "Falco": ("Falco", "runtime security", "ebpf"),
}

# Module-level model cache to avoid reloading on every call
_EMBEDDER = None
_EMBEDDER_TRIED = False


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9][a-z0-9+#.-]{1,}", value.lower()))


def _get_embedder():
    global _EMBEDDER, _EMBEDDER_TRIED
    if _EMBEDDER is not None:
        return _EMBEDDER
    if _EMBEDDER_TRIED:
        return None
    _EMBEDDER_TRIED = True
    try:
        from sentence_transformers import SentenceTransformer
        try:
            _EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            return _EMBEDDER
        except Exception:
            offline = os.getenv("HF_HUB_OFFLINE", "").strip().lower() in ("1", "true", "yes")
            if offline:
                return None
            _EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=False)
            return _EMBEDDER
    except Exception:
        return None


def stability_index(corpus_text: str, concepts: Sequence[str]) -> float:
    """Compute semantic or token-based alignment between curriculum content and concepts."""
    if not corpus_text.strip() or not concepts:
        return 0.0
    embedder = _get_embedder()
    if embedder is not None:
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            score = cosine_similarity(embedder.encode([corpus_text]), embedder.encode(["; ".join(concepts)]))[0][0]
            return round(max(0.0, min(1.0, float(score))) * 100, 2)
        except Exception:
            pass
    # Deterministic offline approximation: concept token coverage.
    concept_tokens = _tokens(" ".join(concepts))
    if not concept_tokens:
        return 0.0
    overlap = len(concept_tokens & _tokens(corpus_text))
    return round(100.0 * overlap / len(concept_tokens), 2)


def tool_coverage(corpus_text: str, tools: Sequence[str | dict], threshold: int = 72) -> tuple[List[str], List[str], Dict[str, float]]:
    haystack = corpus_text.lower()
    matched, missing, scores = [], [], {}
    for raw_tool in tools:
        tool = str(raw_tool.get("name", "")) if isinstance(raw_tool, dict) else str(raw_tool)
        aliases_from_profile = tuple(raw_tool.get("aliases", ())) if isinstance(raw_tool, dict) else ()
        aliases = (tool,) + aliases_from_profile + TOOL_ALIASES.get(tool, ())
        evidence = [alias for alias in aliases if alias.lower() in haystack]
        exact = bool(evidence and tool.lower() in haystack)
        score = 100.0 if exact else (82.0 if evidence else max([partial_ratio(tool.lower(), chunk) for chunk in re.findall(r"\S+", haystack)] or [0]))
        scores[tool] = round(score, 1)
        (matched if score >= threshold else missing).append(tool)
    return matched, missing, scores


def _evidence_details(corpus_text: str, tools: Sequence[str | dict], scores: Dict[str, float]) -> dict[str, dict[str, object]]:
    haystack = corpus_text.lower()
    details = {}
    for raw_tool in tools:
        tool = str(raw_tool.get("name", "")) if isinstance(raw_tool, dict) else str(raw_tool)
        profile_aliases = tuple(raw_tool.get("aliases", ())) if isinstance(raw_tool, dict) else ()
        aliases = (tool,) + profile_aliases + TOOL_ALIASES.get(tool, ())
        terms = [alias for alias in aliases if alias.lower() in haystack]
        score = scores[tool]
        details[tool] = {
            "coverage": score,
            "evidence": terms,
            "match_type": "exact" if tool.lower() in haystack else ("semantic_alias" if terms else "none"),
            "confidence": round(min(1.0, score / 100), 2),
        }
    return details


def compute_priority_register(
    tools: Sequence[str | dict],
    match_scores: Dict[str, float],
    market_demand: Dict[str, float],
    role_relevance_default: float = 100.0,
) -> list[PriorityItem]:
    """Calculate deterministic Curriculum Priority Score (CPS) for each evaluated skill/tool.
    
    Formula:
    CPS = (0.45 * Curriculum_Gap) + (0.40 * Market_Demand) + (0.15 * Role_Relevance)
    
    All inputs normalized to [0, 100].
    Role relevance is 100 for skills included in the selected role profile; the
    engine does not claim an independent role-relevance estimate.
    Priority Levels:
      - >= 75.0 : CRITICAL
      - 60.0 - 74.9 : HIGH
      - 40.0 - 59.9 : MEDIUM
      - < 40.0 : LOW
    """
    register: list[PriorityItem] = []
    
    for raw in tools:
        tool_name = str(raw.get("name", "")) if isinstance(raw, dict) else str(raw)
        demand = max(0.0, min(100.0, float(
            market_demand.get(tool_name, raw.get("demand", 0.0) if isinstance(raw, dict) else 0.0)
        )))
        coverage = max(0.0, min(100.0, float(match_scores.get(tool_name, 0.0))))
        curriculum_gap = max(0.0, 100.0 - coverage)
        role_relevance = max(0.0, min(100.0, float(role_relevance_default)))

        # Weighted calculation
        gap_contrib = 0.45 * curriculum_gap
        demand_contrib = 0.40 * demand
        rel_contrib = 0.15 * role_relevance

        cps = round(gap_contrib + demand_contrib + rel_contrib, 1)

        # Priority Level
        if cps >= 75.0:
            level = "CRITICAL"
        elif cps >= 60.0:
            level = "HIGH"
        elif cps >= 40.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        # Impact and effort estimation (deterministic)
        # Open source CLI tools represent LOW effort; extensive infra tools represent MEDIUM or HIGH
        is_low_effort = tool_name in ("Trivy", "Falco", "Suricata", "Wazuh", "MITRE ATT&CK", "Docker")
        effort: Any = "LOW" if is_low_effort else "MEDIUM"
        
        is_high_impact = cps >= 60.0
        if is_high_impact and is_low_effort:
            quadrant = "HIGH IMPACT / LOW EFFORT"
        elif is_high_impact and not is_low_effort:
            quadrant = "HIGH IMPACT / HIGH EFFORT"
        elif not is_high_impact and is_low_effort:
            quadrant = "LOW IMPACT / LOW EFFORT"
        else:
            quadrant = "LOW IMPACT / HIGH EFFORT"

        evidence_str = (
            f"Curriculum match score is {coverage:.1f}/100 against market demand score of {demand:.1f}/100. "
            f"Match gap score is {curriculum_gap:.1f}/100."
        )

        register.append(PriorityItem(
            item_name=tool_name,
            item_type="skill",
            priority_level=level,
            priority_score=cps,
            market_demand=round(demand, 1),
            curriculum_gap=round(curriculum_gap, 1),
            role_relevance=round(role_relevance, 1),
            trend_momentum=0.0,
            effort_estimate=effort,
            impact_effort_category=quadrant,
            formula_breakdown={
                "gap_weighted_45pct": round(gap_contrib, 1),
                "demand_weighted_40pct": round(demand_contrib, 1),
                "relevance_weighted_15pct": round(rel_contrib, 1),
            },
            evidence_summary=evidence_str,
        ))

    # Sort descending by priority score
    register.sort(key=lambda x: x.priority_score, reverse=True)
    return register


def analyze(
    corpus_text: str,
    concepts: Sequence[str],
    tools: Sequence[str | dict],
    stability_weight: float = 0.4,
    drift_weight: float = 0.6,
) -> dict[str, Any]:
    """Run full deterministic audit: stability, drift, health, evidence, and priority register."""
    stability = stability_index(corpus_text, concepts)
    matched, missing, match_scores = tool_coverage(corpus_text, tools)
    drift = round(100 * len(missing) / max(1, len(tools)), 2)
    health = round(stability_weight * stability + drift_weight * (100 - drift), 2)
    names = [str(tool.get("name", "")) if isinstance(tool, dict) else str(tool) for tool in tools]
    coverage = {name: match_scores[name] for name in names}
    
    demand_dict = {
        (str(t.get("name", "")) if isinstance(t, dict) else str(t)): float(t.get("demand", 0.0) if isinstance(t, dict) else 0.0)
        for t in tools
    }

    priorities = compute_priority_register(tools, match_scores, demand_dict)

    top_critical = [p.item_name for p in priorities if p.priority_level == "CRITICAL"]
    top_high = [p.item_name for p in priorities if p.priority_level == "HIGH"]

    if top_critical:
        summary_rec = f"Focus curriculum updates immediately on CRITICAL gaps: {', '.join(top_critical)}."
    elif top_high:
        summary_rec = f"Prioritize HIGH urgency updates: {', '.join(top_high)}."
    elif missing:
        summary_rec = f"Curriculum stability is adequate; address missing tool coverage: {', '.join(missing)}."
    else:
        summary_rec = "Curriculum demonstrates high market alignment. Maintain foundational rigor."

    return {
        "stability_index": stability,
        "drift_rate": drift,
        "health_score": health,
        "matched_tools": matched,
        "missing_tools": missing,
        "match_scores": match_scores,
        "skill_coverage": coverage,
        "skill_evidence": _evidence_details(corpus_text, tools, match_scores),
        "priority_register": [p.model_dump() for p in priorities],
        "deterministic_summary": summary_rec,
    }
