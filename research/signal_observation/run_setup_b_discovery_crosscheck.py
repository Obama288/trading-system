"""Run Stage 54-SQ-B8 discovery-window Setup B 1R cross-check."""

from __future__ import annotations

from pathlib import Path

from .setup_b_discovery_crosscheck import (
    build_discovery_crosscheck_report,
    format_discovery_crosscheck_report,
    reconstruct_discovery_high_vol_entries,
    write_discovery_crosscheck_artifacts,
)
from .setup_b_exit_research import load_json


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data" / "bitget"
OUTPUT_DIR = PACKAGE_DIR / "output" / "bitget"
B7_EXIT_JSON = OUTPUT_DIR / "setup_b_exit_research.json"
TEXT_OUTPUT = OUTPUT_DIR / "setup_b_discovery_crosscheck.txt"
JSON_OUTPUT = OUTPUT_DIR / "setup_b_discovery_crosscheck.json"


def run_discovery_crosscheck() -> dict[str, object]:
    """Reconstruct discovery high-vol entries and write B8 artifacts."""

    entries, reconstruction, candles_by_symbol = reconstruct_discovery_high_vol_entries(DATA_DIR)
    b7_artifact = load_json(B7_EXIT_JSON)
    report = build_discovery_crosscheck_report(
        entries=entries,
        candles_by_symbol=candles_by_symbol,
        reconstruction=reconstruction,
        b7_exit_artifact=b7_artifact,
    )
    write_discovery_crosscheck_artifacts(
        report,
        text_path=TEXT_OUTPUT,
        json_path=JSON_OUTPUT,
    )
    return report


def main() -> int:
    """CLI entrypoint."""

    report = run_discovery_crosscheck()
    print(format_discovery_crosscheck_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
