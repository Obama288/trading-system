from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from research.signal_observation.models import (
    BtcScore,
    Direction,
    ObservationStatus,
    SetupId,
    SignalObservation,
)


def _sample_observation(**overrides: object) -> SignalObservation:
    payload: dict[str, object] = {
        "observation_id": "obs-001",
        "created_at_utc": datetime(2026, 5, 6, 12, 0, tzinfo=timezone.utc),
        "source_exchange": "public-feed",
        "symbol": "BTCUSDT",
        "setup_id": SetupId.A,
        "direction": Direction.LONG,
        "context_timeframe": "4H",
        "trigger_timeframe": "1H",
        "signal_time": datetime(2026, 5, 6, 12, 0, tzinfo=timezone.utc),
        "entry_time_theoretical": datetime(
            2026, 5, 6, 13, 0, tzinfo=timezone.utc
        ),
        "entry_price_theoretical": Decimal("100.50"),
        "stop_price_theoretical": Decimal("99.50"),
        "target_price_theoretical": Decimal("102.50"),
        "initial_r": Decimal("1.00"),
        "btc_score": BtcScore.BULLISH_NEAR_RESISTANCE,
        "session_utc_hour": 12,
        "session_label": "Europe",
        "status": ObservationStatus.CANDIDATE,
        "outcome_window_candles": 24,
        "mfe_r": Decimal("1.25"),
        "mae_r": Decimal("-0.40"),
        "final_r": Decimal("0.75"),
        "hit_target_before_stop": False,
        "hit_stop_before_target": False,
        "resolution_reason": "window_close",
    }
    payload.update(overrides)
    return SignalObservation(**payload)


def test_models_accept_decimal_price_and_r_values() -> None:
    observation = _sample_observation()

    assert isinstance(observation.entry_price_theoretical, Decimal)
    assert isinstance(observation.stop_price_theoretical, Decimal)
    assert isinstance(observation.target_price_theoretical, Decimal)
    assert isinstance(observation.initial_r, Decimal)
    assert isinstance(observation.outcome.mfe_r, Decimal)
    assert isinstance(observation.outcome.mae_r, Decimal)
    assert isinstance(observation.outcome.final_r, Decimal)


def test_invalid_setup_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="setup_id"):
        _sample_observation(setup_id="C")


def test_invalid_direction_is_rejected() -> None:
    with pytest.raises(ValueError, match="direction"):
        _sample_observation(direction="up")


def test_invalid_status_is_rejected() -> None:
    with pytest.raises(ValueError, match="status"):
        _sample_observation(status="done")


def test_btc_score_is_limited_to_minus2_through_plus2() -> None:
    assert _sample_observation(btc_score=-2).btc_score is BtcScore.BEARISH_BREAKDOWN
    assert _sample_observation(btc_score=2).btc_score is BtcScore.BULLISH

    with pytest.raises(ValueError, match="btc_score"):
        _sample_observation(btc_score=3)


def test_models_do_not_require_balance_or_position_size_fields() -> None:
    field_names = {field.name for field in fields(SignalObservation)}

    assert "account_balance" not in field_names
    assert "balance" not in field_names
    assert "position_size" not in field_names
    assert "size_usd" not in field_names


def test_research_package_has_no_network_or_exchange_imports() -> None:
    package_dir = Path("research/signal_observation")
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

    for path in package_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"{token} found in {path}"
