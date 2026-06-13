# Stage 54-SQ-B0 - Setup B Design Lock

Setup name:
Trend Pullback BOS / Continuation

## 1. Status and Scope

Stage:
54-SQ-B0.

Status:
Design lock / research spec only.

Readiness:
Docs-ready only.
No code-ready, test-ready, runtime-ready, trading-ready, live-ready, or
probe-ready claim.

Scope:
- no detector implementation yet;
- no runtime integration;
- no paper trading;
- no live trading;
- no private API;
- no exchange account operations;
- no orders, cancels, transfers, withdrawals, or set_leverage;
- no service wiring;
- live trading remains NO-GO.

This document does not update `docs/PROGRESS.md` and does not change the
current Stage 54-BG2-C gate. If this document conflicts with
`docs/PROGRESS.md`, `docs/PROGRESS.md` wins.

## 2. Reason for Setup B

Setup A, Breakout -> Retest -> Continuation, is observation-starved on the
current Bitget USDT-FUTURES BTC/ETH/SOL 1H/4H research dataset.

Current accepted research context:
- Setup A baseline generated 6 observations over about 6.5 months.
- Stage 54-SQ-A13 sensitivity variants reached at most 23 observations.
- The Stage 54-SQ observation floor is 30 valid observations for one setup
  before meaningful review.
- Further Setup A tuning risks overfitting the same small dataset.

Setup B is introduced as a separate hypothesis, not as a patched Setup A.
It does not prove edge and does not imply paper, runtime, trading, live, or
probe readiness.

## 3. Input Data

Venue:
Bitget public market data.

Product type:
USDT-FUTURES.

Symbols:
- BTCUSDT
- ETHUSDT
- SOLUSDT

Primary signal timeframe:
4H first.

Optional future extension:
1H only after 4H behavior is understood.

Data boundary:
- use public/local OHLCV only;
- no private API;
- no API keys;
- no account data;
- no balance data;
- no position data;
- no order data.

## 4. Core Hypothesis

In an established trend, price pulls back without invalidating the trend, then
breaks pullback structure in the trend direction.

The research collector simulates entry at BOS confirmation, places a fixed stop
beyond pullback invalidation, and measures outcomes in R. All outputs are
research observations only.

## 5. Trend Definition

Use structural pivot trend first. EMA may be recorded as context, but EMA alone
must not define the base trend in SQ_B_1.0.

Uptrend:
- at least 2 confirmed higher highs;
- at least 2 confirmed higher lows.

Downtrend:
- at least 2 confirmed lower highs;
- at least 2 confirmed lower lows.

Pivot definition:
- pivot high = high greater than highs of N candles left and N candles right;
- pivot low = low lower than lows of N candles left and N candles right;
- starting N = 2 for 4H.

Pivot lag:
- N = 2 on 4H means about 8 hours of confirmation delay;
- this lag is acceptable for observation collection and research;
- any future execution design must account for pivot confirmation lag
  separately.

## 6. Pullback Definition

Uptrend pullback:
- starts after a confirmed swing high;
- retraces toward prior structure without breaking the last confirmed swing low.

Downtrend pullback:
- inverse of uptrend pullback;
- starts after a confirmed swing low;
- retraces toward prior structure without breaking the last confirmed swing high.

Pullback duration:
- minimum 3 candles on the signal timeframe;
- maximum 20 candles on the signal timeframe.

Pullback depth:
- initial research range = 0.30 to 0.70 of the prior impulse.

Primary SQ_B_1.0 pullback rule:
- use prior impulse retracement depth from 0.30 to 0.70;
- require the prior structural swing low/high to remain unbroken.

Strong trend caveat:
- strong trends may not pull back to EMA20;
- EMA20 touch must not be the only valid pullback definition in B0.

Future SQ_1.1 alternatives, not active filters in SQ_B_1.0:
- prior pivot high/low retest;
- Fibonacci 0.382 pullback;
- shallow structure pullback;
- EMA20 touch as diagnostic context, not a required base filter.

## 7. BOS Definition

Long BOS:
- candle closes above the highest high of the pullback sequence.

Short BOS:
- candle closes below the lowest low of the pullback sequence.

Rules:
- BOS must be in the direction of the primary trend;
- wick-only BOS is not enough for the base case;
- BOS candle body ratio must be recorded;
- BOS volume ratio versus recent average volume must be recorded;
- volume is diagnostic only in SQ_B_1.0 and is not a hard gate unless a later
  hypothesis document explicitly justifies it.

## 8. Entry Rule

Research entry price:
- BOS candle close.

Also record:
- next-bar open for future slippage sensitivity.

Boundaries:
- no limit-order assumptions;
- no execution assumption;
- no fees or slippage in the base result unless clearly marked as later
  analysis.

## 9. Stop Placement

Long stop:
- below pullback low minus buffer.

Short stop:
- above pullback high plus buffer.

Buffer:
- use the smaller of:
  - 0.5 percent of entry price;
  - 1.0 * ATR(14).

Rules:
- stop is fixed at entry for base research;
- no trailing stop in the base case;
- no valid observation exists without a structural stop.

## 10. Target and Outcome Rules

Measure outcomes at:
- 1R;
- 1.5R;
- 2R.

Base headline target:
2R.

Reporting rule:
Do not hide 1R or 1.5R behavior. Store all three outcome columns.

Timeout:
- maximum 10 bars on 4H for the initial run;
- unresolved observations after the timeout are explicit flats/timeouts;
- flats/timeouts must not be silently ignored.

Same-candle ambiguity:
If stop and target are both inside the same candle, resolve conservatively as
stop first unless a later design explicitly replaces this rule.

## 11. Invalidation

Pre-entry invalidation:
- trend invalidates before BOS;
- pullback exceeds allowed retracement;
- pullback breaks the prior structural low/high;
- BOS does not trigger within the allowed pullback window.

Post-entry invalidation:
- stop hit.

Research boundary:
No discretionary invalidation after entry in research mode.

## 12. Required Diagnostics Per Observation

Record:
- symbol;
- timeframe;
- direction long/short;
- signal_time;
- signal_hour_utc;
- entry_time;
- entry_price;
- stop;
- target_1r;
- target_1_5r;
- target_2r;
- pullback_start_time;
- pullback_end_time;
- BOS candle timestamp;
- trend age in swings;
- pullback depth;
- pullback duration;
- BOS body ratio;
- BOS volume ratio;
- ATR at entry;
- session label if the existing session utility supports it;
- BTC context for ETH/SOL if available in a later stage;
- MAE;
- MFE;
- bars_to_resolution;
- outcome at 1R;
- outcome at 1.5R;
- outcome at 2R.

No account IDs, balances, positions, private data, order IDs, or execution data
may be recorded.

## 13. Funnel Diagnostics for Setup B

Counters:
- windows checked;
- trend detected;
- valid pullback detected;
- pullback invalidated before BOS;
- BOS candidates;
- BOS confirmed;
- entry observations;
- resolved;
- wins/losses/flats at 1R;
- wins/losses/flats at 1.5R;
- wins/losses/flats at 2R;
- failures by reason.

Failure reasons should include, where measurable:
- insufficient confirmed pivots;
- no structural trend;
- pullback too shallow;
- pullback too deep;
- pullback too short;
- pullback too long;
- prior structural low/high broken;
- BOS missing;
- wick-only BOS;
- stop invalid or non-structural;
- no candles available for outcome resolution.

## 14. Anti-Overfitting Rules

- No parameter changes after seeing results without a new hypothesis document.
- Every parameter relaxation is a new hypothesis.
- Do not select the best R target from one dataset only.
- Do not pool 1H and 4H results until behavior is compared.
- Do not pool long and short results until direction behavior is compared.
- 30 observations is a research continuation floor, not a paper trading gate.
- Prefer 50+ observations before strong conclusions.
- Do not claim signal edge from one venue/timeframe/sample window.

## 15. Paper and Live Boundary

B0 does not authorize:
- paper trading;
- runtime wiring;
- private API;
- exchange account access;
- orders;
- cancels;
- set_leverage;
- transfers;
- withdrawals;
- live trading.

Live trading remains NO-GO.

## 16. Next-Stage Implementation Guidance

Next possible stage:
Stage 54-SQ-B1 should implement the Setup B detector and diagnostics using
this design, if separately authorized by the Human Owner.

Allowed future implementation scope:
- research-layer only;
- local/public OHLCV only;
- deterministic Setup B detector;
- deterministic Setup B funnel diagnostics;
- mocked or local-data tests only;
- no exchange account access;
- no execution.

Likely future files:
- `research/signal_observation/setup_b.py`
- `research/signal_observation/setup_b_diagnostics.py`
- `research/signal_observation/run_setup_b_diagnostics.py`
- `tests/research/test_signal_observation_setup_b.py`
- `tests/research/test_signal_observation_setup_b_diagnostics.py`
- optional local output artifacts under `research/signal_observation/output/`
  if explicitly authorized.

Forbidden future files and areas unless a separate owner-approved stage changes
scope:
- `apps/`
- `libs/`
- `config/`
- `infra/`
- `alembic/`
- runtime service files
- risk_engine
- execution_service
- orchestrator
- position_manager
- kill_switch
- private exchange clients
- private API scripts
- account/balance/position/order/cancel/set_leverage paths

Stage 54-SQ-B1 must not change the money path and must not claim paper,
runtime, trading, live, or probe readiness.
