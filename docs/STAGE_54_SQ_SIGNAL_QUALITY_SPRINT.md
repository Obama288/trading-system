# Stage 54-SQ - Signal Quality / Paper Data Sprint

## 1. Status

Status:
PROPOSED / READY FOR HUMAN OWNER APPROVAL

Readiness:
Docs-ready only.
No code-ready, test-ready, runtime-ready, trading-ready, live-ready, or probe-ready claim.

Relationship to current gate:
This document proposes a signal-quality validation track.
This track does not begin until the Human Owner approves this proposal and docs/PROGRESS.md is updated to reflect Stage 54-SQ as an active track.
It does not replace, advance, or close the currently documented gate in `docs/PROGRESS.md`.
It does not authorize BG2-D, Bitget implementation, Bybit retry, private smoke, runtime wiring, or live/probe operations.

## 2. Goal

Validate whether the current manual/paper trading rules show positive expectancy before further automation.

Core principle:
The goal is not to make money during the sprint. The goal is to prove or disprove statistical edge for specific rules under specific conditions.

## 3. Duration and rule version

Duration:
One-month diagnostic sprint.

Rules version:
SQ_1.0

Default decision after month:
Continue unchanged unless evidence clearly shows a problem.

Clarification:
One month is the positive-evidence window, not a requirement to ignore obvious process failure.

## 4. Observation-driven sprint

Stage 54-SQ is observation-driven, not calendar-driven.
One month is the default review window, but the first meaningful checkpoint requires sufficient observations.
The first meaningful checkpoint requires at least 30 valid observations for one setup.
If fewer than 30 observations are collected in one month, the default decision is to continue SQ_1.0 unchanged or review whether filters are too strict.
If 30+ observations are collected before one month ends, the Human Owner may request an early checkpoint.

## 5. Allowed instruments

- BTC
- ETH
- SOL

## 6. Allowed setups

Setup A:
Breakout -> Retest -> Continuation

Setup B:
Trend Pullback -> BOS / Continuation

Deferred:
Range Bounce

Reason Range Bounce is deferred:
- More subjective regime definition.
- Higher false-break / stop-hunt risk.
- Should be tested separately after the first two setups have evidence.

## 7. Timeframes

Core sprint:
- Context timeframe: 4H
- Trigger timeframe: 1H

Optional short-term layer:
- BTC/ETH 15m directional analysis may be recorded separately.
- Do not mix 15m discretionary decisions into core 4H/1H setup statistics unless explicitly tagged.

## 8. BTC influence on ETH

BTC is a market filter for ETH, not an entry signal.

BTC score:
+2 = BTC 4H bullish and 15m/1H bullish
+1 = BTC bullish but near resistance
 0 = BTC chop
-1 = BTC weak / rejecting
-2 = BTC bearish breakdown

ETH decision:
- BTC +2: ETH long allowed if ETH setup is valid.
- BTC +1: ETH long only if very clean.
- BTC 0: reduced confidence / usually no-trade.
- BTC -1 or -2: ETH long forbidden.

## 9. OKX Events

OKX Events may be used as a short-term sentiment filter only.

Rules:
- Event bias cannot create a trade.
- Chart setup valid + Event confirms = stronger context.
- Chart setup valid + Event against = caution / skip.
- No chart setup + Event bullish/bearish = no trade.
- Crowded Event bias near a key level is a trap risk, not automatic confirmation.

## 10. Microcap / launch tokens

VELLUM, MEGA-like assets are separate case studies.

Rules:
- Do not mix them with BTC/ETH/SOL sprint stats.
- They must pass identity, liquidity, age/history, structure, and BTC/ETH risk-on gates before consideration.
- Microcap observations are not proof of core signal quality.

## 11. Metrics

Track:
- expectancy in R
- win rate
- avg win R
- avg loss R
- profit factor
- max drawdown R
- rule violation rate
- setup quality rate
- frequency of valid signals
- BTC score impact on ETH
- manual mistake vs strategy failure

## 12. Observations

Rules:
- No-trade observations count.
- Skipped valid signals count.
- Do not mix Setup A and Setup B statistics.
- Do not mix discretionary trades into SQ sprint stats.
- No initial stop means no valid sprint trade.
- Every sprint trade must have entry, initial stop, target logic, and R calculation before entry.

## 13. Personal manual trading boundary

Personal manual trading is outside Hephaestus project scope.
Personal trades must not be recorded as project evidence.
Personal trades must not be included in Stage 54-SQ statistics.
Personal trades must not affect project stages, readiness claims, or signal-quality conclusions.
A market setup may be recorded only if it is evaluated independently under SQ_1.0 rules, not because a personal trade was taken.

## 14. Automation boundary

Allowed now:
- manual external price alerts, such as exchange or charting-platform price notifications
- position size calculator
- journal auto-fill helpers
- metrics dashboard
- candidate detector without execution

This does not authorize Hephaestus system alerting infrastructure, runtime wiring, or automated execution.

Not allowed now:
- automated entries
- live trading
- private exchange actions
- execution wiring
- changing rules after a few trades

## 15. Early stop conditions

Early stop is allowed for obvious process failure or clearly broken assumptions.

Early stop conditions:
- Rule violation rate > 50% after 10 observations:
  stop sprint and fix process first.
- Zero valid signals in 14 days:
  review filter logic and setup definitions; do not automatically change strategy.
- Profit factor < 0.4 after 20 completed trades:
  setup review checkpoint; do not auto-change without Human Owner decision.
- Repeated inability to define structural stop before entry:
  stop sprint and fix setup definitions.
- Any live-trading, secret, or exchange-action boundary breach:
  stop and escalate to Human Owner.

Important:
Early stop does not mean automatic strategy mutation.
It means review, classify the failure, and decide whether to continue, fix process, or start a new rules version.

## 16. Exit gate to future paper execution proposal

Stage 54-SQ does not authorize paper execution, live trading, exchange operations, or automated entries.
It may only recommend a future paper-execution proposal if one setup has enough evidence.

Minimum recommendation gate:
- at least 30 valid observations for one setup;
- positive expectancy in R;
- profit factor above 1.3;
- average loss controlled near -1R;
- result is not explained by one outlier;
- rule violation/process failure is not the main driver;
- rules are objective enough to reproduce;
- Human Owner explicitly approves the next stage.

Stronger gate for later automation discussion:
- 50+ observations;
- expectancy remains positive;
- profit factor improves toward or above 1.5;
- BTC/ETH filter impact is understood if ETH is involved.

This gate only allows a proposal for a future paper-execution / simulated-execution stage.
It does not authorize live trading.

## 17. Decision checkpoints

Week 1:
Process check only. Confirm rules are understandable and executable.

Day 14:
Check whether valid signals appear and whether filters are too strict.

End of month:
Review observations and decide:
- continue SQ_1.0 unchanged
- collect more data
- fix process/journal discipline
- change one clearly identified rule
- reject one setup

Do not change rules mid-sprint unless Human Owner explicitly stops the sprint.

## 18. Explicit non-goals

- Proving profitability.
- Approving live trading.
- Starting exchange implementation.
- Retrying Bybit.
- Implementing Bitget.
- Creating a generic exchange adapter.
- Automated execution.
- Treating OKX Events as standalone signals.
