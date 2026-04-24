from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from libs.db.models.execution import ExecutionModel
from libs.db.models.position import PositionModel
from libs.db.models.trade_candidate import TradeCandidateModel
from libs.schemas.common import PositionStatus

_CANDLE_SECONDS = 900  # 15m candles


class StatsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_stats(self, mode: str = "paper") -> dict:
        rows = self._closed_trade_rows(mode=mode)
        return {
            **self._aggregate(rows),
            "by_symbol": self._group_metrics(rows, key_name="symbol"),
            "by_setup_type": self._group_metrics(rows, key_name="setup_type"),
        }

    def _closed_trade_rows(self, mode: str = "paper") -> list[dict]:
        stmt = (
            select(PositionModel, TradeCandidateModel, ExecutionModel)
            .outerjoin(TradeCandidateModel, TradeCandidateModel.candidate_id == PositionModel.candidate_id)
            .outerjoin(ExecutionModel, ExecutionModel.execution_id == PositionModel.execution_id)
            .where(
                ExecutionModel.mode == mode,
                PositionModel.status.in_(
                    [
                        PositionStatus.CLOSED.value,
                        PositionStatus.CANCELLED.value,
                        PositionStatus.EXPIRED.value,
                    ]
                ),
            )
        )
        rows = self.db.execute(stmt).all()
        return [self._to_trade_row(position, candidate, execution) for position, candidate, execution in rows]

    @staticmethod
    def _to_trade_row(
        position: PositionModel,
        candidate: TradeCandidateModel | None,
        execution: ExecutionModel | None,
    ) -> dict:
        setup_type = "unknown"
        if candidate is not None and isinstance(candidate.execution_payload_json, dict):
            setup_type = str(candidate.execution_payload_json.get("setup_type") or setup_type)
        elif execution is not None and isinstance(execution.payload, dict):
            setup_type = str(execution.payload.get("setup_type") or setup_type)

        side = str(position.side).lower()
        direction = -1.0 if side in {"short", "sell"} else 1.0
        close_price = position.close_price if position.close_price is not None else position.entry_price
        pnl = round((close_price - position.entry_price) * position.quantity * direction, 4)

        rr = 0.0
        if position.stop_loss is not None:
            risk_per_unit = abs(position.entry_price - position.stop_loss)
            if risk_per_unit > 0:
                rr = round(((close_price - position.entry_price) * direction) / risk_per_unit, 4)

        return {
            "symbol": position.symbol,
            "setup_type": setup_type,
            "pnl": pnl,
            "rr": rr,
            "has_valid_rr": position.stop_loss is not None and abs(position.entry_price - position.stop_loss) > 0,
            "opened_at": position.opened_at,
            "closed_at": position.closed_at,
        }

    def _group_metrics(self, rows: list[dict], *, key_name: str) -> dict[str, dict]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            grouped[str(row[key_name])].append(row)
        return {key: self._aggregate(items) for key, items in grouped.items()}

    @staticmethod
    def _aggregate(rows: list[dict]) -> dict:
        total_trades = len(rows)
        if total_trades == 0:
            return {
                "total_trades": 0,
                "win_rate_pct": 0.0,
                "avg_rr": 0.0,
                "total_pnl_usdt": 0.0,
                "avg_hold_candles": 0.0,
            }

        wins = sum(1 for row in rows if row["pnl"] > 0)
        rr_values = [row["rr"] for row in rows if row["has_valid_rr"]]
        total_pnl = round(sum(row["pnl"] for row in rows), 4)
        avg_rr = round(sum(rr_values) / len(rr_values), 4) if rr_values else 0.0

        hold_seconds = [
            (row["closed_at"] - row["opened_at"]).total_seconds()
            for row in rows
            if row["closed_at"] is not None and row["opened_at"] is not None
        ]
        avg_hold_candles = (
            round(sum(hold_seconds) / len(hold_seconds) / _CANDLE_SECONDS, 2) if hold_seconds else 0.0
        )

        return {
            "total_trades": total_trades,
            "win_rate_pct": round((wins / total_trades) * 100.0, 2),
            "avg_rr": avg_rr,
            "total_pnl_usdt": total_pnl,
            "avg_hold_candles": avg_hold_candles,
        }
