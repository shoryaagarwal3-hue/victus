"""Sync curriculum catalog JSON records into the SQLite database.

Standalone script to mirror data/cu_cse_curriculum_catalog.json into
data/cu_cse_curriculum.sqlite3 using backend.cu_curriculum_catalog APIs.
"""
from pathlib import Path
import sqlite3
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from backend.cu_curriculum_catalog import load_catalog, sync_catalog_records

def sync():
    catalog_json = BASE / "data" / "cu_cse_curriculum_catalog.json"
    database_sqlite = BASE / "data" / "cu_cse_curriculum.sqlite3"

    print(f"Loading catalog from {catalog_json}...")
    records = load_catalog(catalog_json)
    print(f"Loaded {len(records)} records from JSON.")

    print(f"Upserting records into {database_sqlite}...")
    sync_catalog_records(records, database_sqlite)

    # Verify count in SQLite
    conn = sqlite3.connect(database_sqlite)
    cur = conn.cursor()
    count = cur.execute("SELECT count(*) FROM curriculum_sources").fetchone()[0]
    conn.close()

    print(f"Verification: {count} records currently in SQLite curriculum_sources table.")
    assert count == len(records), f"Mismatch: {count} in SQLite != {len(records)} in JSON"
    print("Catalog sync completed successfully.")

if __name__ == "__main__":
    sync()
