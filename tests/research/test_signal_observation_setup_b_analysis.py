from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

from research.signal_observation.run_setup_b_analysis import run_setup_b_analysis
from research.signal_observation.setup_b_analysis import (
    analyze_setup_b_observations,
    format_analysis_report,
    summarize_best_worst_pairs,
    write_analysis_artifacts,
)


def _observation(
    *,
    symbol: str,
    direction: str,
    signal_time: str,
    hour: int,
    outcome_1r: str,
    outcome_1_5r: str | None = None,
    outcome_2r: str | None = None,
    mae: str = "-0.25",
    mfe: str = "1.25",
    bars: int = 3,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "signal_direction": direction,
        "signal_time": signal_time,
        "signal_hour_utc": hour,
        "outcome_1r": outcome_1r,
        "outcome_1_5r": outcome_1_5r or outcome_1r,
        "outcome_2r": outcome_2r or outcome_1r,
        "mae_1r": mae,
        "mfe_1r": mfe,
        "bars_to_resolution_1r": bars,
        "mae_1_5r": mae,
        "mfe_1_5r": mfe,
        "bars_to_resolution_1_5r": bars,
        "mae_2r": mae,
        "mfe_2r": mfe,
        "bars_to_resolution_2r": bars,
    }


def _sample_observations() -> list[dict[str, object]]:
    return [
        _observation(
            symbol="BTCUSDT",
            direction="long",
            signal_time="2026-01-01T00:00:00+00:00",
            hour=0,
            outcome_1r="loss",
            mae="-1.00",
            mfe="0.20",
            bars=2,
        ),
        _observation(
            symbol="BTCUSDT",
            direction="long",
            signal_time="2026-01-02T00:00:00+00:00",
            hour=4,
            outcome_1r="flat",
            mae="-0.20",
            mfe="0.60",
            bars=10,
        ),
        _observation(
            symbol="ETHUSDT",
            direction="short",
            signal_time="2026-01-03T00:00:00+00:00",
            hour=8,
            outcome_1r="win",
            mae="-0.10",
            mfe="1.10",
            bars=4,
        ),
        _observation(
            symbol="ETHUSDT",
            direction="short",
            signal_time="2026-01-04T00:00:00+00:00",
            hour=12,
            outcome_1r="win",
            outcome_1_5r="win",
            outcome_2r="flat",
            mae="-0.30",
            mfe="2.20",
            bars=5,
        ),
    ]


def test_counts_expectancy_profit_factor_and_flat_rate() -> None:
    analysis = analyze_setup_b_observations(_sample_observations())

    metrics = analysis["overall"]["all"]["1r"]
    assert metrics["observations"] == 4
    assert metrics["wins"] == 2
    assert metrics["losses"] == 1
    assert metrics["flats"] == 1
    assert metrics["win_rate"] == "0.5"
    assert metrics["loss_rate"] == "0.25"
    assert metrics["flat_rate"] == "0.25"
    assert metrics["expectancy_r"] == "0.25"
    assert metrics["profit_factor"] == "2"


def test_zero_loss_and_zero_win_profit_factor_return_none() -> None:
    analysis = analyze_setup_b_observations(_sample_observations())

    eth_short = analysis["by_symbol_direction"]["ETHUSDT / short"]["1r"]
    btc_long = analysis["by_symbol_direction"]["BTCUSDT / long"]["1r"]
    assert eth_short["profit_factor"] is None
    assert btc_long["profit_factor"] is None


def test_grouping_by_symbol_direction_and_pair_ranking() -> None:
    analysis = analyze_setup_b_observations(_sample_observations())

    assert set(analysis["by_symbol"]) == {"BTCUSDT", "ETHUSDT"}
    assert set(analysis["by_direction"]) == {"long", "short"}
    assert set(analysis["by_symbol_direction"]) == {
        "BTCUSDT / long",
        "ETHUSDT / short",
    }
    assert summarize_best_worst_pairs(analysis, "1r") == (
        "ETHUSDT / short",
        "BTCUSDT / long",
    )


def test_mae_mfe_and_bars_average_and_median() -> None:
    analysis = analyze_setup_b_observations(_sample_observations())
    metrics = analysis["overall"]["all"]["1r"]

    assert metrics["avg_mae_r"] == "-0.40"
    assert metrics["median_mae_r"] == "-0.25"
    assert metrics["avg_mfe_r"] == "1.025"
    assert metrics["median_mfe_r"] == "0.85"
    assert metrics["avg_bars_to_resolution"] == "5.25"
    assert metrics["median_bars_to_resolution"] == "4.5"


def test_report_structure_and_warning_flags() -> None:
    analysis = analyze_setup_b_observations(_sample_observations())

    assert analysis["schema"] == "setup_b_metrics_analysis_v1"
    assert "distribution_diagnostics" in analysis
    assert "timing_diagnostics" in analysis
    assert "BTCUSDT / long subgroup below 10 observations; unreliable" in analysis["warning_flags"]
    assert "overall sample size below 30" in analysis["warning_flags"]

    output_dir = Path(".pytest-temp-run") / "setup_b_analysis_test"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    text_path = output_dir / "analysis.txt"
    json_path = output_dir / "analysis.json"
    write_analysis_artifacts(analysis, text_path=text_path, json_path=json_path)
    assert "Overall by target" in text_path.read_text(encoding="utf-8")
    assert json.loads(json_path.read_text(encoding="utf-8"))["schema"] == (
        "setup_b_metrics_analysis_v1"
    )
    assert "Warning flags" in format_analysis_report(analysis)
    shutil.rmtree(output_dir)


def test_empty_observations_do_not_crash() -> None:
    analysis = analyze_setup_b_observations([])

    metrics = analysis["overall"]["all"]["1r"]
    assert metrics["observations"] == 0
    assert metrics["expectancy_r"] is None
    assert metrics["profit_factor"] is None
    assert analysis["warning_flags"] == ["overall sample size below 30"]


def test_runner_generates_real_bitget_analysis_artifacts() -> None:
    analysis = run_setup_b_analysis()

    assert analysis["observation_count"] == 68
    assert analysis["overall"]["all"]["1r"]["wins"] == 18
    assert analysis["overall"]["all"]["1r"]["losses"] == 18
    assert analysis["overall"]["all"]["1r"]["flats"] == 32


def test_no_http_network_imports() -> None:
    root = Path(__file__).parent.parent.parent
    paths = [
        root / "research" / "signal_observation" / "setup_b_analysis.py",
        root / "research" / "signal_observation" / "run_setup_b_analysis.py",
    ]
    forbidden_imports = {"urllib", "requests", "http.client", "socket"}

    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        assert not forbidden_imports.intersection(imported_modules)
