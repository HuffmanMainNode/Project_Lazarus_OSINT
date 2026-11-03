# SQLite Database Review

Run the metadata-only review before publishing or retaining a generated database:

```bash
python scripts/audit_sqlite_metadata.py lazarus_politrack.db
```

The report emits table names, row counts, column names/types, likely sensitive column names and non-null counts, duplicate identifier counts, date coverage for trade/disclosure dates, file size, and SQLite's structural integrity result. It does not print row values.

## Important limits

This is a screening aid, not a privacy or provenance certification. Column-name matching is heuristic. A database may contain sensitive data in innocuous-looking columns, and aggregate counts cannot establish that records are accurate, lawfully collected, or authorized for public release.

A passing SQLite integrity check only means the database pages and structures pass SQLite's check. It does not validate transaction records or source attribution.

The currently tracked `lazarus_politrack.db` must still receive a human provenance and public-release review before being represented as a verified public dataset.
