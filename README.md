# Project Lazarus OSINT

An experimental, local-first research prototype for organizing public financial-disclosure data about elected officials and exploring review signals in that data.

**This repository is not a verified corruption detector, financial-advice product, or complete public-records database.** A trade, disclosure delay, committee overlap, wealth estimate, or algorithmic score does not establish misconduct.

## What is present

- SQLAlchemy models for politicians, issuers, trades, committees, legal references, red flags, and scores.
- Early ingestion modules for selected public disclosure sources.
- Heuristic review rules for disclosure timing, broad sector/committee-name overlap, and high-value reported purchases.
- A ranking formula that aggregates rule severity. It is an uncalibrated research heuristic, not a probability, legal conclusion, or finding of corruption.
- A partial CLI. The red-flag and all-politician scoring commands invoke analysis modules; several ingest, individual-score, and export command paths currently print status/help rather than execute a complete workflow.

## Data-source and coverage limitations

- No verified 1980-to-present coverage claim is made.
- The SEC EDGAR adapter currently returns a hard-coded example record; it is not a live SEC filing client.
- The QuiverQuant wrapper requires a valid provider token. The placeholder token in source code is not a credential and will not authenticate.
- A Capitol Trades wrapper exists, but the current trade-ingestion path does not use it.
- Some ingestion paths contain placeholder behavior and incomplete identity/date matching. Do not treat imported records as authoritative without checking the original filing.
- The tracked SQLite database is a historical project artifact. A metadata-only scan found 548 politician records with populated date-of-birth fields and trade dates spanning April 2025 to April 2026. Its structure can be screened with the [database review procedure](docs/DATABASE_REVIEW.md), but its full contents, source provenance, and publication authorization still require human review; no claim is made here that every row has been independently verified.

## Research and responsible-use rules

1. Prefer primary official disclosures and link each observation to the original filing or source record.
2. Preserve source identifiers, collection time, disclosure date, transformation steps, and uncertainty.
3. Distinguish reported transaction data from estimates, inferred links, and analyst hypotheses.
4. Do not infer bribery, corruption, criminality, intent, or conflicts from wealth, party, committee membership, or a single transaction.
5. Do not collect or publish private personal information about family members. Avoid speculative offshore-account or shell-company allegations without reliable, relevant public evidence.
6. Provide correction and review paths. A flag is a lead for human review, not a verdict.
7. Respect source terms, rate limits, applicable law, and the privacy of people whose information appears in records.

## Current engineering status

This is a prototype, not a continuously operating or decentralized service. No always-on ingestion, multi-node hosting, immutable ledger, predictive market analysis, or complete automated CLI is claimed.

The ranking and red-flag engines are being hardened to avoid fabricated fallback data and destructive recalculation. Their remaining limits, including an uncalibrated score and the absence of a formal stale-finding lifecycle, are documented in the active remediation work.

## Running tests

The GitHub Actions workflow currently installs pytest, SQLAlchemy, pandas, and requests, then runs:

```bash
python -m pytest tests/
```

The repository still needs a maintained dependency manifest and a clean-install guide. Do not assume a production installation path is complete.

## Security and license

See [SECURITY.md](SECURITY.md) for vulnerability reporting and [TERMS_OF_USE.md](TERMS_OF_USE.md) for the current project terms.

The repository's MIT license and proprietary-language statements in package/terms metadata need a maintainer decision. Do not infer a settled licensing position from badges or marketing language.
