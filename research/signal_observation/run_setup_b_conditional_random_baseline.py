"""Run Setup B conditional random baseline over committed local Bitget 4H CSV data."""

from __future__ import annotations

from pathlib import Path

from .csv_loader import load_ohlcv_csv
from .setup_b_conditional_random_baseline import (
    format_conditional_baseline_report,
    run_all_conditional_baselines,
    write_conditional_baseline_artifacts,
)
from .setup_b_random_baseline import load_json


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data" / "bitget"
OUTPUT_DIR = PACKAGE_DIR / "output" / "bitget"
OBSERVATIONS_PATH = OUTPUT_DIR / "setup_b_observations.json"
PRODUCT_TYPE = "USDT-FUTURES"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def run_setup_b_conditional_random_baseline() -> dict[str, object]:
    """Run conditional random baseline and write artifacts."""

    observations = load_json(OBSERVATIONS_PATH)
    if not isinstance(observations, list):
        raise ValueError("Setup B observations artifact must contain a list")

    candles_by_symbol = {
        symbol: load_ohlcv_csv(DATA_DIR / f"{symbol}_{PRODUCT_TYPE}_4H.csv")
        for symbol in SYMBOLS
    }

    report = run_all_conditional_baselines(
        observations=observations,
        candles_by_symbol=candles_by_symbol,
    )

    write_conditional_baseline_artifacts(
        report,
        text_path=OUTPUT_DIR / "setup_b_conditional_random_baseline.txt",
        json_path=OUTPUT_DIR / "setup_b_conditional_random_baseline.json",
    )
    return report


def main() -> int:
    """CLI entrypoint."""

    report = run_setup_b_conditional_random_baseline()
    print(format_conditional_baseline_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
