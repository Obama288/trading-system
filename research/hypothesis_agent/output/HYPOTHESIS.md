# Trading Hypotheses
Generated: 2026-04-21T21:29:11.711051+00:00
Mode: backtest
Market regime: ranging
Symbols: BTC-USDT, ETH-USDT, SOL-USDT

## Hypothesis 1 — trend_continuation on BTC-USDT 1H
- Statement: trend_continuation on BTC-USDT 1H performs best in asia with 47.02% win_rate.
- Direction: BOTH
- Timeframe: 1H
- Best session: asia
- Win rate: 47.02%
- Avg R:R: 0.46
- Sample count: 336
- Confidence: LOW

## Hypothesis 2 — trend_continuation on SOL-USDT 1H
- Statement: trend_continuation on SOL-USDT 1H performs best in asia with 41.88% win_rate.
- Direction: BOTH
- Timeframe: 1H
- Best session: asia
- Win rate: 41.88%
- Avg R:R: 0.3
- Sample count: 351
- Confidence: LOW

## Hypothesis 3 — trend_continuation on ETH-USDT 1H
- Statement: trend_continuation on ETH-USDT 1H performs best in asia with 39.23% win_rate.
- Direction: BOTH
- Timeframe: 1H
- Best session: asia
- Win rate: 39.23%
- Avg R:R: 0.29
- Sample count: 339
- Confidence: LOW

## Full Statistics Table
| Pattern | Symbol | Timeframe | Direction | Best session | Win rate | Avg R:R | Avg duration | Sample count | Confidence | Sharpe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout_retest | BTC-USDT | 15m | BOTH | london | 30.0% | -0.1 | 15.83 | 30 | LOW | -0.072 |
| breakout_retest | BTC-USDT | 1H | BOTH | london | 47.62% | 0.43 | 34.52 | 21 | LOW | 0.279 |
| breakout_retest | ETH-USDT | 15m | BOTH | london | 23.33% | -0.3 | 24.23 | 30 | LOW | -0.232 |
| breakout_retest | ETH-USDT | 1H | BOTH | london | 50.0% | 0.5 | 24.59 | 22 | LOW | 0.326 |
| breakout_retest | SOL-USDT | 15m | BOTH | london_ny_overlap | 29.17% | -0.12 | 15.12 | 24 | LOW | -0.09 |
| breakout_retest | SOL-USDT | 1H | BOTH | london | 63.64% | 0.83 | 23.5 | 22 | LOW | 0.568 |
| trend_continuation | BTC-USDT | 15m | BOTH | london | 30.0% | -0.08 | 32.36 | 330 | LOW | -0.107 |
| trend_continuation | BTC-USDT | 1H | BOTH | asia | 47.02% | 0.46 | 30.11 | 336 | LOW | 0.256 |
| trend_continuation | ETH-USDT | 15m | BOTH | london | 15.97% | -0.51 | 36.1 | 357 | LOW | -0.535 |
| trend_continuation | ETH-USDT | 1H | BOTH | asia | 39.23% | 0.29 | 34.28 | 339 | LOW | 0.13 |
| trend_continuation | SOL-USDT | 15m | BOTH | london_ny_overlap | 24.47% | -0.31 | 33.92 | 331 | LOW | -0.285 |
| trend_continuation | SOL-USDT | 1H | BOTH | asia | 41.88% | 0.3 | 37.77 | 351 | LOW | 0.175 |

## Integration Notes
- Recommended setup_types for config/strategy.yaml: ['trend_continuation']
- Recommended symbols to add to config/strategy.yaml: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
- Suggested risk.yaml adjustments:
```yaml
risk:
  max_risk_per_trade_pct: 0.5
  max_daily_loss_pct: 2.0
  max_open_positions: 3
```

## Integration with main project
- Read TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from existing .env
- Existing setup_types in config/strategy.yaml: ['breakout_retest']
- Existing risk params in config/risk.yaml: {'max_risk_per_trade_pct': 0.5, 'max_daily_loss_pct': 2.0, 'max_open_positions': 1, 'max_leverage': 3}
- Use same session names as libs/schemas/common.py MarketSnapshot
- Use same prefix conventions as existing alerts_service
