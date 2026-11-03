from datetime import date

from analysis.redflag_engine import RedFlagEngine
from models.committees import Committee
from models.issuers import Issuer
from models.politicians import Politician
from models.red_flags import RedFlag
from models.trades import Trade


def make_trade(db_session, **overrides):
    politician = Politician(full_name="Test Official", external_id="TEST-TRADE-001")
    issuer = Issuer(name="Example Energy", ticker="EXE", sector="Energy")
    committee = Committee(name="Energy and Commerce", code="TEST-ENERGY")
    politician.committees.append(committee)
    db_session.add_all([politician, issuer, committee])
    db_session.flush()

    values = {
        "politician_id": politician.id,
        "issuer_id": issuer.id,
        "external_trade_id": "TRADE-001",
        "trade_date": date(2026, 1, 1),
        "disclosure_date": date(2026, 3, 1),
        "days_until_disclosure": 59,
        "trade_type": "Purchase",
        "trade_amount_min": 150000,
        "trade_amount_max": 600001,
        "source_system": "test-fixture",
    }
    values.update(overrides)
    trade = Trade(**values)
    db_session.add(trade)
    db_session.commit()
    return trade


def test_timing_rules_create_review_signals(db_session):
    trade = make_trade(db_session)
    engine = RedFlagEngine(db=db_session)
    engine.check_timing_rules(trade)

    codes = {
        row.rule_code for row in db_session.query(RedFlag).all()
    }
    assert codes == {"LATE_DISCLOSURE", "PRE_LEGISLATION_SUSPICION"}


def test_timing_rules_do_not_flag_exact_thresholds(db_session):
    trade = make_trade(
        db_session,
        days_until_disclosure=45,
        trade_amount_max=500000,
        trade_amount_min=0,
    )
    engine = RedFlagEngine(db=db_session)
    engine.check_timing_rules(trade)
    assert db_session.query(RedFlag).count() == 0


def test_sector_and_purchase_rules_are_explicit_review_signals(db_session):
    trade = make_trade(db_session)
    engine = RedFlagEngine(db=db_session)
    engine.check_sector_conflicts(trade)
    engine.check_pattern_rules(trade)

    rows = db_session.query(RedFlag).order_by(RedFlag.rule_code).all()
    assert {row.rule_code for row in rows} == {
        "CLUSTERED_TRADES",
        "COMMITTEE_SECTOR_CONFLICT",
    }
    assert all("review" in row.description.lower() for row in rows)


def test_repeated_rule_evaluation_updates_instead_of_duplicating(db_session):
    trade = make_trade(db_session)
    engine = RedFlagEngine(db=db_session)
    engine._create_red_flag(trade, "REPEATABLE", 2, "First description")
    engine._create_red_flag(trade, "REPEATABLE", 4, "Updated description")
    db_session.commit()

    rows = db_session.query(RedFlag).filter_by(rule_code="REPEATABLE").all()
    assert len(rows) == 1
    assert rows[0].severity == 4
    assert rows[0].description == "Updated description"


def test_network_rule_is_explicitly_unimplemented(db_session):
    trade = make_trade(db_session)
    engine = RedFlagEngine(db=db_session)
    assert engine.check_network_rules(trade) is None
