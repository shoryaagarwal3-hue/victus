"""Tests for backend.db_maintenance module."""
import sqlite3
from pathlib import Path

from backend.db_maintenance import (
    prune_scan_history,
    clear_scan_history,
    get_scan_history_stats,
)
from backend.trend_store import record_scan, DEFAULT_DB


def test_prune_scan_history_keeps_latest_n(tmp_path):
    """Pruning keeps only the N most recent rows per college/role pair."""
    db_path = tmp_path / "test_history.sqlite"

    # Insert 10 records for College A / Role X
    for i in range(10):
        record_scan(
            "College A",
            "Role X",
            {"stability_index": 50.0 + i, "drift_rate": 10.0, "health_score": 60.0 + i, "missing_tools": []},
            db_path,
        )

    # Insert 5 records for College B / Role Y
    for i in range(5):
        record_scan(
            "College B",
            "Role Y",
            {"stability_index": 70.0 + i, "drift_rate": 5.0, "health_score": 80.0 + i, "missing_tools": []},
            db_path,
        )

    # Prune to keep latest 3 per college/role
    deleted = prune_scan_history(keep_latest_n=3, path=db_path)

    # Should have deleted 7 from College A + 2 from College B = 9 total
    assert deleted == 9

    # Verify remaining counts
    with sqlite3.connect(db_path) as conn:
        count_a = conn.execute(
            "SELECT COUNT(*) FROM scan_history WHERE college_name=? AND role_track=?",
            ("College A", "Role X"),
        ).fetchone()[0]
        count_b = conn.execute(
            "SELECT COUNT(*) FROM scan_history WHERE college_name=? AND role_track=?",
            ("College B", "Role Y"),
        ).fetchone()[0]

    assert count_a == 3
    assert count_b == 3


def test_prune_scan_history_noop_when_fewer_than_keep(tmp_path):
    """Pruning is a no-op when there are fewer rows than keep count."""
    db_path = tmp_path / "test_history.sqlite"

    # Insert only 2 records
    for i in range(2):
        record_scan(
            "College A",
            "Role X",
            {"stability_index": 50.0 + i, "drift_rate": 10.0, "health_score": 60.0 + i, "missing_tools": []},
            db_path,
        )

    # Prune to keep latest 50 - should delete nothing
    deleted = prune_scan_history(keep_latest_n=50, path=db_path)

    assert deleted == 0

    # Verify both records still exist
    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM scan_history").fetchone()[0]
    assert count == 2


def test_clear_scan_history_wipes_table(tmp_path):
    """Clear scan history deletes all rows."""
    db_path = tmp_path / "test_history.sqlite"

    # Insert 5 records
    for i in range(5):
        record_scan(
            "College A",
            "Role X",
            {"stability_index": 50.0 + i, "drift_rate": 10.0, "health_score": 60.0 + i, "missing_tools": []},
            db_path,
        )

    deleted = clear_scan_history(path=db_path)

    assert deleted == 5

    # Verify table is empty
    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM scan_history").fetchone()[0]
    assert count == 0


def test_clear_scan_history_empty_table_returns_zero(tmp_path):
    """Clear on empty table returns 0 and doesn't crash."""
    db_path = tmp_path / "test_history.sqlite"

    # Create empty table by connecting
    from backend.trend_store import connect
    connect(db_path)

    deleted = clear_scan_history(path=db_path)

    assert deleted == 0


def test_clear_scan_history_missing_db_returns_zero(tmp_path):
    """Clear on missing database file returns 0 and doesn't crash."""
    db_path = tmp_path / "nonexistent.sqlite"

    deleted = clear_scan_history(path=db_path)

    assert deleted == 0


def test_prune_scan_history_missing_db_returns_zero(tmp_path):
    """Prune on missing database file returns 0 and doesn't crash."""
    db_path = tmp_path / "nonexistent.sqlite"

    deleted = prune_scan_history(keep_latest_n=10, path=db_path)

    assert deleted == 0


def test_get_scan_history_stats_populated(tmp_path):
    """Stats returns correct info for populated database."""
    db_path = tmp_path / "test_history.sqlite"

    record_scan("College A", "Role X", {"stability_index": 50.0, "drift_rate": 10.0, "health_score": 60.0, "missing_tools": []}, db_path)
    record_scan("College A", "Role X", {"stability_index": 55.0, "drift_rate": 12.0, "health_score": 65.0, "missing_tools": []}, db_path)
    record_scan("College B", "Role Y", {"stability_index": 70.0, "drift_rate": 5.0, "health_score": 80.0, "missing_tools": []}, db_path)

    stats = get_scan_history_stats(db_path)

    assert stats["total_rows"] == 3
    assert stats["unique_colleges"] == 2
    assert stats["unique_roles"] == 2
    assert stats["date_range"] is not None


def test_get_scan_history_stats_empty(tmp_path):
    """Stats returns zeros for empty database."""
    db_path = tmp_path / "test_history.sqlite"

    from backend.trend_store import connect
    connect(db_path)

    stats = get_scan_history_stats(db_path)

    assert stats["total_rows"] == 0
    assert stats["unique_colleges"] == 0
    assert stats["unique_roles"] == 0
    assert stats["date_range"] is None


def test_get_scan_history_stats_missing_db(tmp_path):
    """Stats returns zeros for missing database."""
    db_path = tmp_path / "nonexistent.sqlite"

    stats = get_scan_history_stats(db_path)

    assert stats["total_rows"] == 0
    assert stats["unique_colleges"] == 0
    assert stats["unique_roles"] == 0
    assert stats["date_range"] is None