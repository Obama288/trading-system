"""Run Setup C TSMOM research evaluation on local Bitget 4H CSVs."""

from __future__ import annotations

from pathlib import Path

from research.signal_observation.setup_c_tsmom import (
    analyze_tsmom,
    format_tsmom_report,
    load_bitget_4h_candles,
    write_tsmom_artifacts,
)


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data" / "bitget"
OUTPUT_DIR = PACKAGE_DIR / "output" / "bitget"
TEXT_OUTPUT_PATH = OUTPUT_DIR / "setup_c_tsmom_report.txt"
JSON_OUTPUT_PATH = OUTPUT_DIR / "setup_c_tsmom_report.json"


def run_setup_c_tsmom() -> dict[str, object]:
    """Run deterministic Setup C TSMOM evaluation."""

    candles_by_symbol = load_bitget_4h_candles(DATA_DIR)
    report = analyze_tsmom(candles_by_symbol)
    write_tsmom_artifacts(
        report,
        text_path=TEXT_OUTPUT_PATH,
        json_path=JSON_OUTPUT_PATH,
    )
    return report


def main() -> int:
    """CLI entrypoint for local research evaluation."""

    report = run_setup_c_tsmom()
    print(format_tsmom_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
