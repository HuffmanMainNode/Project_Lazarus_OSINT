import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import SessionLocal
from models.trades import Trade
from models.red_flags import RedFlag
from models.politicians import Politician
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)


class RedFlagEngine:
    def __init__(self):
        self.db = SessionLocal()

    def check_timing_rules(self, trade):
        if trade.days_until_disclosure and trade.days_until_disclosure > 45:
            self._create_red_flag(
                trade, "LATE_DISCLOSURE", 3,
                f"Trade disclosed {trade.days_until_disclosure} days after execution."
            )
        if trade.trade_amount_max and trade.trade_amount_max > 500000:
            self._create_red_flag(
                trade, "PRE_LEGISLATION_SUSPICION", 4,
                "Large trade requires review for timing context; this rule alone does not establish misconduct."
            )

    def check_sector_conflicts(self, trade):
        politician = self.db.query(Politician).options(
            joinedload(Politician.committees)
        ).filter_by(id=trade.politician_id).first()
        if politician and trade.issuer and trade.issuer.sector:
            for committee in politician.committees:
                if trade.issuer.sector.lower() in committee.name.lower():
                    self._create_red_flag(
                        trade, "COMMITTEE_SECTOR_CONFLICT", 5,
                        f"Reported trade sector ({trade.issuer.sector}) overlaps committee name ({committee.name}); review context and disclosures."
                    )

    def check_pattern_rules(self, trade):
        if trade.trade_type == "Purchase" and trade.trade_amount_min and trade.trade_amount_min >= 100000:
            self._create_red_flag(
                trade, "CLUSTERED_TRADES", 2,
                "High-value purchase pattern detected; this is a review signal, not proof of wrongdoing."
            )

    def check_network_rules(self, trade):
        # No verified network rule is implemented yet.
        return None

    def _create_red_flag(self, trade, rule_code, severity, description):
        # Idempotently update this engine's finding instead of inserting duplicates.
        existing = self.db.query(RedFlag).filter(
            RedFlag.politician_id == trade.politician_id,
            RedFlag.trade_id == trade.id,
            RedFlag.rule_code == rule_code,
        ).first()
        if existing:
            existing.severity = severity
            existing.description = description
            return existing

        red_flag = RedFlag(
            politician_id=trade.politician_id,
            trade_id=trade.id,
            rule_code=rule_code,
            severity=severity,
            description=description
        )
        self.db.add(red_flag)
        return red_flag

    def run_analysis(self):
        try:
            trades = self.db.query(Trade).options(joinedload(Trade.issuer)).all()
            for trade in trades:
                self.check_timing_rules(trade)
                self.check_sector_conflicts(trade)
                self.check_pattern_rules(trade)
                self.check_network_rules(trade)
            self.db.commit()
            logger.info("Red-flag analysis complete. Scanned %s trades.", len(trades))
        except Exception:
            self.db.rollback()
            logger.exception("Error during ranking analysis")
            raise
        finally:
            self.db.close()


if __name__ == "__main__":
    RedFlagEngine().run_analysis()
