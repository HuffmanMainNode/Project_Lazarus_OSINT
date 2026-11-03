import pytest

from data_sources.quiverquant_api import QuiverQuantAPI
from data_sources.sec_edgar import SEC_EdgarAPI
from ingestion.ingest_committees import ingest_committees
from ingestion.ingest_state_officials import fetch_state_data
from ingestion.ingest_executive import fetch_executive_data
from ingestion.ingest_judicial import fetch_judicial_data
from ingestion.ingest_trades import (
    build_external_trade_id,
    parse_amount_range,
    parse_trade_date,
    resolve_politician_id,
)


def test_quiverquant_requires_a_real_token(monkeypatch):
    monkeypatch.delenv("QUIVERQUANT_API_TOKEN", raising=False)
    with pytest.raises(ValueError, match="QUIVERQUANT_API_TOKEN"):
        QuiverQuantAPI()


def test_quiverquant_uses_environment_token(monkeypatch):
    monkeypatch.setenv("QUIVERQUANT_API_TOKEN", "test-token")
    api = QuiverQuantAPI()
    assert api.headers["Authorization"] == "Token test-token"


def test_sec_adapter_returns_no_simulated_records():
    assert SEC_EdgarAPI().fetch_form4_filings() == []


def test_placeholder_government_adapters_do_not_emit_sample_people():
    assert fetch_state_data() == []
    assert fetch_executive_data() == []
    assert fetch_judicial_data() == []


def test_committee_ingestion_fails_closed_without_membership_source():
    assert ingest_committees() == 0


def test_trade_id_is_deterministic_and_prefers_provider_id():
    item = {
        "BioGuideID": "A000001",
        "Date": "2026-01-01",
        "Ticker": "ABC",
        "Transaction": "Purchase",
        "Amount": "$1,001 - $15,000",
    }
    assert build_external_trade_id(item) == build_external_trade_id(item)
    assert build_external_trade_id({**item, "transaction_id": "PTR-123"}) == "QUIVER:PTR-123"


def test_trade_id_refuses_insufficient_identity():
    assert build_external_trade_id({"Ticker": "ABC"}) is None


def test_unknown_politician_is_not_assigned_to_a_default_person():
    assert resolve_politician_id(
        {"BioGuideID": "MISSING", "Representative": "Unknown Person"},
        {"A000001": 1},
        {"Known Person": 2},
    ) is None


def test_trade_date_and_amount_parsers_handle_invalid_inputs():
    assert parse_trade_date("2026-01-02").isoformat() == "2026-01-02"
    assert parse_trade_date("not-a-date") is None
    assert parse_amount_range("$1,000 - $15,000") == (1000.0, 15000.0)
    assert parse_amount_range("unknown") == (None, None)


from ingestion.ingest_trades import ingest_trades
from models.issuers import Issuer
from models.politicians import Politician
from models.trades import Trade


class FakeTradeAPI:
    def __init__(self, records):
        self.records = records

    def get_house_trading(self):
        return self.records


def test_ingestion_skips_unmatched_official_instead_of_assigning_first_person(db_session):
    record = {
        "transaction_id": "PTR-UNKNOWN",
        "BioGuideID": "NOT-IN-DATABASE",
        "Representative": "Unmatched Official",
        "Date": "2026-01-01",
        "Ticker": "ABC",
        "Transaction": "Purchase",
        "Amount": "$1,000 - $15,000",
        "last_modified": "2026-02-01",
    }
    result = ingest_trades(db=db_session, api=FakeTradeAPI([record]))
    assert result == {"inserted": 0, "updated": 0, "skipped": 1}
    assert db_session.query(Trade).count() == 0


def test_ingestion_retries_update_the_same_stable_trade_record(db_session):
    official = Politician(full_name="Known Official", external_id="A000001")
    issuer = Issuer(name="Example Corp", ticker="ABC")
    db_session.add_all([official, issuer])
    db_session.commit()

    record = {
        "BioGuideID": "A000001",
        "Representative": "Known Official",
        "Date": "2026-01-01",
        "Ticker": "ABC",
        "Transaction": "Purchase",
        "Amount": "$1,000 - $15,000",
        "last_modified": "2026-02-01",
    }
    api = FakeTradeAPI([record])
    first = ingest_trades(db=db_session, api=api)
    second = ingest_trades(db=db_session, api=api)

    assert first == {"inserted": 1, "updated": 0, "skipped": 0}
    assert second == {"inserted": 0, "updated": 1, "skipped": 0}
    assert db_session.query(Trade).count() == 1
