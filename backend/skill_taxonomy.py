"""Skill taxonomy lookup for distinguishing competency categories and types."""
import json
from pathlib import Path
from typing import Any


def load_skill_taxonomy(path: str | Path) -> dict[str, tuple[str, str]]:
    """Load a normalized case-insensitive index of skill names and aliases."""
    raw: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    categories = raw.get("categories", []) if isinstance(raw, dict) else []
    index: dict[str, tuple[str, str]] = {}
    for category in categories:
        category_name = str(category.get("name", "")).strip()
        for skill in category.get("skills", []):
            skill_name = str(skill.get("name", "")).strip()
            skill_type = str(skill.get("type", "TOOL")).strip().upper()
            for name in [skill_name, *skill.get("aliases", [])]:
                normalized = str(name).strip().casefold()
                if normalized:
                    index[normalized] = (category_name, skill_type)
    return index


def classify_skill(
    skill_name: str,
    taxonomy: dict[str, tuple[str, str]],
) -> tuple[str, str]:
    """Return a known category/type without inferring a market demand level."""
    return taxonomy.get(skill_name.strip().casefold(), ("Uncategorized", "UNKNOWN"))
