"""Run the local Setup B random-entry baseline."""

from __future__ import annotations

from pathlib import Path

from research.signal_observation.setup_b_random_baseline import (
    DEFAULT_ITERATIONS,
    DEFAULT_SEED,
    format_random_baseline_report,
    load_bitget_4h_candles,
    load_json,
    run_random_baseline_iterations,
    write_random_baseline_artifacts,
)


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data" / "bitget"
OUTPUT_DIR = PACKAGE_DIR / "output" / "bitget"
OBSERVATIONS_PATH = OUTPUT_DIR / "setup_b_observations.json"
SETUP_B_METRICS_PATH = OUTPUT_DIR / "setup_b_metrics_analysis.json"
TEXT_OUTPUT_PATH = OUTPUT_DIR / "setup_b_random_baseline.txt"
JSON_OUTPUT_PATH = OUTPUT_DIR / "setup_b_random_baseline.json"


def run_setup_b_random_baseline(
    *,
    iterations: int = DEFAULT_ITERATIONS,
    seed: int = DEFAULT_SEED,
) -> dict[str, object]:
    """Run the deterministic local random baseline and write artifacts."""

    observations = load_json(OBSERVATIONS_PATH)
    if not isinstance(observations, list):
        raise ValueError("Setup B observations artifact must contain a list")
    setup_b_metrics = load_json(SETUP_B_METRICS_PATH)
    if not isinstance(setup_b_metrics, dict):
        raise ValueError("Setup B metrics artifact must contain an object")

    analysis = run_random_baseline_iterations(
        observations=observations,
        candles_by_symbol=load_bitget_4h_candles(DATA_DIR),
        setup_b_metrics=setup_b_metrics,
        iterations=iterations,
        seed=seed,
    )
    write_random_baseline_artifacts(
        analysis,
        text_path=TEXT_OUTPUT_PATH,
        json_path=JSON_OUTPUT_PATH,
    )
    return analysis


def main() -> int:
    """CLI entrypoint."""

    analysis = run_setup_b_random_baseline()
    print(format_random_baseline_report(analysis), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
