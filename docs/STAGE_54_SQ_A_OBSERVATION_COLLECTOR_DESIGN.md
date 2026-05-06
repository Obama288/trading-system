# Stage 54-SQ-A - Automated Signal Observation Collector Design

## 1. Status

Status:
PROPOSED / DESIGN ONLY

Readiness:
Docs-ready only.
No code-ready, test-ready, runtime-ready, trading-ready, live-ready, or probe-ready claim.

Relationship:
This document extends the Stage 54-SQ proposal with a design for automated signal observation collection.
It does not activate Stage 54-SQ.
It does not update docs/PROGRESS.md.
It does not authorize implementation.
It does not authorize paper execution, live trading, exchange operations, or private API use.

## 2. Purpose

Define a detector + outcome tracker that collects rule-defined signal observations automatically.

The collector should:
- read public OHLCV candles;
- scan BTC/ETH/SOL;
- detect Setup A and Setup B candidates;
- record theoretical entry, stop, target, and BTC score context;
- resolve simulated outcome in R after a defined window;
- produce machine-readable observations and summary reports.

The collector must not:
- place orders;
- cancel orders;
- call private exchange endpoints;
- use API keys or secrets;
- connect to execution_service;
- change risk_engine, kill_switch, orchestrator, or position_manager;
- use personal manual trades as evidence.

## 3. Data requirements

Required public data:
- symbols: BTCUSDT, ETHUSDT, SOLUSDT;
- timeframes: 4H context, 1H trigger;
- OHLCV candles;
- at least 6 months of history, preferably 12 months;
- one exchange/source per run;
- no private API;
- no credentials.

Optional later:
- 15m BTC/ETH directional context;
- OKX Events sentiment snapshots if available without private credentials;
- spread/slippage model for later paper-execution stages.

## 4. Core outputs

Observation fields:
- observation_id
- created_at_utc
- source_exchange
- symbol
- setup_id: A or B
- direction
- context_timeframe
- trigger_timeframe
- signal_time
- entry_time_theoretical
- entry_price_theoretical
- stop_price_theoretical
- stop_reason
- target_price_theoretical
- initial_R
- btc_score
- btc_context
- eth_btc_filter_status if symbol is ETH
- session_utc_hour
- session_label
- volume_context
- blocked_reason if invalid
- status: candidate / valid / blocked / resolved
- outcome_window_candles
- MFE_R
- MAE_R
- final_R
- hit_target_before_stop
- hit_stop_before_target
- resolution_reason

## 5. Setup A - Breakout -> Retest -> Continuation

SQ_1.0 long rules:

Context timeframe:
- 4H.

Trigger timeframe:
- 1H.

Range/base detection:
- Lookback: last 48 candles on 4H.
- Range high = highest high in lookback.
- Range low = lowest low in lookback.
- Range height must be >= 1.0 * ATR(14) on 4H.
- Range must have at least 3 touches near the relevant boundary.
- Touch tolerance: 0.15 * ATR(14) on 4H.
- Touch definition should be based on wick entering the tolerance zone.
- Record whether touches used high/low wick or close.

Breakout:
- 4H candle closes above range_high.
- Breakout close distance >= 0.2 * ATR(14) on 4H above range_high.
- Breakout candle body >= 50% of candle range.
- Breakout candle volume > 1.5x average volume over the last 20 4H candles.

Retest:
- Within next 24 candles on 1H after breakout, price returns to the retest zone.
- Retest zone = range_high +/- 0.25 * ATR(14) on 1H.
- Price may overshoot the zone, but the confirmation candle must close back above range_high.

Theoretical entry:
- Open of the next 1H candle after retest confirmation.

Stop:
- Below retest swing low - 0.1 * ATR(14) on 1H.

Target:
- Fixed +2R target for SQ_1.0.

Outcome window:
- 24 candles on 1H after theoretical entry.

Outcome:
- If stop is hit before target: -1R.
- If target is hit before stop: +2R.
- If neither is hit within the outcome window: calculate final_R from final 1H close.
- If both stop and target are inside the same candle, mark ambiguous and use conservative resolution: stop first.

Short rules:
- Symmetric inverse of long rules.
- Use range_low breakdown, close below range_low, retest from below, stop above retest swing high, fixed +2R target.

## 6. Setup B - Trend Pullback -> BOS / Continuation

SQ_1.0 long rules:

Context timeframe:
- 4H.

Trigger timeframe:
- 1H.

Trend regime:
- 4H close above EMA200.
- EMA20 above EMA50 on 4H.
- Last confirmed pivot high > previous confirmed pivot high.
- Last confirmed pivot low > previous confirmed pivot low.

Pivot definition:
- Pivot high = high greater than highs of 2 candles left and 2 candles right.
- Pivot low = low lower than lows of 2 candles left and 2 candles right.
- Record pivot lag as a known limitation.

Pullback:
- Price pulls back to EMA20 on 4H +/- 0.25 * ATR(14) on 4H.
- Previous confirmed 4H pivot low is not broken.
- For SQ_1.0, Fibonacci pullback alternatives are out of scope and listed as SQ_1.1 candidate improvements.

1H BOS trigger:
- During pullback, identify local 1H swing high.
- Signal occurs when 1H candle closes above that local swing high.
- Wick-only break does not count.

Theoretical entry:
- Open of next 1H candle after BOS confirmation.

Stop:
- Below pullback 1H swing low - 0.1 * ATR(14) on 1H.

Target:
- Fixed +2R target for SQ_1.0.
- Also record distance to previous 4H swing high in R as air_to_obstacle_R.

Outcome window:
- 24 candles on 1H after theoretical entry.

Outcome:
- Same as Setup A.

Short rules:
- Symmetric inverse:
  4H close below EMA200;
  EMA20 below EMA50;
  lower highs/lower lows;
  pullback to EMA20;
  BOS below local 1H swing low;
  stop above pullback 1H swing high.

## 7. BTC score and ETH tagging

BTC score is recorded for all ETH signals.

Do not pre-block raw ETH observations based on BTC score in SQ_1.0.
Instead record:
- eth_signal_raw = setup detected;
- eth_signal_allowed_by_btc_filter = true if BTC score >= +1 for long, <= -1 for short;
- btc_score at signal time.

BTC score:
+2 = BTC 4H bullish and 1H/15m bullish
+1 = BTC bullish but near resistance
 0 = BTC chop
-1 = BTC weak / rejecting
-2 = BTC bearish breakdown

Purpose:
Compare ETH outcomes with and without BTC filtering.

## 8. Session and time tagging

For every observation, record:
- UTC hour;
- weekday;
- session_label:
  - Asia
  - Europe
  - US
  - overlap
  - weekend
- whether signal occurred near major session open.

SQ_1.0 does not block by session.
Session data is recorded for later analysis.

## 9. Outcome calculation

Use R-based simulated outcomes only.

Rules:
- No personal manual trades.
- No actual execution.
- No account balance.
- No position size.
- No dollars.
- Initial_R is based on theoretical entry to theoretical stop.
- MFE_R and MAE_R should be calculated over the outcome window.
- final_R should be calculated from either stop, target, or final close.
- Same-candle stop/target ambiguity resolves conservatively as stop first.

## 10. Storage proposal

Preferred machine-readable output:
- JSONL for raw observations;
- CSV for summary/reporting.

Proposed paths for future implementation only:
- research/signal_observation/output/observations.jsonl
- research/signal_observation/output/observations.csv
- research/signal_observation/output/summary.md

Do not create these files in this design slice.

## 11. Reports

Future reports should include:
- observations by setup;
- observations by symbol;
- expectancy in R;
- win rate;
- profit factor;
- avg win R;
- avg loss R;
- max drawdown R;
- MFE/MAE distribution;
- ETH results by BTC score;
- session performance;
- signal frequency.

## 12. Autonomy levels

Level 0:
Offline detector and outcome tracker. No execution. Current design target.

Level 1:
Detector + summary report. No execution.

Level 2:
Detector + manual external alert candidates. No Hephaestus system alerting infrastructure. No execution.

Level 3:
Paper/simulated execution. Separate future approval required.

Level 4:
Live execution. Not in scope. NO-GO.

## 13. Open questions

- Whether existing apps/market_data can supply historical public OHLCV.
- Whether existing libs/exchange public adapters can be reused without private API.
- Whether adding a dependency such as ccxt is acceptable later.
- Whether SOL needs different lookback parameters.
- Whether Setup B should add Fibonacci pullback in SQ_1.1.
- Whether session filters should later become blockers.
- Whether spread/slippage modeling is needed before paper execution.
- How to handle missing candles and exchange maintenance periods.

## 14. Explicit non-goals

- No implementation in this slice.
- No runtime integration.
- No private exchange API.
- No API keys or secrets.
- No paper execution.
- No live trading.
- No orders or cancels.
- No risk_engine, execution_service, orchestrator, kill_switch, or position_manager changes.
- No manual trade journal.
- No readiness upgrade.
