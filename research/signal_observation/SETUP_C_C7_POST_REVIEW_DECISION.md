# Setup C C7 Post-Review Decision Record

## Purpose

Companion to `docs/archive/STAGE_54_SQ_C7_EXPANDED_VALIDATION_DESIGN_LOCK.md`. This
record accepts the Stage 54-SQ C7 expanded validation evidence run, captures
the independent post-C7 review verdict, lists the main residual caveats, and
states the recommended next research gate.

This record is research-only. It does not authorize paper trading, runtime
wiring, live trading, probe access, or any readiness promotion.

## C7 Verdict Accepted

- **C7_PASS** accepted.
- Evidence run scope: locked backward expanded window
  `2022-01-01T00:00:00Z` to `2023-12-17T12:00:00Z`; public Bitget 4H OHLCV
  only; frozen symbol set BTCUSDT, ETHUSDT, SOLUSDT; lookback 40; rebalance
  every 6 bars; vol proxy ATR(20) / close; cost moderate; high_cost funding
  in-gate; random baseline seed `RANDOM_SEED + PRIMARY_LOOKBACK = 5443`,
  iterations 1000.
- Evidence artifacts (committed at `c108197`, remote-visible):
  - `research/signal_observation/output/bitget/setup_c_c7_expanded_report.txt`
  - `research/signal_observation/output/bitget/setup_c_c7_expanded_report.json`
- All five C7 gate conditions pass on the locked expanded window:
  1. expanded vt-post-cost-moderate > 0
  2. expanded beats random p75
  3. funding-adjusted high_cost > 0
  4. ≥ 2 of 3 symbols non-negative (3 of 3 non-negative observed)
  5. combined-retention ratio ≥ 50% (observed ≈ 2.49×)

## Independent Post-C7 Review

- Verdict: **PASS**.
- The C7 design lock and the analyzer's logic were respected end-to-end:
  no parameter changes, no symbol changes, no rebalance changes, no
  threshold tweaks, no gate-criteria changes after seeing results. Locked
  window boundaries, single-public-download policy, and frozen-component
  policy were all honored. No private exchange endpoint was called, no
  credentials were used, no order or cancel was issued, no paper or live
  readiness was claimed.

## Status After C7 PASS

- Setup C remains **PASS_CANDIDATE research-only**.
- No paper readiness, runtime readiness, trading readiness, probe readiness,
  or live readiness is claimed by this record.
- LIVE remains **NO-GO**.
- Escalation remains **HOLD**.
- Per design lock §"What C7 Does Not Authorize", the C7 PASS verdict does
  not authorize paper trading, live trading, runtime wiring, private API
  access, exchange operations, parameter optimization, strategy filters,
  order_status, orders, cancels, set_leverage, live reconcile, or live
  execution.

## Main Caveats

1. **SOL concentration.** SOLUSDT contributes approximately 53% of the
   expanded vt-post-cost-moderate headline (≈ `+91.61` of `+171.42` total),
   versus BTCUSDT (≈ `+43.80`, ~26%) and ETHUSDT (≈ `+36.02`, ~21%).
   Gate condition 4 (≥ 2 of 3 symbols non-negative) is satisfied with all
   three symbols non-negative, but the pooled headline is single-symbol
   heavy. Cross-symbol diversification is weaker than the gate alone
   suggests.
2. **Expanded backward window is stronger than the newer dev/validation
   period.** The combined-retention ratio is ≈ `2.49×`, well above the
   `0.50×` floor; this reflects the expanded backward window producing
   stronger vt-post-cost-moderate than the more recent dev/validation
   period rather than a uniform edge across regimes. Setup C may have been
   more profitable in the 2022–2023 regime than in the current
   dev/validation regime, which is consistent with regime drift rather
   than stable edge.
3. **Expanded high_vol and low_vol regimes are both positive.** Expanded
   regime diagnostics show both high_vol and low_vol buckets contributing
   positively, in contrast to the C5 dev/validation finding of high_vol
   weakness in the validation split (interpretation
   `validation_only_or_discovery_only`). The expanded backward regime is
   structurally different from the recent dev/validation regime on this
   axis. Regime diagnostics remain observational only and do not introduce
   a strategy filter.
4. **Single venue, narrow universe.** All evidence is Bitget-only and
   restricted to a 3-symbol universe (BTC, ETH, SOL). Cross-venue and
   wider-universe behavior is unobserved.

## Recommended Next Research Gate

- **Cross-venue validation** of Setup C is the recommended next research
  gate before any move toward wider-universe testing or execution realism.
- Cross-venue validation must test whether the same Setup C detector
  (unchanged: 40-bar lookback, 6-bar rebalance, ATR(20)/close vol proxy,
  moderate cost, deterministic random baseline) produces comparable
  vt-post-cost-moderate on at least one other public exchange's 4H OHLCV
  for the same frozen symbol set.
- Cross-venue validation requires a separate design lock and explicit
  owner approval before any code, data, or analysis is added. Source must
  be public-only; no credentials; no private endpoints; no order, cancel,
  withdraw, transfer, or live execution; no paper readiness; no runtime
  wiring.
- Wider symbol universe and execution realism (slippage modeling, latency,
  liquidity, partial-fill behavior, exchange fee tiers, etc.) are deferred
  until cross-venue validation is completed and independently reviewed.

## What This Record Does Not Authorize

- Paper trading.
- Live trading.
- Runtime or service wiring.
- Private exchange endpoints, credentials, signed payloads, API keys, or
  secret-derived values.
- Orders, cancels, `set_leverage`, withdraws, transfers, or live reconcile.
- Any form of readiness claim (paper / runtime / probe / trading / live).
- Parameter optimization, symbol additions, lookback changes, rebalance
  changes, timeframe changes, threshold changes, or regime filter
  introduction on the existing Setup C / C1–C7 design lock.
- Re-download of additional Bitget data for the C7 expanded window
  (single-download policy is in force).
