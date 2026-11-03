"""Optional QuiverQuant API wrapper.

A real provider token must be supplied explicitly or through
QUIVERQUANT_API_TOKEN. No placeholder credential is sent.
"""
import logging
import os
import time
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class QuiverQuantAPI:
    BASE_URL = "https://api.quiverquant.com/beta"

    def __init__(self, token: Optional[str] = None):
        resolved_token = token or os.environ.get("QUIVERQUANT_API_TOKEN")
        if not resolved_token:
            raise ValueError(
                "QuiverQuant token missing. Set QUIVERQUANT_API_TOKEN or pass token explicitly."
            )
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Token {resolved_token}",
        }

    def _request(self, endpoint: str, retries: int = 3) -> Optional[List[Dict]]:
        if not endpoint or endpoint.startswith("/") or ".." in endpoint.split("/"):
            raise ValueError("endpoint must be a relative API path")
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, list):
                    logger.error("QuiverQuant returned an unexpected response shape.")
                    return None
                if not all(isinstance(item, dict) for item in payload):
                    logger.error("QuiverQuant returned non-object records.")
                    return None
                return payload
            except requests.exceptions.HTTPError as error:
                if response.status_code == 429:
                    logger.warning("QuiverQuant rate limited; retrying attempt %s.", attempt + 1)
                    time.sleep(2 ** attempt)
                else:
                    logger.error("QuiverQuant HTTP request failed: %s", type(error).__name__)
                    break
            except (requests.exceptions.RequestException, ValueError) as error:
                logger.error("QuiverQuant request failed: %s", type(error).__name__)
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def get_senate_trading(self) -> List[Dict]:
        return self._request("live/senatetrading") or []

    def get_house_trading(self) -> List[Dict]:
        return self._request("live/housetrading") or []
