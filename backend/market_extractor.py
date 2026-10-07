"""Market data normalization, provenance tracking, and CSV posting-prevalence extraction.
Ensures no fabricated percentages and maintains explicit source provenance.
"""
import re
from datetime import date
from collections import Counter
from typing import Iterable, Any, Sequence
from .models import MarketProfile, MarketProvenance


def get_tool_name(tool: object) -> str:
    return str(tool.get("name", "")) if isinstance(tool, dict) else str(tool)


def normalize_demand(value: object, proportion: bool = False, clip: bool = True) -> float:
    """Normalize demand score to a standard index.
    Does NOT assert the unit is percentage unless verified.
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if proportion and 0 <= number <= 1:
        number *= 100
    if clip:
        return round(max(0.0, min(100.0, number)), 2)
    return round(max(0.0, number), 2)


def normalize_market_profile(profile: dict[str, Any], demand_scale: bool = True) -> dict[str, Any]:
    """Return normalized profile dict with full provenance and structured tool specs."""
    concepts = [str(item) for item in profile.get("foundation_concepts", [])]
    tools: list[dict[str, Any]] = []
    demand_map = profile.get("demand", {})
    
    prov_raw = profile.get("provenance", {})
    profile_source_type = prov_raw.get("source_type", "INSUFFICIENT EVIDENCE")
    profile_confidence = (
        0.0
        if profile_source_type == "INSUFFICIENT EVIDENCE"
        else float(prov_raw.get("confidence", 0.0))
    )
    profile_prov = MarketProvenance(
        metric=prov_raw.get("metric", "relative_demand_index_0_to_100" if demand_scale else "raw_mentions"),
        source=prov_raw.get("source", "Unverified curated baseline"),
        source_type=profile_source_type,
        date=prov_raw.get("date", "undocumented"),
        denominator=prov_raw.get("denominator"),
        confidence=profile_confidence,
    )

    for raw in profile.get("toolchain", []):
        if isinstance(raw, dict):
            name = get_tool_name(raw)
            aliases = [str(alias) for alias in raw.get("aliases", [])]
            raw_d = raw.get("demand", 0)
            demand = normalize_demand(raw_d, clip=demand_scale)
            metric = raw.get("metric", profile_prov.metric)
            source = raw.get("source", profile_prov.source)
            source_type = raw.get("source_type", profile_prov.source_type)
            doc_date = raw.get("date", profile_prov.date)
            confidence = (
                0.0
                if source_type == "INSUFFICIENT EVIDENCE"
                else float(raw.get("confidence", profile_prov.confidence))
            )
        else:
            name = str(raw)
            aliases = []
            raw_d = demand_map.get(str(raw), 0)
            demand = normalize_demand(raw_d, clip=demand_scale)
            metric = profile_prov.metric
            source = profile_prov.source
            source_type = profile_prov.source_type
            doc_date = profile_prov.date
            confidence = profile_prov.confidence

        if name:
            tools.append({
                "name": name,
                "demand": demand,
                "aliases": aliases,
                "provenance": {
                    "metric": metric,
                    "source": source,
                    "source_type": source_type,
                    "date": doc_date,
                    "confidence": confidence,
                },
            })

    return {
        "foundation_concepts": concepts,
        "toolchain": tools,
        "provenance": profile_prov.model_dump(),
    }


def extract_market_profile(
    rows: Iterable[str],
    concepts: Iterable[str] | None = None,
    tools: Iterable[str] | None = None,
    limit: int = 30,
    source_label: str = "Uploaded Job Postings CSV",
) -> MarketProfile:
    """Measure known concepts/tools as the share of CSV rows containing each term.
    Handles both (rows, concepts, tools) and (rows, vocabulary).
    """
    row_list = list(rows)
    total_postings = len(row_list)
    normalized_rows = [str(row).lower() for row in row_list]
    counts: Counter[str] = Counter()

    # Determine vocabulary and explicit groupings
    if concepts is not None and tools is not None:
        concept_list = list(concepts)
        tool_list = list(tools)
        vocabulary = list(dict.fromkeys(concept_list + tool_list))
        explicit_groups = True
    elif concepts is not None and tools is None:
        vocabulary = list(concepts)
        concept_list = []
        tool_list = []
        explicit_groups = False
    else:
        vocabulary = []
        concept_list = []
        tool_list = []
        explicit_groups = False

    for term in vocabulary:
        normalized = re.sub(r"\s+", " ", str(term).strip().lower())
        pattern = re.compile(r"(?<!\w)" + re.escape(normalized) + r"(?!\w)")
        counts[term] = sum(bool(pattern.search(row)) for row in normalized_rows)
    prevalences = {
        term: round(count / total_postings * 100, 2) if total_postings else 0.0
        for term, count in counts.items()
    }

    prov = MarketProvenance(
        metric="posting_prevalence_percent",
        source=source_label,
        source_type="DERIVED",
        date=date.today().isoformat(),
        denominator=total_postings,
        confidence=0.0,
    )

    if explicit_groups:
        demand_dict = {term: prevalences[term] for term in vocabulary}
        return MarketProfile(
            foundation_concepts=concept_list,
            toolchain=tool_list,
            demand=demand_dict,
            provenance=prov,
        )

    ranked = [term for term, _ in counts.most_common(limit)]
    half = (len(ranked) + 1) // 2
    demand_dict = {term: prevalences[term] for term in ranked}
    
    return MarketProfile(
        foundation_concepts=ranked[:half],
        toolchain=ranked[half:],
        demand=demand_dict,
        provenance=prov,
    )
