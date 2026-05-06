"""Generate Setup B metrics analysis artifacts from local JSON output."""

from __future__ import annotations

from pathlib import Path

from research.signal_observation.setup_b_analysis import (
    analyze_setup_b_observations,
    format_analysis_report,
    load_observations,
    write_analysis_artifacts,
)


PACKAGE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PACKAGE_DIR / "output" / "bitget"
OBSERVATIONS_PATH = OUTPUT_DIR / "setup_b_observations.json"
TEXT_OUTPUT_PATH = OUTPUT_DIR / "setup_b_metrics_analysis.txt"
JSON_OUTPUT_PATH = OUTPUT_DIR / "setup_b_metrics_analysis.json"


def run_setup_b_analysis() -> dict[str, object]:
    """Analyze existing local Setup B observation artifacts."""

    observations = load_observations(OBSERVATIONS_PATH)
    analysis = analyze_setup_b_observations(observations)
    write_analysis_artifacts(
        analysis,
        text_path=TEXT_OUTPUT_PATH,
        json_path=JSON_OUTPUT_PATH,
    )
    return analysis


def main() -> int:
    """CLI entrypoint for deterministic local analysis."""

    analysis = run_setup_b_analysis()
    print(format_analysis_report(analysis), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
