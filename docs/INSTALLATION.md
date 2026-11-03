# Local setup

This repository is an experimental, local-first Python research prototype. The supported development/test setup uses Python 3.10 or newer.

## 1. Create an isolated environment

```bash
python -m venv .venv
```

Activate it:

- macOS/Linux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`

## 2. Install dependencies

For the application and CLI:

```bash
python -m pip install -r requirements.txt
```

For tests and local development:

```bash
python -m pip install -r requirements-dev.txt
```

The dependency files declare supported version ranges. They are not a fully pinned lockfile; production or reproducible deployments should generate and review a platform-specific lock with hashes.

## 3. Configure data sources

The QuiverQuant integration requires a valid provider credential:

```bash
export QUIVERQUANT_API_TOKEN="your-provider-token"
```

PowerShell:

```powershell
$env:QUIVERQUANT_API_TOKEN = "your-provider-token"
```

Do not commit tokens or place them in issue reports. No external API is called by the test suite.

To ingest a locally supplied current-legislator JSON file, set `LEGISLATORS_JSON_PATH` to its path. Date-of-birth ingestion is disabled by default.

## 4. Run supported workflows

From the repository root:

```bash
python -m cli.lazarus_cli --help
python -m cli.lazarus_cli ingest --politicians
python -m cli.lazarus_cli ingest --trades
python -m cli.lazarus_cli ingest --all
python -m cli.lazarus_cli redflags --run
python -m cli.lazarus_cli score --all
```

The trade workflow requires the QuiverQuant token and configured database. The SEC, committee, state, executive, and judicial ingestion paths remain disabled until verified adapters exist.

## 5. Run checks

```bash
python -m pytest tests/ -q
python scripts/audit_sqlite_metadata.py lazarus_politrack.db
```

The metadata audit reports aggregate structure only. It does not validate row accuracy, provenance, publication rights, or privacy suitability.

## Database warning

The tracked SQLite file is a historical artifact. Its contents have not been independently validated for accuracy or publication authorization. It contains unverified committee assignments and date-of-birth values. Do not treat it as a vetted dataset or use it as a trusted source without a separate human provenance and privacy review.

For a fresh local database, set `DATABASE_URL` to a new SQLite path before running workflows. Back up any database before schema or ingestion experiments.
