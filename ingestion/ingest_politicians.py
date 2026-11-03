"""Import current-legislator records from a caller-supplied public JSON file.

Date of birth is not imported unless explicitly enabled because it is not
needed for the financial-disclosure research workflow.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

project_dir = Path(__file__).resolve().parents[1]
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from core.database import SessionLocal
from models.politicians import Politician

logger = logging.getLogger(__name__)


def parse_and_ingest(file_path=None, db=None, include_date_of_birth=False):
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    configured_path = file_path or os.environ.get("LEGISLATORS_JSON_PATH")
    source_path = (
        Path(configured_path)
        if configured_path
        else project_dir / "data" / "legislators-current.json"
    )

    if not source_path.is_file():
        logger.error(
            "Legislator source file not found at %s; set LEGISLATORS_JSON_PATH.",
            source_path,
        )
        if owns_session:
            session.close()
        return 0

    try:
        with source_path.open("r", encoding="utf-8") as source_file:
            data = json.load(source_file)
        if not isinstance(data, list):
            raise ValueError("Legislator source must contain a JSON array.")

        processed = 0
        for item in data:
            if not isinstance(item, dict):
                continue
            bioguide_id = item.get("id", {}).get("bioguide")
            if not bioguide_id:
                continue

            name_dict = item.get("name", {})
            full_name = f"{name_dict.get('first', '')} {name_dict.get('last', '')}".strip()
            if not full_name:
                continue

            terms = item.get("terms", [])
            latest_term = terms[-1] if isinstance(terms, list) and terms else {}
            chamber = latest_term.get("type")
            if chamber == "rep":
                chamber = "House"
            elif chamber == "sen":
                chamber = "Senate"

            values = {
                "full_name": full_name,
                "chamber": chamber,
                "party": latest_term.get("party"),
                "state_code": latest_term.get("state"),
                "district": (
                    str(latest_term.get("district"))
                    if latest_term.get("district") is not None
                    else None
                ),
            }

            if include_date_of_birth:
                birthday = item.get("bio", {}).get("birthday")
                try:
                    values["date_of_birth"] = (
                        datetime.strptime(birthday, "%Y-%m-%d").date()
                        if birthday
                        else None
                    )
                except ValueError:
                    values["date_of_birth"] = None

            politician = session.query(Politician).filter(
                Politician.external_id == bioguide_id
            ).first()
            if politician is None:
                session.add(Politician(external_id=bioguide_id, **values))
            else:
                for key, value in values.items():
                    setattr(politician, key, value)
            processed += 1

        session.commit()
        logger.info("Processed %s legislator records.", processed)
        return processed
    except Exception:
        session.rollback()
        logger.exception("Legislator ingestion failed")
        raise
    finally:
        if owns_session:
            session.close()


if __name__ == "__main__":
    parse_and_ingest()
