from __future__ import annotations

import json
import shutil
from pathlib import Path

from research.signal_observation.setup_b import SignalDirection, detect_setup_b
from research.signal_observation.setup_b_diagnostics import (
    diagnose_setup_b,
    format_setup_b_diagnostics_report,
    write_setup_b_artifacts,
)

from test_signal_observation_setup_b import _long_setup_candles


def test_setup_b_diagnostics_counters_are_deterministic() -> None:
    summary, observations = diagnose_setup_b(
        _long_setup_candles(),
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
    )

    assert summary.symbol == "BTCUSDT"
    assert summary.direction == "long"
    assert summary.candles_loaded == len(_long_setup_candles())
    assert summary.pivots_detected >= 4
    assert summary.trend_detected >= 1
    assert summary.valid_pullbacks >= 1
    assert summary.bos_confirmed == 1
    assert summary.entry_observations == len(observations) == 1


def test_setup_b_diagnostics_match_normal_detector_output() -> None:
    candles = _long_setup_candles()
    normal = detect_setup_b(candles, symbol="BTCUSDT", direction=SignalDirection.LONG)

    summary, observations = diagnose_setup_b(
        candles,
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
    )

    assert observations == normal
    assert summary.entry_observations == len(normal)


def test_setup_b_report_writers_are_stable() -> None:
    summary, observations = diagnose_setup_b(
        _long_setup_candles(),
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
    )
    output_dir = Path(".pytest-temp-run") / "setup_b_diagnostics_test"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    text_path = output_dir / "diagnostics.txt"
    diagnostics_json_path = output_dir / "diagnostics.json"
    observations_json_path = output_dir / "observations.json"

    write_setup_b_artifacts(
        [summary],
        observations,
        text_path=text_path,
        diagnostics_json_path=diagnostics_json_path,
        observations_json_path=observations_json_path,
    )

    assert text_path.read_text(encoding="utf-8") == format_setup_b_diagnostics_report([summary])
    diagnostics_payload = json.loads(diagnostics_json_path.read_text(encoding="utf-8"))
    observations_payload = json.loads(observations_json_path.read_text(encoding="utf-8"))
    assert diagnostics_payload[0]["symbol"] == "BTCUSDT"
    assert diagnostics_payload[0]["entry_observations"] == 1
    assert observations_payload[0]["symbol"] == "BTCUSDT"
    shutil.rmtree(output_dir)


def test_setup_b_diagnostics_modules_do_not_import_network_libraries() -> None:
    repo_root = Path(__file__).parent.parent.parent
    module_paths = [
        repo_root / "research" / "signal_observation" / "setup_b_diagnostics.py",
        repo_root / "research" / "signal_observation" / "run_setup_b_diagnostics.py",
    ]

    forbidden_tokens = (
        "urllib",
        "requests",
        "http.client",
        "socket",
        "libs.exchange",
        "execution_service",
        "risk_engine",
        "orchestrator",
        "position_manager",
        "kill_switch",
    )
    for path in module_paths:
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text
