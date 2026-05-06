"""Local Setup A diagnostics runner for Bitget CSV research data."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .csv_loader import load_ohlcv_csv
from .setup_a_diagnostics import (
    SetupAFunnelDiagnostics,
    diagnose_setup_a,
    format_diagnostics_report,
    write_diagnostics_artifacts,
)


SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
PRODUCT_TYPE = "USDT-FUTURES"
SOURCE_EXCHANGE = "bitget_public"
DEFAULT_DATA_DIR = Path("research/signal_observation/data/bitget")
DEFAULT_OUTPUT_DIR = Path("research/signal_observation/output/bitget")


def run_bitget_setup_a_diagnostics(
    *,
    data_dir: str | Path = DEFAULT_DATA_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    symbols: Sequence[str] = SYMBOLS,
) -> list[SetupAFunnelDiagnostics]:
    """Run Setup A diagnostics over committed local Bitget CSV data."""

    data_path = Path(data_dir)
    output_path = Path(output_dir)
    diagnostics: list[SetupAFunnelDiagnostics] = []

    for symbol in symbols:
        context_csv = data_path / f"{symbol}_{PRODUCT_TYPE}_4H.csv"
        trigger_csv = data_path / f"{symbol}_{PRODUCT_TYPE}_1H.csv"
        context_candles = load_ohlcv_csv(context_csv)
        trigger_candles = load_ohlcv_csv(trigger_csv)
        diagnostics.append(
            diagnose_setup_a(
                context_candles,
                trigger_candles,
                symbol=symbol,
                source_exchange=SOURCE_EXCHANGE,
            )
        )

    write_diagnostics_artifacts(
        diagnostics,
        text_path=output_path / "setup_a_funnel_diagnostics.txt",
        json_path=output_path / "setup_a_funnel_diagnostics.json",
    )
    return diagnostics


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint for local Setup A diagnostics."""

    parser = argparse.ArgumentParser(
        description="Run Setup A funnel diagnostics over local Bitget CSV files."
    )
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    diagnostics = run_bitget_setup_a_diagnostics(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
    )
    print(format_diagnostics_report(diagnostics), end="")


if __name__ == "__main__":
    main()
