from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Protocol
from uuid import uuid4

from apps.position_manager.application.reconcile import reconcile_positions_use_case
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.position_manager.schemas.requests import ExchangePositionSnapshot, ReconcileRequest

LOGGER = logging.getLogger(__name__)


class MarketFetcher(Protocol):
    def fetch_candles(self, symbol: str, timeframe: str, *, limit: int = 2) -> list[dict]: ...


def _load_mark_price(
    *,
    market_fetcher: MarketFetcher,
    symbol: str,
    timeframe: str,
    candle_limit: int,
) -> float | None:
    candles = market_fetcher.fetch_candles(symbol=symbol, timeframe=timeframe, limit=candle_limit)
    if not candles:
        return None
    return float(candles[-1]["close"])


def build_reconcile_request(
    *,
    open_positions: list,
    market_fetcher: MarketFetcher,
    timeframe: str,
    candle_limit: int,
    correlation_id: str,
) -> ReconcileRequest:
    mark_price_by_symbol: dict[str, float | None] = {}
    snapshots: list[ExchangePositionSnapshot] = []
    for row in open_positions:
        if row.symbol not in mark_price_by_symbol:
            mark_price_by_symbol[row.symbol] = _load_mark_price(
                market_fetcher=market_fetcher,
                symbol=row.symbol,
                timeframe=timeframe,
                candle_limit=candle_limit,
            )
        snapshots.append(
            ExchangePositionSnapshot(
                position_id=row.position_id,
                execution_id=row.execution_id,
                symbol=row.symbol,
                side=row.side,
                quantity=row.quantity,
                entry_price=row.entry_price,
                mark_price=mark_price_by_symbol[row.symbol],
                opened_at=row.opened_at,
                ttl_expires_at=row.ttl_expires_at,
                status="open",
            )
        )
    return ReconcileRequest(exchange_positions=snapshots, correlation_id=correlation_id)


def run_reconcile_cycle(
    *,
    repo: PositionRepository,
    journal_client,
    alert_client,
    market_fetcher: MarketFetcher,
    timeframe: str,
    candle_limit: int,
    correlation_id: str | None = None,
) -> dict:
    open_positions = repo.list_open_positions()
    corr = correlation_id or f"corr_pos_reconcile_sched_{uuid4().hex}"
    if not open_positions:
        return {
            "ok": True,
            "code": "RECONCILED",
            "reconciled_count": 0,
            "results": [],
            "open_positions": [],
            "correlation_id": corr,
        }

    req = build_reconcile_request(
        open_positions=open_positions,
        market_fetcher=market_fetcher,
        timeframe=timeframe,
        candle_limit=candle_limit,
        correlation_id=corr,
    )
    result = reconcile_positions_use_case(
        repo=repo,
        journal_client=journal_client,
        alert_client=alert_client,
        req=req,
    )
    result["correlation_id"] = corr
    return result


async def run_reconcile_scheduler_loop(
    *,
    session_factory,
    journal_client,
    alert_client,
    market_fetcher: MarketFetcher,
    interval_seconds: float,
    timeframe: str,
    candle_limit: int,
    continue_on_error: bool = False,
    stop_event: asyncio.Event | None = None,
) -> None:
    while True:
        if stop_event is not None and stop_event.is_set():
            return

        try:
            def _run_once() -> dict:
                db = session_factory()
                try:
                    repo = PositionRepository(db)
                    return run_reconcile_cycle(
                        repo=repo,
                        journal_client=journal_client,
                        alert_client=alert_client,
                        market_fetcher=market_fetcher,
                        timeframe=timeframe,
                        candle_limit=candle_limit,
                    )
                finally:
                    db.close()

            result = await asyncio.to_thread(_run_once)
            LOGGER.info(
                "position reconcile scheduler cycle completed",
                extra={
                    "correlation_id": result.get("correlation_id"),
                    "reconciled_count": result.get("reconciled_count"),
                    "open_positions_count": len(result.get("open_positions", [])),
                },
            )
        except Exception:
            LOGGER.exception("position reconcile scheduler cycle failed")
            if not continue_on_error:
                raise

        await asyncio.sleep(interval_seconds)
