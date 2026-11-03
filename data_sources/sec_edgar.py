"""SEC EDGAR adapter boundary.

This module intentionally returns no filings until a real SEC submissions/filings
client, identity mapping, and Form 4 transaction parser are implemented.
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class SEC_EdgarAPI:
    def fetch_form4_filings(self) -> List[Dict]:
        logger.warning(
            "SEC Form 4 ingestion is NOT_IMPLEMENTED; no simulated records are returned."
        )
        return []
