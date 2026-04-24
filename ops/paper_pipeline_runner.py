from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any, Protocol
from uuid import uuid4

import httpx
from pydantic import BaseModel

from apps.market_data.domain.freshness import is_stale
from apps.market_data.domain.snapshot_builder import build_market_snapshot
from apps.review_gateway.application.review_candidate import review_candidate_use_case
from apps.risk_engine.application.evaluate_risk import evaluate_risk_use_case
from apps.risk_engine.main import AccountState, RiskRequest
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.signal_engine.application.evaluate_signal import evaluate_signal_use_case
from apps.orchestrator.schemas.pipeline_requests import EvaluatePipelineRequest
from libs.clients.kill_switch_client import HttpKillSwitchClient, KillSwitchClient, KillSwitchError
from libs.config.settings import load_all_configs
from libs.db.session import get_session_factory
from libs.schemas.common import RiskDecision, SignalStatus
from libs.clients.okx_market_data_fetcher import OkxMarketDataFetcher


class EvaluateClient(Protocol):
    async def evaluate(self, payload: EvaluatePipelineRequest) -> dict: ...


class OrchestratorEvaluateClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = os.getenv("INTERNAL_SERVICE_TOKEN")
        if not self._token:
            raise RuntimeError(
                "INTERNAL_SERVICE_TOKEN environment variable is not set. "
                "OrchestratorEvaluateClient requires INTERNAL_SERVICE_TOKEN to call /v1/pipeline/evaluate."
            )

    async def evaluate(self, payload: EvaluatePipelineRequest) -> dict:
        headers = {"X-Internal-Token": self._token}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/pipeline/evaluate",
                json=payload.model_dump(mode="json"),
                headers=headers,
            )
            response.raise_for_status()
            return response.json()


class PipelineAccountState(BaseModel):
    equity_usdt: float
    daily_pnl_usdt: float
    portfolio_exposure_pct: float
    open_positions: int


def _strategy_config() -> dict[str, Any]:
    return load_all_configs().get("strategy", {}).get("strategy", {})


def parse_args() -> argparse.Namespace:
    strategy_cfg = _strategy_config()
    default_symbols = strategy_cfg.get(
        "symbols",
        ["BTC-USDT", "ETH-USDT", "BNB-USDT", "SOL-USDT", "AVAX-USDT", "LINK-USDT"],
    )
    default_timeframe = strategy_cfg.get("default_timeframe", "15m")
    parser = argparse.ArgumentParser(description="Minimal live-market paper pipeline runner.")
    parser.add_argument("--symbols", nargs="+", default=default_symbols)
    parser.add_argument("--timeframes", nargs="+", default=[default_timeframe])
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--equity-usdt", type=float, default=1000.0)
    parser.add_argument("--daily-pnl-usdt", type=float, default=0.0)
    parser.add_argument("--portfolio-exposure-pct", type=float, default=0.0)
    parser.add_argument("--interval-seconds", type=float, default=300.0)
    parser.add_argument("--orchestrator-base-url", default=os.getenv("ORCHESTRATOR_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--kill-switch-base-url", default=os.getenv("KILL_SWITCH_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--once", action="store_true")
    return parser.parse_args()


def _stale_threshold_seconds() -> int:
    configs = load_all_configs()
    return int(configs["risk"].get("market_data", {}).get("stale_snapshot_threshold_seconds", 30))


def _stale_threshold_seconds_for_timeframe(timeframe: str) -> int:
    discovery_thresholds = {
        "1m": 120,
        "5m": 420,
        "15m": 1020,
    }
    return discovery_thresholds.get(timeframe, _stale_threshold_seconds())


def _build_snapshot_from_candles(symbol: str, timeframe: str, candles: list[dict]):
    opens = [float(item["open"]) for item in candles]
    closes = [float(item["close"]) for item in candles]
    highs = [float(item["high"]) for item in candles]
    lows = [float(item["low"]) for item in candles]
    last_price = closes[-1]
    snapshot = build_market_snapshot(
        symbol=symbol,
        timeframe=timeframe,
        last_price=last_price,
        bid=last_price,
        ask=last_price,
        opens=opens,
        closes=closes,
        highs=highs,
        lows=lows,
        session=str(candles[-1].get("session") or "unknown"),
    )
    return snapshot.model_copy(update={"timestamp": candles[-1]["timestamp"]})


def _load_account_state(*, equity_usdt: float, daily_pnl_usdt: float, portfolio_exposure_pct: float) -> PipelineAccountState:
    session_factory = get_session_factory()
    with session_factory() as db:
        repo = PositionRepository(db)
        open_positions = len(repo.list_open_positions())
    return PipelineAccountState(
        equity_usdt=equity_usdt,
        daily_pnl_usdt=daily_pnl_usdt,
        portfolio_exposure_pct=portfolio_exposure_pct,
        open_positions=open_positions,
    )


async def run_cycle(
    *,
    symbol: str,
    timeframe: str,
    candle_limit: int,
    kill_switch_client: KillSwitchClient,
    market_fetcher,
    evaluate_client: EvaluateClient,
    account_state: PipelineAccountState,
    signal_evaluator=evaluate_signal_use_case,
    risk_evaluator=evaluate_risk_use_case,
    review_evaluator=review_candidate_use_case,
) -> dict[str, Any]:
    correlation_id = f"corr_paper_pipeline_{uuid4().hex}"
    try:
        kill_switch_status = await kill_switch_client.get_status(correlation_id=correlation_id)
    except KillSwitchError:
        return {
            "candidate_created": False,
            "symbol": symbol,
            "timeframe": timeframe,
            "correlation_id": correlation_id,
            "reason": "kill_switch_error",
        }
    if kill_switch_status.get("data", {}).get("kill_switch_active") is True:
        return {
            "candidate_created": False,
            "symbol": symbol,
            "timeframe": timeframe,
            "correlation_id": correlation_id,
            "reason": "kill_switch_active",
        }

    candles = market_fetcher.fetch_candles(symbol=symbol, timeframe=timeframe, limit=candle_limit)
    if len(candles) < 50:
        return {
            "candidate_created": False,
            "symbol": symbol,
            "timeframe": timeframe,
            "correlation_id": correlation_id,
            "reason": "insufficient_candles",
        }

    snapshot = _build_snapshot_from_candles(symbol=symbol, timeframe=timeframe, candles=candles)
    stale_threshold_seconds = _stale_threshold_seconds_for_timeframe(timeframe)
    if is_stale(snapshot.timestamp, threshold_seconds=stale_threshold_seconds):
        return {
            "candidate_created": False,
            "symbol": symbol,
            "timeframe": timeframe,
            "correlation_id": correlation_id,
            "reason": "stale_snapshot",
        }

    signal = signal_evaluator(snapshot)
    if signal.status != SignalStatus.CANDIDATE:
        return {
            "candidate_created": False,
            "symbol": symbol,
            "timeframe": timeframe,
            "correlation_id": correlation_id,
            "reason": "no_signal_candidate",
        }

    risk_request = RiskRequest(
        signal_id=signal.signal_id,
        symbol=signal.symbol,
        side=signal.side,
        confidence=signal.confidence,
        entry_zone=signal.entry_zone,
        stop_loss=signal.stop_loss,
        account_state=AccountState(
            equity_usdt=account_state.equity_usdt,
            daily_pnl_usdt=account_state.daily_pnl_usdt,
            open_positions=account_state.open_positions,
            portfolio_exposure_pct=account_state.portfolio_exposure_pct,
        ),
        correlation_id=correlation_id,
    )
    risk_payload = risk_evaluator(risk_request)
    risk = RiskDecision(
        risk_id=f"risk_{signal.signal_id}",
        signal_id=signal.signal_id,
        symbol=signal.symbol,
        **risk_payload,
    )
    if not risk.approved:
        return {
            "candidate_created": False,
            "symbol": symbol,
            "timeframe": timeframe,
            "correlation_id": correlation_id,
            "reason": "risk_rejected",
        }

    review = review_evaluator(signal, risk, snapshot, stale_threshold_seconds=stale_threshold_seconds)
    if not review.passed:
        return {
            "candidate_created": False,
            "symbol": symbol,
            "timeframe": timeframe,
            "correlation_id": correlation_id,
            "reason": "review_rejected",
        }

    response = await evaluate_client.evaluate(
        EvaluatePipelineRequest(
            signal=signal,
            risk=risk,
            review=review,
            correlation_id=correlation_id,
        )
    )
    return {
        "candidate_created": bool(response.get("ok")),
        "symbol": symbol,
        "timeframe": timeframe,
        "correlation_id": correlation_id,
        "reason": None if response.get("ok") else "orchestrator_rejected",
        "result": response,
    }


async def run_loop(
    *,
    symbols: list[str],
    timeframes: list[str],
    candle_limit: int,
    equity_usdt: float,
    daily_pnl_usdt: float,
    portfolio_exposure_pct: float,
    interval_seconds: float,
    once: bool,
    orchestrator_base_url: str,
    kill_switch_base_url: str,
) -> None:
    kill_switch_client = HttpKillSwitchClient(base_url=kill_switch_base_url)
    market_fetcher = OkxMarketDataFetcher()
    evaluate_client = OrchestratorEvaluateClient(orchestrator_base_url)

    while True:
        account_state = _load_account_state(
            equity_usdt=equity_usdt,
            daily_pnl_usdt=daily_pnl_usdt,
            portfolio_exposure_pct=portfolio_exposure_pct,
        )
        for timeframe in timeframes:
            for symbol in symbols:
                result = await run_cycle(
                    symbol=symbol,
                    timeframe=timeframe,
                    candle_limit=candle_limit,
                    kill_switch_client=kill_switch_client,
                    market_fetcher=market_fetcher,
                    evaluate_client=evaluate_client,
                    account_state=account_state,
                )
                print(json.dumps(result, ensure_ascii=False), flush=True)
        if once:
            return
        await asyncio.sleep(interval_seconds)


def main() -> None:
    args = parse_args()
    asyncio.run(
        run_loop(
            symbols=args.symbols,
            timeframes=args.timeframes,
            candle_limit=args.limit,
            equity_usdt=args.equity_usdt,
            daily_pnl_usdt=args.daily_pnl_usdt,
            portfolio_exposure_pct=args.portfolio_exposure_pct,
            interval_seconds=args.interval_seconds,
            once=args.once,
            orchestrator_base_url=args.orchestrator_base_url,
            kill_switch_base_url=args.kill_switch_base_url,
        )
    )


if __name__ == "__main__":
    main()
