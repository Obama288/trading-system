"""Run Stage 54-SQ-B6 cost-aware Setup B report from local artifacts."""

from __future__ import annotations

from pathlib import Path

from .setup_b_cost_aware import (
    EXPECTED_HIGH_VOL_N,
    build_cost_aware_report,
    format_cost_aware_report,
    load_json,
    reconstruct_validation_high_vol_subset,
    write_cost_aware_artifacts,
)


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data" / "bitget"
OUTPUT_DIR = PACKAGE_DIR / "output" / "bitget"
VALIDATION_JSON = OUTPUT_DIR / "setup_b_high_vol_validation.json"
TEXT_OUTPUT = OUTPUT_DIR / "setup_b_cost_aware_report.txt"
JSON_OUTPUT = OUTPUT_DIR / "setup_b_cost_aware_report.json"


def run_cost_aware_report() -> dict[str, object]:
    """Reconstruct B5 high-vol subset and write B6 cost-aware artifacts."""

    observations, reconstruction = reconstruct_validation_high_vol_subset(DATA_DIR)
    if reconstruction["reconstructed_n"] != EXPECTED_HIGH_VOL_N:
        raise SystemExit(
            "B6 reconstruction mismatch: "
            f"expected {EXPECTED_HIGH_VOL_N}, got {reconstruction['reconstructed_n']}"
        )

    validation_artifact = load_json(VALIDATION_JSON)
    report = build_cost_aware_report(
        high_vol_observations=observations,
        validation_artifact=validation_artifact,
    )
    report["reconstruction"] = {
        **report["reconstruction"],  # type: ignore[index]
        "all_validation_observations": reconstruction["all_validation_observations"],
        "atr_threshold_info": reconstruction["atr_threshold_info"],
    }
    write_cost_aware_artifacts(report, text_path=TEXT_OUTPUT, json_path=JSON_OUTPUT)
    return report


def main() -> int:
    report = run_cost_aware_report()
    print(format_cost_aware_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
