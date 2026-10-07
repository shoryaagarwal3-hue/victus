import json
from pathlib import Path
from typing import Any


def load_catalog(path: str | Path = "data/cert_catalog.json") -> dict[str, list[dict[str, str]]]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def map_certifications(tools: list[str], path: str | Path = "data/cert_catalog.json") -> dict[str, list[dict[str, str]]]:
    catalog = load_catalog(path)
    return {tool: catalog.get(tool, []) for tool in tools}
