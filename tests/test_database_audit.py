import json
import sqlite3

from scripts.audit_sqlite_metadata import inspect_database


def test_reports_schema_counts_and_sensitive_column_names_without_row_values(tmp_path):
    database = tmp_path / "sample.db"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE politicians (
            id INTEGER PRIMARY KEY,
            full_name TEXT,
            date_of_birth TEXT,
            external_id TEXT
        );
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY,
            external_trade_id TEXT,
            trade_date TEXT,
            disclosure_date TEXT
        );
        INSERT INTO politicians VALUES
            (1, 'PRIVATE TEST NAME', '1980-01-02', 'P-1'),
            (2, 'ANOTHER TEST NAME', '1970-03-04', 'P-1');
        INSERT INTO trades VALUES
            (1, 'T-1', '2020-01-01', '2020-02-01'),
            (2, 'T-2', '2024-01-01', '2024-02-01');
        """
    )
    connection.commit()
    connection.close()

    report = inspect_database(database)
    serialized = json.dumps(report)

    assert report["sqlite_integrity_check"] == ["ok"]
    assert {table["table"]: table["row_count"] for table in report["tables"]} == {
        "politicians": 2,
        "trades": 2,
    }
    politician_report = next(t for t in report["tables"] if t["table"] == "politicians")
    assert "date_of_birth" in politician_report["potentially_sensitive_columns"]
    assert politician_report["sensitive_column_non_null_counts"]["date_of_birth"] == 2
    assert politician_report["duplicate_identifier_counts"]["external_id"] == 1
    trade_report = next(t for t in report["tables"] if t["table"] == "trades")
    assert trade_report["date_coverage"]["trade_date"]["minimum"] == "2020-01-01"
    assert "PRIVATE TEST NAME" not in serialized
    assert "ANOTHER TEST NAME" not in serialized
    assert "1980-01-02" not in serialized


def test_rejects_non_sqlite_file(tmp_path):
    file_path = tmp_path / "not-a-database.db"
    file_path.write_text("not sqlite", encoding="utf-8")
    try:
        inspect_database(file_path)
    except ValueError as error:
        assert "not a SQLite" in str(error)
    else:
        raise AssertionError("Expected non-SQLite file to be rejected")


def test_rejects_missing_database(tmp_path):
    try:
        inspect_database(tmp_path / "missing.db")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing database to be rejected")
