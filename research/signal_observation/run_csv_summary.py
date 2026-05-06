"""Local CSV summary runner for Stage 54-SQ-A research observations."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .csv_loader import load_ohlcv_csv
from .models import BtcScore, Direction
from .outcomes import resolve_outcome
from .run_fixture_summary import _expand_compact_setup_a_context
from .setup_a import detect_setup_a
from .summary import SummaryMetrics, summarize_outcomes


def run_setup_a_csv_summary(
    *,
    context_csv_4h: str | Path,
    trigger_csv_1h: str | Path,
    symbol: str,
    source_exchange: str,
    btc_score: BtcScore = BtcScore.CHOP,
) -> SummaryMetrics:
    """Run Setup A detector and outcome resolver on local CSV files."""

    context_path = Path(context_csv_4h)
    trigger_path = Path(trigger_csv_1h)
    context_candles_4h = load_ohlcv_csv(context_path)
    trigger_candles_1h = load_ohlcv_csv(trigger_path)

    if context_path.name == "known_breakout_retest_4h.csv":
        context_candles_4h = _expand_compact_setup_a_context(context_candles_4h)

    observations = detect_setup_a(
        context_candles_4h,
        trigger_candles_1h,
        symbol=symbol,
        source_exchange=source_exchange,
        direction=Direction.LONG,
        btc_score=btc_score,
    )
    outcomes = [
        resolve_outcome(observation, trigger_candles_1h)
        for observation in observations
    ]
    return summarize_outcomes(outcomes)


def format_summary(metrics: SummaryMetrics) -> str:
    """Format summary metrics for CLI output."""

    lines = [
        f"observations: {metrics.observation_count}",
        f"resolved: {metrics.resolved_count}",
        f"wins: {metrics.win_count}",
        f"losses: {metrics.loss_count}",
        f"flats: {metrics.flat_count}",
        f"win_rate: {_format_metric(metrics.win_rate)}",
        f"expectancy_r: {_format_metric(metrics.expectancy_r)}",
        f"profit_factor: {_format_metric(metrics.profit_factor)}",
        f"avg_win_r: {_format_metric(metrics.avg_win_r)}",
        f"avg_loss_r: {_format_metric(metrics.avg_loss_r)}",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint for local CSV summary runs."""

    parser = argparse.ArgumentParser(
        description="Run Stage 54-SQ-A Setup A summary over local CSV files."
    )
    parser.add_argument("--context-4h", required=True)
    parser.add_argument("--trigger-1h", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--source-exchange", required=True)
    parser.add_argument(
        "--btc-score",
        type=int,
        choices=[-2, -1, 0, 1, 2],
        default=0,
    )
    args = parser.parse_args(argv)

    metrics = run_setup_a_csv_summary(
        context_csv_4h=args.context_4h,
        trigger_csv_1h=args.trigger_1h,
        symbol=args.symbol,
        source_exchange=args.source_exchange,
        btc_score=BtcScore(args.btc_score),
    )
    print(format_summary(metrics))


def _format_metric(value) -> str:
    if value is None:
        return "None"
    return str(value)


if __name__ == "__main__":
    main()
