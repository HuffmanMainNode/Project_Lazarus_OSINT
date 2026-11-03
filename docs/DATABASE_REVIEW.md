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


## Metadata-only baseline: 2026-11-03

The tracked database passed SQLite's structural integrity check. The metadata audit reported:

| Table | Rows |
|---|---:|
| politicians | 548 |
| trades | 10,082 |
| issuers | 987 |
| politician_committees | 536 |
| politician_scores | 548 |
| committees | 4 |
| red_flags | 0 |
| statutes | 1 |
| us_code | 2 |

The trade-date range is **2025-04-21 to 2026-04-20**. The disclosure-date range is **2025-05-05 to 2026-04-24**. This does not support the README's former 1980-to-present coverage statement.

The `politicians.date_of_birth` field is populated in all 548 rows. The metadata report does not expose those values, and the database does not itself establish their source provenance or publication authorization. Review whether this field is necessary for the project's purpose and verify the source of every retained value before representing the database as a vetted public dataset.

The database contains 10,082 trade rows and no duplicate non-null `external_trade_id` values under the metadata audit. This is a structural observation, not a validation that the trade records match original disclosures. The `red_flags` table contains zero rows in this snapshot; 548 score rows therefore should not be interpreted as 548 findings or as validated corruption assessments.

These aggregate results do not authorize public release. A human must still inspect data provenance, source terms, and the need for personal fields.
