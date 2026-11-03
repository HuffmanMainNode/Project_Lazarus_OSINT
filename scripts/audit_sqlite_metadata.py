#!/usr/bin/env python3
"""Report SQLite database structure and aggregate metadata without exposing row values."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

SENSITIVE_COLUMN = re.compile(
    r"(email|phone|address|ssn|social_security|passport|account|"
    r"date_of_birth|dob|birth_date|home_|personal|private)",
    re.IGNORECASE,
)
DATE_COLUMNS = {"trade_date", "disclosure_date"}
IDENTIFIER_COLUMNS = {"external_id", "external_trade_id", "ticker", "code"}


def _quoted_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def inspect_database(database_path: str | Path) -> dict:
    path = Path(database_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Database file not found: {path.name}")

    with path.open("rb") as handle:
        if handle.read(16) != b"SQLite format 3\x00":
            raise ValueError("File is not a SQLite 3 database.")

    uri = f"file:{quote(str(path), safe='/:')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        integrity_rows = connection.execute("PRAGMA integrity_check").fetchall()
        integrity = [row[0] for row in integrity_rows]
        tables = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()

        table_reports = []
        for table_row in tables:
            table_name = table_row["name"]
            table_sql = _quoted_identifier(table_name)
            columns = connection.execute(f"PRAGMA table_info({table_sql})").fetchall()
            column_names = [column["name"] for column in columns]
            row_count = connection.execute(
                f"SELECT COUNT(*) FROM {table_sql}"
            ).fetchone()[0]

            duplicate_counts = {}
            for column_name in column_names:
                if column_name.lower() in IDENTIFIER_COLUMNS:
                    column_sql = _quoted_identifier(column_name)
                    duplicate_count = connection.execute(
                        f"SELECT COUNT(*) - COUNT(DISTINCT {column_sql}) "
                        f"FROM {table_sql} WHERE {column_sql} IS NOT NULL"
                    ).fetchone()[0]
                    duplicate_counts[column_name] = duplicate_count

            date_coverage = {}
            for column_name in column_names:
                if column_name.lower() in DATE_COLUMNS:
                    column_sql = _quoted_identifier(column_name)
                    minimum, maximum = connection.execute(
                        f"SELECT MIN({column_sql}), MAX({column_sql}) FROM {table_sql}"
                    ).fetchone()
                    date_coverage[column_name] = {
                        "minimum": minimum,
                        "maximum": maximum,
                    }

            table_reports.append({
                "table": table_name,
                "row_count": row_count,
                "columns": [
                    {"name": column["name"], "type": column["type"]}
                    for column in columns
                ],
                "potentially_sensitive_columns": [
                    name for name in column_names if SENSITIVE_COLUMN.search(name)
                ],
                "duplicate_identifier_counts": duplicate_counts,
                "date_coverage": date_coverage,
            })

        return {
            "database_file": path.name,
            "file_bytes": path.stat().st_size,
            "sqlite_integrity_check": integrity,
            "tables": table_reports,
            "privacy": "No row values are emitted by this report.",
            "limitations": [
                "Column-name matching is heuristic and cannot identify every sensitive field.",
                "Aggregate metadata does not establish data accuracy, source provenance, consent, or public-release authorization.",
                "A clean SQLite integrity check does not validate the truth of stored records.",
            ],
        }
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "database",
        nargs="?",
        default="lazarus_politrack.db",
        help="SQLite database path (default: lazarus_politrack.db)",
    )
    args = parser.parse_args()
    try:
        report = inspect_database(args.database)
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"Database audit failed: {error}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["sqlite_integrity_check"] == ["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
