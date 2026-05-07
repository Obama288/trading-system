"""Run Stage 54-SQ-B5 high-volatility Setup B out-of-time validation."""

from __future__ import annotations

from pathlib import Path

from .csv_loader import load_ohlcv_csv
from .setup_b_high_vol_validation import (
    DISCOVERY_START,
    PRODUCT_TYPE,
    SYMBOLS,
    build_b5_report,
    build_vol_high_eligible_indices,
    compare_actual_to_conditional_random,
    compute_validation_metrics,
    evaluate_b5_gate,
    extend_4h_csvs_backward,
    format_b5_report,
    run_validation_conditional_random,
    run_validation_observations,
    split_candles_at_discovery,
    tag_high_vol_validation,
    write_b5_artifacts,
)


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data" / "bitget"
OUTPUT_DIR = PACKAGE_DIR / "output" / "bitget"


def run_setup_b_high_vol_validation() -> dict[str, object]:
    """Run B5 out-of-time validation and write artifacts."""

    csv_extension = extend_4h_csvs_backward(DATA_DIR)

    full_candles_by_symbol = {
        symbol: load_ohlcv_csv(DATA_DIR / f"{symbol}_{PRODUCT_TYPE}_4H.csv")
        for symbol in SYMBOLS
    }

    val_candles_by_symbol, disc_candles_by_symbol = split_candles_at_discovery(
        full_candles_by_symbol
    )
    window_info = {
        sym: {
            "val_candle_count": len(val_candles_by_symbol[sym]),
            "disc_candle_count": len(disc_candles_by_symbol[sym]),
            "total_candle_count": len(full_candles_by_symbol[sym]),
        }
        for sym in SYMBOLS
    }

    all_val_observations = run_validation_observations(full_candles_by_symbol)

    tagged_observations, atr_threshold_info = tag_high_vol_validation(
        all_val_observations, full_candles_by_symbol
    )
    high_vol_observations = [
        obs for obs in tagged_observations
        if obs.get("tag_volatility_regime") == "high"
    ]

    eligible_indices = build_vol_high_eligible_indices(
        full_candles_by_symbol, val_candles_by_symbol
    )
    eligible_candle_counts = {sym: len(idx) for sym, idx in sorted(eligible_indices.items())}

    actual_metrics = compute_validation_metrics(high_vol_observations)

    random_summary = run_validation_conditional_random(
        high_vol_observations=high_vol_observations,
        eligible_indices=eligible_indices,
        full_candles_by_symbol=full_candles_by_symbol,
    )

    comparison = compare_actual_to_conditional_random(actual_metrics, random_summary)
    b5_gate = evaluate_b5_gate(actual_metrics, random_summary, len(high_vol_observations))

    report = build_b5_report(
        csv_extension=csv_extension,
        window_info=window_info,
        all_val_observations=all_val_observations,
        high_vol_observations=high_vol_observations,
        atr_threshold_info=atr_threshold_info,
        eligible_candle_counts=eligible_candle_counts,
        actual_metrics=actual_metrics,
        random_summary=random_summary,
        comparison=comparison,
        b5_gate=b5_gate,
    )
    write_b5_artifacts(
        report,
        text_path=OUTPUT_DIR / "setup_b_high_vol_validation.txt",
        json_path=OUTPUT_DIR / "setup_b_high_vol_validation.json",
    )
    return report


def main() -> int:
    """CLI entrypoint."""

    report = run_setup_b_high_vol_validation()
    print(format_b5_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
