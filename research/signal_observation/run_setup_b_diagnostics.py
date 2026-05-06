"""Run Setup B diagnostics over committed local Bitget 4H CSV data."""

from __future__ import annotations

from pathlib import Path

from .csv_loader import load_ohlcv_csv
from .setup_b import SignalDirection
from .setup_b_diagnostics import (
    SetupBDiagnosticsSummary,
    diagnose_setup_b,
    format_setup_b_diagnostics_report,
    write_setup_b_artifacts,
)


PACKAGE_DIR = Path(__file__).resolve().parent
BITGET_DATA_DIR = PACKAGE_DIR / "data" / "bitget"
BITGET_OUTPUT_DIR = PACKAGE_DIR / "output" / "bitget"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
PRODUCT_TYPE = "USDT-FUTURES"


def run_setup_b_diagnostics() -> tuple[list[SetupBDiagnosticsSummary], int]:
    """Run Setup B diagnostics for BTC/ETH/SOL long and short 4H data."""

    diagnostics: list[SetupBDiagnosticsSummary] = []
    observations = []
    for symbol in SYMBOLS:
        csv_path = BITGET_DATA_DIR / f"{symbol}_{PRODUCT_TYPE}_4H.csv"
        candles = load_ohlcv_csv(csv_path)
        for direction in (SignalDirection.LONG, SignalDirection.SHORT):
            summary, direction_observations = diagnose_setup_b(
                candles,
                symbol=symbol,
                direction=direction,
            )
            diagnostics.append(summary)
            observations.extend(direction_observations)

    write_setup_b_artifacts(
        diagnostics,
        observations,
        text_path=BITGET_OUTPUT_DIR / "setup_b_diagnostics.txt",
        diagnostics_json_path=BITGET_OUTPUT_DIR / "setup_b_diagnostics.json",
        observations_json_path=BITGET_OUTPUT_DIR / "setup_b_observations.json",
    )
    return diagnostics, len(observations)


def main() -> None:
    """CLI entrypoint for local diagnostics only."""

    diagnostics, _ = run_setup_b_diagnostics()
    print(format_setup_b_diagnostics_report(diagnostics), end="")


if __name__ == "__main__":
    main()
