"""Judicial-official ingestion is disabled until a verified source adapter exists."""

import logging

logger = logging.getLogger(__name__)


def fetch_judicial_data():
    logger.warning("Judicial adapter is not implemented; no sample records are returned.")
    return []


def ingest_judicials():
    logger.warning("No judicial officials ingested because no verified source adapter is configured.")
    return 0


if __name__ == "__main__":
    ingest_judicials()
