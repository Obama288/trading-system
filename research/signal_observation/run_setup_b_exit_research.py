"""Run Stage 54-SQ-B7 bounded exit research from local 4H files."""

from __future__ import annotations

from pathlib import Path

from .setup_b_exit_research import (
    EXPECTED_HIGH_VOL_N,
    build_exit_research_report,
    format_exit_research_report,
    reconstruct_high_vol_entries,
    write_exit_research_artifacts,
)


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data" / "bitget"
OUTPUT_DIR = PACKAGE_DIR / "output" / "bitget"
TEXT_OUTPUT = OUTPUT_DIR / "setup_b_exit_research.txt"
JSON_OUTPUT = OUTPUT_DIR / "setup_b_exit_research.json"


def run_exit_research() -> dict[str, object]:
    """Reconstruct high-vol validation entries and write B7 artifacts."""

    entries, reconstruction, candles_by_symbol = reconstruct_high_vol_entries(DATA_DIR)
    if reconstruction["reconstructed_n"] != EXPECTED_HIGH_VOL_N:
        raise SystemExit(
            "B7 reconstruction mismatch: "
            f"expected {EXPECTED_HIGH_VOL_N}, got {reconstruction['reconstructed_n']}"
        )

    report = build_exit_research_report(
        entries=entries,
        candles_by_symbol=candles_by_symbol,
        reconstruction=reconstruction,
    )
    write_exit_research_artifacts(
        report,
        text_path=TEXT_OUTPUT,
        json_path=JSON_OUTPUT,
    )
    return report


def main() -> int:
    """CLI entrypoint."""

    report = run_exit_research()
    print(format_exit_research_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
