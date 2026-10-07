"""Loading and flattening the structured career-role catalog."""
import json
from pathlib import Path
from typing import Any


def load_role_catalog(path: str | Path) -> list[dict[str, str]]:
    """Return normalized role/category records in catalog order."""
    raw: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    categories = raw.get("categories", []) if isinstance(raw, dict) else []
    roles: list[dict[str, str]] = []
    seen: set[str] = set()
    for category in categories:
        category_name = str(category.get("name", "")).strip()
        for role in category.get("roles", []):
            role_name = str(role).strip()
            key = role_name.casefold()
            if category_name and role_name and key not in seen:
                roles.append({"category": category_name, "name": role_name})
                seen.add(key)
    if not roles:
        raise ValueError(f"Role catalog contains no usable roles: {path}")
    return roles
