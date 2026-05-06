"""Local fixture summary runner for Stage 54-SQ-A research observations."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from .candles import Candle
from .csv_loader import load_ohlcv_csv
from .outcomes import resolve_outcome
from .setup_a import LOOKBACK_CANDLES_4H, detect_setup_a
from .summary import SummaryMetrics, summarize_outcomes


def run_fixture_setup_a_summary() -> SummaryMetrics:
    """Run the known local Setup A fixture through detector and outcome resolver."""

    repo_root = Path(__file__).resolve().parents[2]
    fixture_dir = repo_root / "tests" / "fixtures" / "signal_observation"
    context_candles_4h = _expand_compact_setup_a_context(
        load_ohlcv_csv(fixture_dir / "known_breakout_retest_4h.csv")
    )
    trigger_candles_1h = load_ohlcv_csv(fixture_dir / "known_breakout_retest_1h.csv")

    observations = detect_setup_a(
        context_candles_4h,
        trigger_candles_1h,
        symbol="BTCUSDT",
        source_exchange="fixture",
    )
    outcomes = [
        resolve_outcome(observation, trigger_candles_1h)
        for observation in observations
    ]
    return summarize_outcomes(outcomes)


def _expand_compact_setup_a_context(candles: list[Candle]) -> list[Candle]:
    """Expand the compact fixture so the detector has a full 48-candle base."""

    if len(candles) > LOOKBACK_CANDLES_4H:
        return candles
    if len(candles) < 2:
        return candles

    breakout = candles[-1]
    seed = candles[:-1]
    start_time = breakout.timestamp - timedelta(hours=4 * LOOKBACK_CANDLES_4H)
    base: list[Candle] = []
    for index in range(LOOKBACK_CANDLES_4H):
        source = seed[index % len(seed)]
        base.append(
            Candle(
                timestamp=start_time + timedelta(hours=4 * index),
                open=source.open,
                high=source.high,
                low=source.low,
                close=source.close,
                volume=source.volume,
            )
        )
    return base + [breakout]


def main() -> None:
    """Print a concise local fixture summary."""

    metrics = run_fixture_setup_a_summary()
    print(f"observations: {metrics.observation_count}")
    print(f"resolved: {metrics.resolved_count}")
    print(f"wins: {metrics.win_count}")
    print(f"losses: {metrics.loss_count}")
    print(f"win_rate: {_format_metric(metrics.win_rate)}")
    print(f"expectancy_r: {_format_metric(metrics.expectancy_r)}")
    print(f"profit_factor: {_format_metric(metrics.profit_factor)}")


def _format_metric(value) -> str:
    if value is None:
        return "None"
    return str(value)


if __name__ == "__main__":
    main()
