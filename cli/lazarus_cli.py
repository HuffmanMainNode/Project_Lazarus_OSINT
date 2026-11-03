"""Command-line entry point for the implemented Lazarus workflows."""
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Experimental public financial-disclosure research prototype"
    )
    subparsers = parser.add_subparsers(dest="command")

    ingest = subparsers.add_parser("ingest", help="Run a configured ingestion workflow")
    group = ingest.add_mutually_exclusive_group(required=True)
    group.add_argument("--trades", action="store_true", help="Ingest QuiverQuant House trades")
    group.add_argument("--politicians", action="store_true", help="Ingest current legislators JSON")
    group.add_argument("--all", action="store_true", help="Run both supported ingestion workflows")

    redflags = subparsers.add_parser("redflags", help="Run review-signal rules")
    redflags.add_argument("--run", action="store_true", required=True)

    score = subparsers.add_parser("score", help="Calculate uncalibrated review scores")
    score.add_argument("--all", action="store_true", required=True)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    failures = []

    if args.command == "ingest":
        if args.trades or args.all:
            try:
                from ingestion.ingest_trades import ingest_trades
                ingest_trades()
            except Exception as error:
                logger.error("Trade ingestion failed: %s", type(error).__name__)
                failures.append("trades")
        if args.politicians or args.all:
            try:
                from ingestion.ingest_politicians import parse_and_ingest
                parse_and_ingest()
            except Exception as error:
                logger.error("Politician ingestion failed: %s", type(error).__name__)
                failures.append("politicians")
        return 1 if failures else 0

    if args.command == "redflags":
        from analysis.redflag_engine import RedFlagEngine
        RedFlagEngine().run_analysis()
        return 0

    if args.command == "score":
        from analysis.ranking_engine import RankingEngine
        RankingEngine().run_ranking()
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
