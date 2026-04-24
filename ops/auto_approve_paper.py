from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from libs.db.session import get_session_factory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Temporary controlled auto-approve loop for paper trading.")
    parser.add_argument("--interval-seconds", type=float, default=2.0)
    parser.add_argument("--operator-user-id", type=int, default=9001)
    parser.add_argument("--orchestrator-base-url", default=os.getenv("ORCHESTRATOR_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--once", action="store_true")
    return parser.parse_args()


def _candidate_to_log_row(candidate, correlation_id: str, result: dict) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_id": candidate.candidate_id,
        "correlation_id": correlation_id,
        "status": candidate.status,
        "symbol": candidate.symbol,
        "side": candidate.side,
        "result": result,
    }


def run_loop(*, interval_seconds: float, operator_user_id: int, orchestrator_base_url: str, once: bool) -> None:
    from libs.db.models.trade_candidate import TradeCandidateModel

    session_factory = get_session_factory()
    base_url = orchestrator_base_url.rstrip("/")
    operator_token = os.getenv("OPERATOR_TOKEN")

    while True:
        with session_factory() as db:
            candidates = (
                db.query(TradeCandidateModel)
                .filter(TradeCandidateModel.status == "pending")
                .order_by(TradeCandidateModel.created_at.asc())
                .all()
            )

            filtered = []
            now = datetime.now(timezone.utc)
            for candidate in candidates:
                if candidate.ttl_expires_at is None:
                    continue
                ttl = candidate.ttl_expires_at
                if ttl.tzinfo is None:
                    ttl = ttl.replace(tzinfo=timezone.utc)
                if ttl <= now:
                    continue
                if not candidate.execution_payload_json:
                    continue
                filtered.append(candidate)

            for candidate in filtered:
                correlation_id = f"corr_auto_approve_{uuid4().hex}"
                payload = {
                    "candidate_id": candidate.candidate_id,
                    "telegram_user_id": operator_user_id,
                    "correlation_id": correlation_id,
                }
                headers = {}
                if operator_token:
                    headers["X-Operator-Token"] = operator_token
                try:
                    response = httpx.post(f"{base_url}/v1/pipeline/approve", json=payload, headers=headers, timeout=10.0)
                    result = {
                        "http_status": response.status_code,
                        "body": response.json(),
                    }
                except Exception as exc:
                    result = {
                        "http_status": None,
                        "error": str(exc),
                    }
                print(json.dumps(_candidate_to_log_row(candidate, correlation_id, result), ensure_ascii=False), flush=True)

        if once:
            return
        time.sleep(interval_seconds)


def main() -> None:
    args = parse_args()
    run_loop(
        interval_seconds=args.interval_seconds,
        operator_user_id=args.operator_user_id,
        orchestrator_base_url=args.orchestrator_base_url,
        once=args.once,
    )


if __name__ == "__main__":
    main()
