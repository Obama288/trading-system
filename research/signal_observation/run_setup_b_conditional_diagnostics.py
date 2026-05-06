"""Run Setup B conditional diagnostics over committed local Bitget 4H CSV data."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from .csv_loader import load_ohlcv_csv
from .setup_b_conditional_diagnostics import (
    build_conditional_report,
    format_conditional_report,
    write_conditional_artifacts,
)
from .setup_b_random_baseline import load_json


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data" / "bitget"
OUTPUT_DIR = PACKAGE_DIR / "output" / "bitget"
OBSERVATIONS_PATH = OUTPUT_DIR / "setup_b_observations.json"
RANDOM_BASELINE_PATH = OUTPUT_DIR / "setup_b_random_baseline.json"
PRODUCT_TYPE = "USDT-FUTURES"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def _load_random_1r_median_expectancy() -> Decimal | None:
    try:
        baseline = load_json(RANDOM_BASELINE_PATH)
        if not isinstance(baseline, dict):
            return None
        rb = baseline.get("random_baseline")
        if not isinstance(rb, dict):
            return None
        exp = rb.get("1r", {}).get("expectancy_r", {})
        if not isinstance(exp, dict):
            return None
        median = exp.get("median")
        if median is None:
            return None
        return Decimal(str(median))
    except Exception:
        return None


def run_setup_b_conditional_diagnostics() -> dict[str, object]:
    """Run conditional diagnostics and write artifacts."""

    observations = load_json(OBSERVATIONS_PATH)
    if not isinstance(observations, list):
        raise ValueError("Setup B observations artifact must contain a list")

    candles_by_symbol = {
        symbol: load_ohlcv_csv(DATA_DIR / f"{symbol}_{PRODUCT_TYPE}_4H.csv")
        for symbol in SYMBOLS
    }

    report = build_conditional_report(
        observations,
        candles_by_symbol,
        random_1r_median_expectancy=_load_random_1r_median_expectancy(),
    )

    write_conditional_artifacts(
        report,
        text_path=OUTPUT_DIR / "setup_b_conditional_diagnostics.txt",
        json_path=OUTPUT_DIR / "setup_b_conditional_diagnostics.json",
    )
    return report


def main() -> int:
    """CLI entrypoint."""

    report = run_setup_b_conditional_diagnostics()
    print(format_conditional_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
