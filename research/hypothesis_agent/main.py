from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from research.hypothesis_agent.alerts.telegram import send_research_alert
from research.hypothesis_agent.analysis.market_regime import detect_market_regime
from research.hypothesis_agent.analysis.patterns import PATTERN_NAMES, analyze_patterns
from research.hypothesis_agent.analysis.statistics import summarize_trades
from research.hypothesis_agent.config import AgentConfig, build_config
from research.hypothesis_agent.data.fetcher import OkxMarketDataFetcher
from research.hypothesis_agent.hypothesis.generator import generate_top_hypotheses
from research.hypothesis_agent.scheduler.adaptive import decide_mode

BACKTEST_TIMEOUT_SECONDS = 60


def _direction_from_trades(trades: list[dict]) -> str:
    directions = {trade["direction"] for trade in trades}
    if directions == {"LONG"}:
        return "LONG"
    if directions == {"SHORT"}:
        return "SHORT"
    return "BOTH"


def _check_deadline(deadline: float | None) -> None:
    if deadline is not None and time.monotonic() > deadline:
        raise TimeoutError(f"backtest timed out after {BACKTEST_TIMEOUT_SECONDS} seconds")


def analyze_market(
    config: AgentConfig,
    fetcher: OkxMarketDataFetcher,
    *,
    candle_limit: int | None = 100,
    deadline: float | None = None,
) -> tuple[list[dict], dict[str, str]]:
    stats_rows: list[dict] = []
    regime_by_market: dict[str, str] = {}
    for symbol in config.symbols:
        for timeframe in config.timeframes:
            _check_deadline(deadline)
            print(f"Fetching {symbol} {timeframe}...", flush=True)
            candles = fetcher.fetch_history(symbol, timeframe, days=config.history_days, limit=candle_limit)
            if len(candles) < 30:
                continue
            print(f"Analyzing {symbol}...", flush=True)
            regime = detect_market_regime(candles[-60:], slope_threshold=config.trending_slope_threshold)
            regime_by_market[f"{symbol}:{timeframe}"] = regime
            pattern_trades = analyze_patterns(candles)
            for pattern_name in PATTERN_NAMES:
                trades = pattern_trades[pattern_name]
                summary = summarize_trades(trades)
                stats_rows.append(
                    {
                        "pattern": pattern_name,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "direction": _direction_from_trades(trades),
                        **summary,
                    }
                )
    return stats_rows, regime_by_market


def _aggregate_regime(regime_by_market: dict[str, str]) -> str:
    if not regime_by_market:
        return "quiet"
    priority = {"volatile": 4, "trending": 3, "ranging": 2, "quiet": 1}
    return max(regime_by_market.values(), key=lambda item: priority[item])


def _load_state(config: AgentConfig) -> dict:
    if not config.state_path.exists():
        return {"active_hypotheses": [], "regime_by_market": {}}
    return json.loads(config.state_path.read_text(encoding="utf-8"))


def _save_state(config: AgentConfig, *, active_hypotheses: list[dict], regime_by_market: dict[str, str]) -> None:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.state_path.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "active_hypotheses": active_hypotheses,
                "regime_by_market": regime_by_market,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _render_markdown(
    config: AgentConfig,
    *,
    mode: str,
    market_regime: str,
    hypotheses: list[dict],
    stats_rows: list[dict],
) -> str:
    strategy_config = config.strategy_config.get("strategy", {})
    risk_config = config.risk_config.get("risk", {})
    recommended_setups = sorted({item["pattern"] for item in hypotheses})
    recommended_symbols = sorted({item["symbol"].replace("-", "") for item in hypotheses})

    lines = [
        "# Trading Hypotheses",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Mode: {mode}",
        f"Market regime: {market_regime}",
        f"Symbols: {', '.join(config.symbols)}",
        "",
    ]

    for index, hypothesis in enumerate(hypotheses, start=1):
        lines.extend(
            [
                f"## Hypothesis {index} — {hypothesis['pattern']} on {hypothesis['symbol']} {hypothesis['timeframe']}",
                f"- Statement: {hypothesis['statement']}",
                f"- Direction: {hypothesis['direction']}",
                f"- Timeframe: {hypothesis['timeframe']}",
                f"- Best session: {hypothesis['best_session']}",
                f"- Win rate: {hypothesis['win_rate']}%",
                f"- Avg R:R: {hypothesis['avg_rr']}",
                f"- Sample count: {hypothesis['sample_count']}",
                f"- Confidence: {hypothesis['confidence']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Full Statistics Table",
            "| Pattern | Symbol | Timeframe | Direction | Best session | Win rate | Avg R:R | Avg duration | Sample count | Confidence | Sharpe |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in sorted(stats_rows, key=lambda item: (item["pattern"], item["symbol"], item["timeframe"])):
        lines.append(
            f"| {row['pattern']} | {row['symbol']} | {row['timeframe']} | {row['direction']} | "
            f"{row['best_session']} | {row['win_rate']}% | {row['avg_rr']} | {row['avg_duration_candles']} | "
            f"{row['sample_count']} | {row['confidence']} | {row['sharpe']} |"
        )

    lines.extend(
        [
            "",
            "## Integration Notes",
            f"- Recommended setup_types for config/strategy.yaml: {recommended_setups}",
            f"- Recommended symbols to add to config/strategy.yaml: {recommended_symbols}",
            "- Suggested risk.yaml adjustments:",
            "```yaml",
            "risk:",
            f"  max_risk_per_trade_pct: {risk_config.get('max_risk_per_trade_pct', 0.5)}",
            f"  max_daily_loss_pct: {risk_config.get('max_daily_loss_pct', 2.0)}",
            f"  max_open_positions: {max(risk_config.get('max_open_positions', 1), len(recommended_symbols))}",
            "```",
            "",
            "## Integration with main project",
            "- Read TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from existing .env",
            f"- Existing setup_types in config/strategy.yaml: {strategy_config.get('setup_types', [])}",
            f"- Existing risk params in config/risk.yaml: {risk_config}",
            "- Use same session names as libs/schemas/common.py MarketSnapshot",
            "- Use same prefix conventions as existing alerts_service",
        ]
    )
    return "\n".join(lines) + "\n"


def write_hypothesis_output(
    config: AgentConfig,
    *,
    mode: str,
    market_regime: str,
    hypotheses: list[dict],
    stats_rows: list[dict],
) -> None:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.hypothesis_output_path.write_text(
        _render_markdown(
            config,
            mode=mode,
            market_regime=market_regime,
            hypotheses=hypotheses,
            stats_rows=stats_rows,
        ),
        encoding="utf-8",
    )


def run_backtest(
    config: AgentConfig,
    *,
    fetcher: OkxMarketDataFetcher | None = None,
    alert_sender=send_research_alert,
    candle_limit: int | None = 100,
) -> dict:
    fetcher = fetcher or OkxMarketDataFetcher(base_url=config.okx_base_url)
    deadline = time.monotonic() + BACKTEST_TIMEOUT_SECONDS
    stats_rows, regime_by_market = analyze_market(
        config,
        fetcher,
        candle_limit=candle_limit,
        deadline=deadline,
    )
    _check_deadline(deadline)
    market_regime = _aggregate_regime(regime_by_market)
    hypotheses = generate_top_hypotheses(stats_rows, limit=config.hypothesis_count)
    print("Writing HYPOTHESIS.md...", flush=True)
    write_hypothesis_output(config, mode="backtest", market_regime=market_regime, hypotheses=hypotheses, stats_rows=stats_rows)
    _save_state(config, active_hypotheses=hypotheses, regime_by_market=regime_by_market)

    for hypothesis in hypotheses:
        alert_sender(
            f"New hypothesis generated: {hypothesis['pattern']} on {hypothesis['symbol']} — "
            f"win_rate {hypothesis['win_rate']}%",
            bot_token=config.telegram_bot_token,
            chat_id=config.telegram_chat_id,
        )

    return {"mode": "backtest", "market_regime": market_regime, "hypotheses": hypotheses, "stats_rows": stats_rows}


def _current_hypothesis_metrics(stats_rows: list[dict]) -> dict[tuple[str, str, str], dict]:
    return {(row["pattern"], row["symbol"], row["timeframe"]): row for row in stats_rows}


def run_live(
    config: AgentConfig,
    *,
    fetcher: OkxMarketDataFetcher | None = None,
    alert_sender=send_research_alert,
    iterations: int | None = None,
) -> dict:
    fetcher = fetcher or OkxMarketDataFetcher(base_url=config.okx_base_url)
    state = _load_state(config)
    run_count = 0
    last_result: dict = {"mode": "live", "market_regime": "quiet", "hypotheses": [], "stats_rows": []}

    while iterations is None or run_count < iterations:
        stats_rows, regime_by_market = analyze_market(config, fetcher, candle_limit=None)
        market_regime = _aggregate_regime(regime_by_market)
        current_metrics = _current_hypothesis_metrics(stats_rows)
        degraded = False
        previous_regimes = state.get("regime_by_market", {})

        for market_key, regime in regime_by_market.items():
            if previous_regimes.get(market_key) not in {None, regime}:
                symbol, _timeframe = market_key.split(":", 1)
                alert_sender(
                    f"Market regime changed: {symbol} → {regime}",
                    bot_token=config.telegram_bot_token,
                    chat_id=config.telegram_chat_id,
                )

        active_hypotheses = state.get("active_hypotheses", [])
        for item in active_hypotheses:
            key = (item["pattern"], item["symbol"], item["timeframe"])
            current = current_metrics.get(key)
            if current is None:
                continue
            item["current_win_rate"] = current["win_rate"]
            if current["win_rate"] < config.degradation_win_rate_threshold:
                degraded = True
                alert_sender(
                    f"Hypothesis degraded: {item['pattern']} on {item['symbol']} — "
                    f"win_rate dropped to {current['win_rate']}%",
                    bot_token=config.telegram_bot_token,
                    chat_id=config.telegram_chat_id,
                )

        if degraded:
            alert_sender(
                "Switching to backtest mode — reason: active hypothesis win_rate dropped below threshold",
                bot_token=config.telegram_bot_token,
                chat_id=config.telegram_chat_id,
            )
            return run_backtest(config, fetcher=fetcher, alert_sender=alert_sender, candle_limit=None)

        write_hypothesis_output(
            config,
            mode="live",
            market_regime=market_regime,
            hypotheses=active_hypotheses,
            stats_rows=stats_rows,
        )
        _save_state(config, active_hypotheses=active_hypotheses, regime_by_market=regime_by_market)
        last_result = {
            "mode": "live",
            "market_regime": market_regime,
            "hypotheses": active_hypotheses,
            "stats_rows": stats_rows,
        }
        state = _load_state(config)
        run_count += 1
        if iterations is None:
            time.sleep(config.live_poll_seconds)

    return last_result


def run_adaptive(
    config: AgentConfig,
    *,
    fetcher: OkxMarketDataFetcher | None = None,
    alert_sender=send_research_alert,
    iterations: int | None = None,
) -> dict:
    fetcher = fetcher or OkxMarketDataFetcher(base_url=config.okx_base_url)
    regime_candles = fetcher.fetch_history(config.regime_symbol, config.regime_timeframe, days=7)
    regime = detect_market_regime(regime_candles[-60:], slope_threshold=config.trending_slope_threshold) if regime_candles else "quiet"

    state = _load_state(config)
    has_degraded = any(
        item.get("current_win_rate", item.get("win_rate", 100.0)) < config.degradation_win_rate_threshold
        for item in state.get("active_hypotheses", [])
    )
    mode, reason = decide_mode(market_regime=regime, has_degraded_hypothesis=has_degraded)
    alert_sender(
        f"Switching to {mode} mode — reason: {reason}",
        bot_token=config.telegram_bot_token,
        chat_id=config.telegram_chat_id,
    )
    if mode == "live":
        return run_live(config, fetcher=fetcher, alert_sender=alert_sender, iterations=iterations)
    return run_backtest(config, fetcher=fetcher, alert_sender=alert_sender, candle_limit=None)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Adaptive research hypothesis agent")
    parser.add_argument("--mode", choices=("auto", "backtest", "live"), default="auto")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--iterations", type=int, default=None)
    parser.add_argument("--project-root", default=str(Path.cwd()))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config(args.project_root)
    if args.mode == "backtest":
        run_backtest(config, candle_limit=args.limit)
        return
    if args.mode == "live":
        run_live(config, iterations=args.iterations)
        return
    run_adaptive(config, iterations=args.iterations)


if __name__ == "__main__":
    main()
