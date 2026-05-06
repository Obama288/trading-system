from __future__ import annotations

from pathlib import Path

from research.signal_observation.run_fixture_summary import (
    main,
    run_fixture_setup_a_summary,
)
from research.signal_observation.summary import SummaryMetrics


def test_run_fixture_setup_a_summary_returns_summary_metrics() -> None:
    metrics = run_fixture_setup_a_summary()

    assert isinstance(metrics, SummaryMetrics)


def test_run_fixture_setup_a_summary_resolves_known_fixture() -> None:
    metrics = run_fixture_setup_a_summary()

    assert metrics.observation_count >= 1
    assert metrics.resolved_count >= 1
    assert metrics.expectancy_r is not None


def test_fixture_summary_cli_prints_concise_summary(capsys) -> None:
    main()
    output = capsys.readouterr().out

    assert "observations:" in output
    assert "resolved:" in output
    assert "wins:" in output
    assert "losses:" in output
    assert "win_rate:" in output
    assert "expectancy_r:" in output
    assert "profit_factor:" in output


def test_summary_modules_have_no_network_or_exchange_imports() -> None:
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
    for path in (
        Path("research/signal_observation/summary.py"),
        Path("research/signal_observation/run_fixture_summary.py"),
    ):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"{token} found in {path}"
