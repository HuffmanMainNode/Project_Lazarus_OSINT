from types import SimpleNamespace

from analysis.ranking_engine import RankingEngine
from models.politicians import Politician
from models.red_flags import RedFlag
from models.scores import PoliticianScore


def test_calculate_score_is_deterministic_and_bounded():
    engine = RankingEngine(db=None)
    assert engine.calculate_score([]) == 0.0
    assert engine.calculate_score([SimpleNamespace(severity=3)]) == 25.92
    assert engine.calculate_score([
        SimpleNamespace(severity=3),
        SimpleNamespace(severity=4),
    ]) == 50.34


def test_assign_tier_does_not_infer_corruption_from_wealth():
    engine = RankingEngine(db=None)
    assert engine.assign_tier(None) == "UNKNOWN - Net worth not verified"
    assert engine.assign_tier(50_000_000) == "Tier 2 - Moderate reported net worth"
    assert engine.assign_tier(50_000_001) == "Tier 1 - High reported net worth"
    assert engine.assign_tier(10_000_000) == "Tier 3 - Lower reported net worth"


def test_run_ranking_persists_review_score(db_session):
    politician = Politician(full_name="Test Official", external_id="TEST-001")
    db_session.add(politician)
    db_session.flush()
    db_session.add(RedFlag(
        politician_id=politician.id,
        rule_code="TEST_SIGNAL",
        severity=3,
        description="Test-only review signal",
    ))
    db_session.commit()

    engine = RankingEngine(db=db_session)
    engine.run_ranking()

    score = db_session.query(PoliticianScore).filter_by(
        politician_id=politician.id
    ).one()
    assert score.corruption_score == 25.92
