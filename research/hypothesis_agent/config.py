from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from libs.config.settings import load_yaml


def _read_env_value(name: str, env_path: Path) -> str | None:
    direct = os.getenv(name)
    if direct:
        return direct
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip()
    return None


@dataclass(frozen=True)
class AgentConfig:
    project_root: Path
    symbols: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "SOL-USDT")
    timeframes: tuple[str, ...] = ("15m", "1H")
    history_days: int = 180
    live_poll_seconds: int = 900
    degradation_win_rate_threshold: float = 45.0
    regime_symbol: str = "BTC-USDT"
    regime_timeframe: str = "15m"
    trending_slope_threshold: float = 0.0008
    hypothesis_count: int = 3
    okx_base_url: str = "https://www.okx.com"

    @property
    def env_path(self) -> Path:
        return self.project_root / ".env"

    @property
    def strategy_config_path(self) -> Path:
        return self.project_root / "config" / "strategy.yaml"

    @property
    def risk_config_path(self) -> Path:
        return self.project_root / "config" / "risk.yaml"

    @property
    def output_dir(self) -> Path:
        return self.project_root / "research" / "hypothesis_agent" / "output"

    @property
    def hypothesis_output_path(self) -> Path:
        return self.output_dir / "HYPOTHESIS.md"

    @property
    def state_path(self) -> Path:
        return self.output_dir / "active_hypotheses.json"

    @property
    def telegram_bot_token(self) -> str | None:
        return _read_env_value("TELEGRAM_BOT_TOKEN", self.env_path)

    @property
    def telegram_chat_id(self) -> str | None:
        return _read_env_value("TELEGRAM_CHAT_ID", self.env_path)

    @property
    def strategy_config(self) -> dict[str, Any]:
        return load_yaml(self.strategy_config_path)

    @property
    def risk_config(self) -> dict[str, Any]:
        return load_yaml(self.risk_config_path)


def build_config(project_root: str | Path | None = None) -> AgentConfig:
    root = Path(project_root or Path.cwd()).resolve()
    return AgentConfig(project_root=root)
