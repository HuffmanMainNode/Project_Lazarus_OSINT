"""QuiverQuant trade ingestion with explicit identity and retry boundaries."""
import hashlib
import json
import logging
import re
import sys
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.database import SessionLocal
from data_sources.quiverquant_api import QuiverQuantAPI
from models.issuers import Issuer
from models.politicians import Politician
from models.trades import Trade

logger = logging.getLogger(__name__)


def get_or_create_unknown_issuer(db):
    issuer = db.query(Issuer).filter(Issuer.ticker == "UNKNOWN").first()
    if issuer is None:
        issuer = Issuer(
            ticker="UNKNOWN",
            name="Unresolved issuer",
            sector=None,
            industry=None,
        )
        db.add(issuer)
        db.flush()
    return issuer


def build_external_trade_id(item):
    """Build a stable source ID, preferring a provider-supplied transaction ID."""
    for key in ("transaction_id", "TransactionID", "Transaction Id", "id"):
        value = item.get(key)
        if value not in (None, ""):
            return f"QUIVER:{value}"

    stable_fields = {
        "bioguide_id": item.get("BioGuideID"),
        "date": item.get("Date"),
        "ticker": item.get("Ticker"),
        "transaction": item.get("Transaction"),
        "amount": item.get("Amount"),
        "last_modified": item.get("last_modified"),
    }
    if not stable_fields["bioguide_id"] or not stable_fields["date"] or not stable_fields["transaction"]:
        return None
    encoded = json.dumps(stable_fields, sort_keys=True, separators=(",", ":"))
    return "QUIVER:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def parse_trade_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), pattern).date()
        except ValueError:
            continue
    return None


def parse_amount_range(value):
    if value is None or str(value).strip() == "":
        return None, None
    raw = str(value).strip().replace("$", "").replace(",", "")
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*-\s*([0-9]+(?:\.[0-9]+)?)", raw)
    try:
        if match:
            minimum, maximum = float(match.group(1)), float(match.group(2))
        else:
            amount = float(raw)
            minimum = maximum = amount
    except ValueError:
        return None, None
    if minimum < 0 or maximum < minimum:
        return None, None
    return minimum, maximum


def resolve_politician_id(item, by_external_id, by_name):
    external_id = item.get("BioGuideID")
    if external_id and external_id in by_external_id:
        return by_external_id[external_id]
    name = item.get("Representative")
    if name and name in by_name:
        return by_name[name]
    return None


def ingest_trades(db=None, api=None):
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    inserted = updated = skipped = 0
    try:
        provider = api if api is not None else QuiverQuantAPI()
        raw_trades = provider.get_house_trading()
        if not isinstance(raw_trades, list):
            raise TypeError("Trade provider must return a list of records.")

        issuers = session.query(Issuer).all()
        issuer_map = {issuer.ticker: issuer.id for issuer in issuers if issuer.ticker}
        unknown_issuer = get_or_create_unknown_issuer(session)

        politicians = session.query(Politician).all()
        by_external_id = {
            person.external_id: person.id
            for person in politicians if person.external_id
        }
        by_name = {
            person.full_name: person.id
            for person in politicians if person.full_name
        }

        for item in raw_trades:
            if not isinstance(item, dict):
                skipped += 1
                continue
            external_trade_id = build_external_trade_id(item)
            politician_id = resolve_politician_id(item, by_external_id, by_name)
            if external_trade_id is None or politician_id is None:
                skipped += 1
                logger.warning(
                    "Skipping provider record without stable identity or matched official."
                )
                continue

            ticker = item.get("Ticker")
            issuer_id = issuer_map.get(ticker, unknown_issuer.id)
            trade_date = parse_trade_date(item.get("Date"))
            disclosure_date = parse_trade_date(item.get("last_modified"))
            days_until_disclosure = (
                (disclosure_date - trade_date).days
                if trade_date is not None and disclosure_date is not None
                else None
            )
            amount_min, amount_max = parse_amount_range(item.get("Amount"))

            trade = session.query(Trade).filter(
                Trade.external_trade_id == external_trade_id
            ).first()
            values = {
                "politician_id": politician_id,
                "issuer_id": issuer_id,
                "trade_date": trade_date,
                "disclosure_date": disclosure_date,
                "days_until_disclosure": days_until_disclosure,
                "trade_type": item.get("Transaction"),
                "trade_amount_raw": str(item.get("Amount")) if item.get("Amount") is not None else None,
                "trade_amount_min": amount_min,
                "trade_amount_max": amount_max,
                "source_system": "QuiverQuant",
            }
            if trade is None:
                trade = Trade(external_trade_id=external_trade_id, **values)
                session.add(trade)
                inserted += 1
            else:
                for key, value in values.items():
                    setattr(trade, key, value)
                updated += 1

        session.commit()
        result = {"inserted": inserted, "updated": updated, "skipped": skipped}
        logger.info("Trade ingestion complete: %s", result)
        return result
    except Exception:
        session.rollback()
        logger.exception("Trade ingestion failed")
        raise
    finally:
        if owns_session:
            session.close()


if __name__ == "__main__":
    ingest_trades()
