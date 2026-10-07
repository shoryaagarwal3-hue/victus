from backend.trend_store import history, record_scan, seed_simulated_history


def test_scan_history_round_trip(tmp_path):
    db_path = tmp_path / "history.sqlite"
    record_scan(
        "Test University",
        "SOC Analyst",
        {"stability_index": 60.0, "drift_rate": 25.0, "health_score": 69.0, "missing_tools": ["Splunk"]},
        db_path,
    )
    rows = history("Test University", "SOC Analyst", db_path)
    assert len(rows) == 1
    assert rows[0][1] == 69.0


def test_simulated_history_is_seeded_only_once(tmp_path):
    db_path = tmp_path / "history.sqlite"
    seed_simulated_history("Test University", "SOC Analyst", 80.0, db_path)
    seed_simulated_history("Test University", "SOC Analyst", 95.0, db_path)
    rows = history("Test University", "SOC Analyst", db_path)
    assert len(rows) == 2
    assert [health for _, health in rows] == [72.0, 76.0]
