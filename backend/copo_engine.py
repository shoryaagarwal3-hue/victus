import json
from pathlib import Path


def load_po_definitions(path: str | Path = "data/po_definitions.json") -> dict[str, str]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def build_matrix(outcomes: list[str], mappings: list[dict], po_definitions: dict[str, str]) -> list[dict]:
    """Produce rows with 1-3 strengths; blank cells are zero for NBA-style matrices."""
    by_outcome = {m.get("course_outcome"): m for m in mappings}
    rows = []
    for outcome in outcomes:
        row = {"Course Outcome": outcome}
        mapped = {x.get("po"): int(x.get("strength", 0)) for x in by_outcome.get(outcome, {}).get("mapped_pos", [])}
        row.update({po: mapped.get(po, 0) for po in po_definitions})
        rows.append(row)
    return rows
