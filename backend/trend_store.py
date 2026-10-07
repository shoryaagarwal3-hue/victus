import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "db" / "scan_history.sqlite"

SCHEMA = """CREATE TABLE IF NOT EXISTS scan_history (
id INTEGER PRIMARY KEY AUTOINCREMENT, college_name TEXT NOT NULL, role_track TEXT NOT NULL,
scan_date TEXT NOT NULL, stability_index REAL, drift_rate REAL, health_score REAL, missing_tool_count INTEGER)"""


def connect(path: str | Path = DEFAULT_DB) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def record_scan(college: str, role: str, scores: dict[str, Any], path: str | Path = DEFAULT_DB) -> None:
    with connect(path) as conn:
        conn.execute("INSERT INTO scan_history VALUES (NULL,?,?,?,?,?,?,?)",
                     (college, role, date.today().isoformat(), scores["stability_index"],
                      scores["drift_rate"], scores["health_score"], len(scores["missing_tools"])))


def history(college: str, role: str, path: str | Path = DEFAULT_DB) -> list[tuple[str, float]]:
    with connect(path) as conn:
        return conn.execute("SELECT scan_date, health_score FROM scan_history WHERE college_name=? AND role_track=? ORDER BY scan_date",
                            (college, role)).fetchall()


def seed_simulated_history(
    college: str, role: str, current_health: float, path: str | Path = DEFAULT_DB
) -> None:
    """Add clearly labelled prior-semester trend points for first-run demos only."""
    with connect(path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM scan_history WHERE college_name=? AND role_track=?",
            (college, role),
        ).fetchone()[0]
        if count:
            return
        today = date.today()
        for offset, adjustment in ((730, -8.0), (365, -4.0)):
            conn.execute(
                "INSERT INTO scan_history (college_name, role_track, scan_date, "
                "stability_index, drift_rate, health_score, missing_tool_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (college, role, (today - timedelta(days=offset)).isoformat(),
                 max(0.0, current_health + adjustment), 0.0,
                 max(0.0, min(100.0, current_health + adjustment)), 0),
            )
