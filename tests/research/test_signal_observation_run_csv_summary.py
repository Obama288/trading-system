from __future__ import annotations

from pathlib import Path

import pytest

from research.signal_observation.models import BtcScore
from research.signal_observation.run_csv_summary import (
    format_summary,
    main,
    run_setup_a_csv_summary,
)
from research.signal_observation.summary import SummaryMetrics


FIXTURE_DIR = Path("tests/fixtures/signal_observation")
CONTEXT_4H = FIXTURE_DIR / "known_breakout_retest_4h.csv"
TRIGGER_1H = FIXTURE_DIR / "known_breakout_retest_1h.csv"


def _run_fixture_summary() -> SummaryMetrics:
    return run_setup_a_csv_summary(
        context_csv_4h=CONTEXT_4H,
        trigger_csv_1h=TRIGGER_1H,
        symbol="BTCUSDT",
        source_exchange="fixture",
    )


def test_run_setup_a_csv_summary_returns_summary_metrics() -> None:
    metrics = _run_fixture_summary()

    assert isinstance(metrics, SummaryMetrics)


def test_fixture_summary_has_observations_and_resolved_outcomes() -> None:
    metrics = _run_fixture_summary()

    assert metrics.observation_count >= 1
    assert metrics.resolved_count >= 1


def test_btc_score_parameter_is_accepted() -> None:
    metrics = run_setup_a_csv_summary(
        context_csv_4h=CONTEXT_4H,
        trigger_csv_1h=TRIGGER_1H,
        symbol="ETHUSDT",
        source_exchange="fixture",
        btc_score=BtcScore.BULLISH,
    )

    assert isinstance(metrics, SummaryMetrics)


def test_format_summary_includes_required_fields() -> None:
    text = format_summary(_run_fixture_summary())

    assert "observations:" in text
    assert "resolved:" in text
    assert "win_rate:" in text
    assert "expectancy_r:" in text
    assert "profit_factor:" in text


def test_cli_main_prints_formatted_summary(capsys) -> None:
    main(
        [
            "--context-4h",
            str(CONTEXT_4H),
            "--trigger-1h",
            str(TRIGGER_1H),
            "--symbol",
            "BTCUSDT",
            "--source-exchange",
            "fixture",
            "--btc-score",
            "1",
        ]
    )
    output = capsys.readouterr().out

    assert "observations:" in output
    assert "profit_factor:" in output


def test_missing_file_raises_cleanly() -> None:
    with pytest.raises(FileNotFoundError):
        run_setup_a_csv_summary(
            context_csv_4h="missing_4h.csv",
            trigger_csv_1h=TRIGGER_1H,
            symbol="BTCUSDT",
            source_exchange="fixture",
        )


def test_run_csv_summary_has_no_network_or_exchange_imports() -> None:
    text = Path("research/signal_observation/run_csv_summary.py").read_text(
        encoding="utf-8"
    )
    forbidden_tokens = (
        "requests",
        "httpx",
        "aiohttp",
        "websocket",
        "websockets",
        "ccxt",
        "socket",
        "libs.exchange",
    )

    for token in forbidden_tokens:
        assert token not in text
