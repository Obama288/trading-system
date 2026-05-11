# Setup C C7 Cross-Venue Decision Record

## Purpose

Companion to `docs/STAGE_54_SQ_C7_EXPANDED_VALIDATION_DESIGN_LOCK.md`,
`docs/STAGE_54_SQ_C7_CROSS_VENUE_DESIGN_LOCK.md`, and
`research/signal_observation/SETUP_C_C7_POST_REVIEW_DECISION.md`. This
record accepts the cross-venue C7 evidence (Bitget + Binance) as research
evidence after the governance reconciliation at `e355aff`, lists the main
residual caveats, and states the recommended next research gate.

This record is research-only. It does not authorize paper trading, runtime
wiring, live trading, probe access, or any readiness promotion.

## 1. Verdict

**Cross-venue both-PASS accepted as research evidence.**

Independent review verdict: math PASS on both venues; governance issue
reconciled by the cross-venue design lock at `e355aff`. The cross-venue
design lock is the envelope the Binance run is retroactively measured
against; it locks the same envelope for any future cross-venue work.

## 2. Venues

- **Bitget USDT-FUTURES public history-candles:** decision `C7_PASS`.
  Evidence at `c108197` (data `16ae508`):
  `research/signal_observation/output/bitget/setup_c_c7_expanded_report.json`.
- **Binance USDT-M Futures public klines:** decision `C7_PASS`.
  Evidence at `775d739` (data `583e724`):
  `research/signal_observation/output/binance/setup_c_c7_expanded_report.json`.
- **OKX public history-candles:** authorized by the cross-venue design
  lock but **deferred / blocked** — every reachability probe from the
  current host returned HTTP 403 Cloudflare error 1010 (ASN-level block).
  No data download attempted. No evidence.

## 3. Gate Summary

All five C7 gate conditions pass **independently** on both venues. Same
locked detector, same locked windows, same locked frozen symbols (BTCUSDT
/ ETHUSDT / SOLUSDT), same 4H timeframe.

| # | Condition | Bitget | Binance |
|---|---|---|---|
| 1 | expanded vt-post-cost-moderate > 0 | `171.4236` ✅ | `113.8858` ✅ |
| 2 | expanded > random p75 | `171.42 > 5.38` ✅ | `113.89 > 5.98` ✅ |
| 3 | funding-adjusted high_cost > 0 | `171.1400` ✅ | `112.2726` ✅ |
| 4 | ≥ 2 of 3 symbols non-negative | 3 / 3 ✅ | 3 / 3 ✅ |
| 5 | combined-retention ratio ≥ 50% | `2.485×` ✅ | `4.980×` ✅ |

## 4. Interpretation

**Cross-venue PASS means gate replication, not magnitude replication.**

A venue passes if and only if all five C7 gate conditions are
independently satisfied on that venue's evidence. Cross-venue PASS does
not require numeric magnitudes to match across venues; it requires only
that each venue independently satisfies the locked gate. Both Bitget and
Binance satisfy this independent gate-replication test.

Magnitude differences between venues are observational and must be
recorded (see Caveats). They do **not** invalidate the cross-venue both-
PASS verdict.

## 5. Caveats

1. **Binance dev magnitude is much lower than Bitget dev.** Binance
   development-window vt-post-cost-moderate is approximately **25%** of
   Bitget's (`28.61` vs `115.43`). The expanded backward window values
   are closer (Binance `113.89` ≈ 66% of Bitget's `171.42`). The signal's
   headline magnitude on Binance over the dev period is much weaker than
   on Bitget. Cause has not been determined and is a separate research
   question.
2. **Binance combined-retention ratio is inflated by a small denominator.**
   The Binance combined-retention ratio of `4.98×` is much higher than
   Bitget's `2.49×`, but this is driven by Binance's much smaller dev-only
   denominator, not by a stronger Binance edge. Do **not** interpret a
   higher cross-retention ratio as a stronger venue. Both ratios satisfy
   the locked `≥ 0.50` floor; the ratio test is binary.
3. **SOL concentration is amplified on Binance.** SOL share of the
   expanded headline is approximately **69.6%** on Binance vs **53.4%**
   on Bitget. Both venues satisfy cond_4 (≥ 2 of 3 symbols non-negative;
   3 / 3 observed on both venues). The locked policy does not impose a
   concentration cap; the delta is observational.
4. **Evidence is still 3-symbol universe.** No wider-universe behavior
   is observed on either venue. Wider-universe testing remains deferred
   per the single-venue post-C7 review record and the cross-venue design
   lock.
5. **OKX remains deferred / blocked from the current host.** Cloudflare
   1010 ASN-level block on every reachability probe. Lifting the block
   is a host / network change, not an in-repo code task. OKX C7 evidence
   would extend the cross-venue both-PASS state to three venues if and
   when access is restored.

## 6. Decision

**Keep Setup C active as research-only PASS_CANDIDATE after cross-venue
replication.**

- Setup C remains **PASS_CANDIDATE research-only**.
- Escalation remains **HOLD**.
- LIVE remains **NO-GO**.
- Mode remains paper trading only.
- **Do not promote readiness.** Per the single-venue C7 design lock §
  "What C7 Does Not Authorize" and the cross-venue design lock § "What
  This Design Lock Does Not Authorize", cross-venue both-PASS does not
  authorize paper trading, runtime wiring, trading readiness, probe
  readiness, or live readiness.

## 7. Recommended Next Research Gate

**Direction-call agreement diagnostic between Bitget and Binance over the
dev window.**

- Purpose: determine whether the Binance dev-magnitude divergence (Caveat
  1) is driven by direction-call flips between venues (the detector
  disagreeing on long vs short at the same rebalance bar) or by
  volatility / micro-pricing differences (same direction calls but
  different per-interval returns and vol_proxy values).
- Method (to be locked by a separate diagnostic design lock if owner
  approves): for each rebalance bar timestamp present in both venues'
  dev intervals, compare the per-symbol Setup C direction call. Report
  per-symbol agreement rate, per-symbol disagreement rate, distribution
  of disagreement timestamps over time, and whether disagreements
  concentrate in particular regime buckets.
- Public-data-only. No credentials. No private endpoints. No order /
  cancel / withdraw / transfer / live execution. **Observational only**
  — no gate change, no detector change, no readiness change.
- Output: a single diagnostic JSON / text artifact under
  `research/signal_observation/output/cross_venue/`. No analyzer change.

## 8. Secondary Next Option

**OKX C7 evidence, if reachable from another network.**

- The cross-venue design lock already authorizes OKX as a third
  replication site. The OKX public bounded-pagination downloader exists
  at `research/signal_observation/okx_public_downloader.py` (tests pass).
- Trigger: a host / network change that lifts the Cloudflare 1010 block
  on `www.okx.com`. Lifting the block is not an in-repo code task.
- If OKX C7 is added and passes, the cross-venue both-PASS state extends
  to three independent venues; if it fails or holds, the cross-venue
  decision record must be amended.
- Either way, no readiness promotion.

## 9. What This Record Does Not Authorize

- Paper trading.
- Live trading.
- Runtime or service wiring.
- Private exchange endpoints, credentials, signed payloads, API keys, or
  secret-derived values.
- Orders, cancels, `set_leverage`, withdraw, transfer, or live reconcile.
- Any form of readiness claim (paper / runtime / probe / trading / live).
- Parameter optimization, symbol additions, lookback changes, rebalance
  changes, timeframe changes, threshold changes, regime-filter
  introduction, or gate-criteria changes on any venue.
- Re-download of expanded or dev data on any venue that already has
  locked data committed (Bitget `16ae508`, Binance `583e724`).
- Adding a fourth venue without a separate explicit owner approval and
  an extension of the cross-venue design lock.
- Wider symbol universe and execution realism (slippage, latency,
  liquidity, partial fills, fee tiers) remain deferred.
