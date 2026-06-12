from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from research.hypothesis_agent.config import build_config
from research.hypothesis_agent.main import run_adaptive, run_backtest


def make_candles(count: int, *, base_price: float = 100.0, trend: float = 0.4) -> list[dict]:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    candles: list[dict] = []
    price = base_price
    for index in range(count):
        open_price = price
        close_price = price + trend + ((index % 4) - 1.5) * 0.2
        high = max(open_price, close_price) + 0.8
        low = min(open_price, close_price) - 0.8
        price = close_price
        candles.append(
            {
                "timestamp": start + timedelta(minutes=15 * index),
                "open": round(open_price, 4),
                "high": round(high, 4),
                "low": round(low, 4),
                "close": round(close_price, 4),
                "volume": 100 + index,
                "body": abs(close_price - open_price),
                "session": "london_ny_overlap",
            }
        )
    return candles


class DummyFetcher:
    def __init__(self, candles: list[dict]) -> None:
        self.candles = candles

    def fetch_history(self, symbol: str, timeframe: str, *, days: int, limit: int | None = None) -> list[dict]:
        return self.candles


def test_run_backtest_writes_hypothesis_output(tmp_path):
    config = build_config(tmp_path)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    (config.project_root / "config").mkdir(parents=True, exist_ok=True)
    (config.project_root / "config" / "strategy.yaml").write_text("strategy:\n  setup_types:\n    - breakout_retest\n", encoding="utf-8")
    (config.project_root / "config" / "risk.yaml").write_text("risk:\n  max_open_positions: 1\n", encoding="utf-8")

    alerts: list[str] = []
    result = run_backtest(
        config,
        fetcher=DummyFetcher(make_candles(220)),
        alert_sender=lambda message, **kwargs: alerts.append(message) or True,
    )

    assert result["mode"] == "backtest"
    content = config.hypothesis_output_path.read_text(encoding="utf-8")
    assert "# Research Candidates (Stage 0)" in content
    assert "## Full Statistics Table" in content
    assert isinstance(result["hypotheses"], list)
    if result["hypotheses"]:
        assert "## Candidate 1" in content
        assert alerts
        assert all("win_rate" not in msg for msg in alerts)
        assert all("Stage 0" in msg for msg in alerts)
    else:
        assert "## Candidate 1" not in content
        assert alerts == []


def test_run_adaptive_switches_to_backtest_on_degraded_state(tmp_path):
    config = build_config(tmp_path)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    (config.project_root / "config").mkdir(parents=True, exist_ok=True)
    (config.project_root / "config" / "strategy.yaml").write_text("strategy:\n  setup_types: []\n", encoding="utf-8")
    (config.project_root / "config" / "risk.yaml").write_text("risk:\n  max_open_positions: 1\n", encoding="utf-8")
    config.state_path.write_text(
        json.dumps(
            {
                "active_hypotheses": [
                    {
                        "pattern": "momentum",
                        "symbol": "BTC-USDT",
                        "timeframe": "15m",
                        "win_rate": 60.0,
                        "current_win_rate": 40.0,
                    }
                ],
                "regime_by_market": {},
            }
        ),
        encoding="utf-8",
    )

    alerts: list[str] = []
    result = run_adaptive(
        config,
        fetcher=DummyFetcher(make_candles(220)),
        alert_sender=lambda message, **kwargs: alerts.append(message) or True,
        iterations=1,
    )

    assert result["mode"] == "backtest"
    assert any("Switching to backtest mode" in message for message in alerts)
