import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import math
from core.database import SessionLocal
from models.politicians import Politician
from models.red_flags import RedFlag
from models.scores import PoliticianScore

logger = logging.getLogger(__name__)


class RankingEngine:
    def __init__(self):
        self.db = SessionLocal()

    def calculate_score(self, red_flags):
        if not red_flags:
            return 0.0
        total_severity = sum(flag.severity for flag in red_flags)
        score = 100 * (1 - math.exp(-0.1 * total_severity))
        return round(score, 2)

    def assign_tier(self, net_worth):
        """Describe reported wealth only; never infer corruption from wealth."""
        if net_worth is None:
            return "UNKNOWN - Net worth not verified"
        if net_worth > 50000000:
            return "Tier 1 - High reported net worth"
        if net_worth > 10000000:
            return "Tier 2 - Moderate reported net worth"
        return "Tier 3 - Lower reported net worth"

    def run_ranking(self):
        try:
            politicians = self.db.query(Politician).all()
            for pol in politicians:
                red_flags = self.db.query(RedFlag).filter(
                    RedFlag.politician_id == pol.id
                ).all()
                score_val = self.calculate_score(red_flags)

                score_record = self.db.query(PoliticianScore).filter(
                    PoliticianScore.politician_id == pol.id
                ).first()
                if not score_record:
                    score_record = PoliticianScore(
                        politician_id=pol.id, corruption_score=score_val
                    )
                    self.db.add(score_record)
                else:
                    score_record.corruption_score = score_val

                net_worth = getattr(pol, "estimated_net_worth", None)
                tier = self.assign_tier(net_worth)
                logger.info(
                    "Calculated for %s: %s; Corruption Score: %s",
                    pol.full_name, tier, score_val
                )

            self.db.commit()
            logger.info(
                "Ranking complete. Updated scores and evaluated tiers for %s politicians.",
                len(politicians)
            )
        except Exception:
            self.db.rollback()
            logger.exception("Error during ranking analysis")
            raise
        finally:
            self.db.close()


if __name__ == "__main__":
    RankingEngine().run_ranking()
