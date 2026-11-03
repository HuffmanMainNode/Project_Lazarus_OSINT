"""Executive-official ingestion is disabled until a verified source adapter exists."""

import logging

logger = logging.getLogger(__name__)


def fetch_executive_data():
    logger.warning("Executive adapter is not implemented; no sample records are returned.")
    return []


def ingest_executives():
    logger.warning("No executive officials ingested because no verified source adapter is configured.")
    return 0


if __name__ == "__main__":
    ingest_executives()
