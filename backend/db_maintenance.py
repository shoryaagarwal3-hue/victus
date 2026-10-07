"""Database maintenance utilities for scan_history.sqlite."""
import sqlite3
from pathlib import Path
from typing import Any

from backend.trend_store import connect, DEFAULT_DB


def prune_scan_history(keep_latest_n: int = 50, path: str | Path = DEFAULT_DB) -> int:
    """
    Delete all but the N most recent rows per (college_name, role_track) pair.

    Args:
        keep_latest_n: Number of most recent rows to keep per college/role pair.
        path: Path to the SQLite database file.

    Returns:
        Number of rows deleted.
    """
    path = Path(path)
    if not path.exists():
        return 0

    with connect(path) as conn:
        # Get count before deletion
        before = conn.execute("SELECT COUNT(*) FROM scan_history").fetchone()[0]

        # Delete all but the N most recent per college/role
        conn.execute("""
            DELETE FROM scan_history
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (PARTITION BY college_name, role_track ORDER BY scan_date DESC) as rn
                    FROM scan_history
                )
                WHERE rn <= ?
            )
        """, (keep_latest_n,))

        conn.commit()

        # Get count after deletion
        after = conn.execute("SELECT COUNT(*) FROM scan_history").fetchone()[0]

    return before - after


def clear_scan_history(path: str | Path = DEFAULT_DB) -> int:
    """
    Wipe the scan_history table entirely.

    Args:
        path: Path to the SQLite database file.

    Returns:
        Number of rows deleted.
    """
    path = Path(path)
    if not path.exists():
        return 0

    with connect(path) as conn:
        before = conn.execute("SELECT COUNT(*) FROM scan_history").fetchone()[0]
        conn.execute("DELETE FROM scan_history")
        conn.commit()
        return before


def get_scan_history_stats(path: str | Path = DEFAULT_DB) -> dict[str, Any]:
    """
    Get statistics about the scan history database.

    Args:
        path: Path to the SQLite database file.

    Returns:
        Dictionary with stats: total_rows, unique_colleges, unique_roles, date_range
    """
    path = Path(path)
    if not path.exists():
        return {"total_rows": 0, "unique_colleges": 0, "unique_roles": 0, "date_range": None}

    with connect(path) as conn:
        stats = conn.execute("""
            SELECT
                COUNT(*) as total_rows,
                COUNT(DISTINCT college_name) as unique_colleges,
                COUNT(DISTINCT role_track) as unique_roles,
                MIN(scan_date) as earliest_date,
                MAX(scan_date) as latest_date
            FROM scan_history
        """).fetchone()

    return {
        "total_rows": stats[0],
        "unique_colleges": stats[1],
        "unique_roles": stats[2],
        "date_range": (stats[3], stats[4]) if stats[3] and stats[4] else None,
    }