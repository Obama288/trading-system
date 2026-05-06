"""Local Setup A sensitivity diagnostics runner for Bitget CSV research data."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .csv_loader import load_ohlcv_csv
from .setup_a_sensitivity import (
    VARIANTS,
    SensitivityVariant,
    SensitivityVariantResult,
    SensitivitySymbolResult,
    compute_variant_totals,
    format_sensitivity_report,
    run_sensitivity_variant,
    write_sensitivity_artifacts,
)


SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
PRODUCT_TYPE = "USDT-FUTURES"
SOURCE_EXCHANGE = "bitget_public"
DEFAULT_DATA_DIR = Path("research/signal_observation/data/bitget")
DEFAULT_OUTPUT_DIR = Path("research/signal_observation/output/bitget")


def run_bitget_setup_a_sensitivity(
    *,
    data_dir: str | Path = DEFAULT_DATA_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    symbols: Sequence[str] = SYMBOLS,
    variants: Sequence[SensitivityVariant] = VARIANTS,
) -> list[SensitivityVariantResult]:
    """Run Setup A sensitivity analysis over committed local Bitget CSV data."""

    data_path = Path(data_dir)
    output_path = Path(output_dir)

    candle_cache: dict[str, object] = {}

    def _load_context(symbol: str):
        key = f"{symbol}_4H"
        if key not in candle_cache:
            csv = data_path / f"{symbol}_{PRODUCT_TYPE}_4H.csv"
            candle_cache[key] = load_ohlcv_csv(csv)
        return candle_cache[key]

    def _load_trigger(symbol: str):
        key = f"{symbol}_1H"
        if key not in candle_cache:
            csv = data_path / f"{symbol}_{PRODUCT_TYPE}_1H.csv"
            candle_cache[key] = load_ohlcv_csv(csv)
        return candle_cache[key]

    variant_results: list[SensitivityVariantResult] = []

    for variant in variants:
        symbol_results: list[SensitivitySymbolResult] = []
        for symbol in symbols:
            context_candles = _load_context(symbol)
            trigger_candles = _load_trigger(symbol)
            result = run_sensitivity_variant(
                context_candles,
                trigger_candles,
                symbol=symbol,
                source_exchange=SOURCE_EXCHANGE,
                variant=variant,
            )
            symbol_results.append(result)
        totals = compute_variant_totals(symbol_results, variant.name)
        variant_results.append(
            SensitivityVariantResult(
                variant=variant.name,
                symbol_results=symbol_results,
                totals=totals,
            )
        )

    write_sensitivity_artifacts(
        variant_results,
        text_path=output_path / "setup_a_sensitivity_diagnostics.txt",
        json_path=output_path / "setup_a_sensitivity_diagnostics.json",
    )
    return variant_results


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint for local Setup A sensitivity diagnostics."""

    parser = argparse.ArgumentParser(
        description="Run Setup A sensitivity diagnostics over local Bitget CSV files."
    )
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    variant_results = run_bitget_setup_a_sensitivity(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
    )
    print(format_sensitivity_report(variant_results), end="")


if __name__ == "__main__":
    main()
