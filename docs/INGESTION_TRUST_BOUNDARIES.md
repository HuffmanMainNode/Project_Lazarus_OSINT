# Ingestion Trust Boundaries

## Verified-source requirement

A record must not enter the research database merely because a scraper or adapter returned an object. Ingestion requires a stable source identifier, a matched official identity, and traceable source context. Missing identity is a skipped record, never an assignment to the first person in the database.

## Disabled sources and rules

- SEC Form 4 adapter: returns no records until a real filing client and transaction parser exist. The prior hard-coded example was not a live filing.
- State, executive, and judicial sample adapters: return no records until verified source adapters exist. The former hard-coded people and identifiers were examples, not source observations.
- Committee ingestion: disabled. The prior implementation assigned memberships using `hash(full_name) % 2`; these were arbitrary and are not evidence.
- Committee-sector red-flag rule: disabled until dated, sourced membership records are available.
- QuiverQuant: requires `QUIVERQUANT_API_TOKEN`; the placeholder token is not used.

## Trade identity and retry behavior

Provider-supplied transaction identifiers are preferred. If unavailable, the importer creates a deterministic hash from stable source fields. Records without enough stable identity or a matched official are skipped. This reduces false attribution and retry duplicates, but a composite hash can still collide for two genuinely distinct, otherwise identical source records. Provider-native unique IDs remain preferable.

## Historical database caution

The existing SQLite database contains 536 politician-committee links, but the old ingestion code generated these assignments arbitrarily. The current code no longer creates such links and the committee-conflict rule is disabled. The existing links are not automatically deleted; they require a separate, reviewed data correction because they are already part of the public database.

This project is an experimental research tool. It does not determine corruption, criminality, intent, or wrongdoing.
