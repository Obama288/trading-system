# Stage 54-SQ C7 Cross-Venue Validation Design Lock

## Purpose

Govern cross-venue replication of Setup C after the Bitget C7_PASS evidence
run, by extending the locked-window, locked-gate, locked-detector policy
from `docs/STAGE_54_SQ_C7_EXPANDED_VALIDATION_DESIGN_LOCK.md` (the
"single-venue C7 design lock") to additional public venues.

**This is a governance reconciliation after owner-approved Binance work; it
does not alter data, code, gates, or evidence.** It records the design lock
that the Binance C7 evidence run at `775d739` is retroactively measured
against, and it locks the same envelope for any future cross-venue work.

This design lock is research-only. It does not authorize paper trading,
runtime wiring, live trading, probe access, or any readiness promotion.

## Relationship to the single-venue C7 design lock

- The single-venue C7 design lock (`docs/STAGE_54_SQ_C7_EXPANDED_VALIDATION_DESIGN_LOCK.md`)
  governs the Bitget evidence run. It remains the authoritative C7 gate /
  detector / window source.
- This cross-venue design lock **does not modify** any single-venue rule.
  Every locked component — detector, symbols, timeframe, lookback,
  rebalance, vol proxy, cost scenarios, funding scenarios, random baseline
  seed and iterations, gate criteria, anti-cherry-picking rules — is
  inherited verbatim.
- The post-C7 review decision record
  (`research/signal_observation/SETUP_C_C7_POST_REVIEW_DECISION.md`) stated
  that "cross-venue validation requires a separate design lock and explicit
  owner approval." This file is that separate design lock.

## Authorized Venues

- **Bitget USDT-FUTURES public history-candles:** original C7 single-venue
  evidence venue. Status: data committed at `16ae508`; evidence committed
  at `c108197`; decision = `C7_PASS`. Done.
- **Binance USDT-M Futures public klines:** authorized as cross-venue
  replication site. Status: data committed at `583e724`; evidence committed
  at `775d739`; decision = `C7_PASS`. Done.
- **OKX public history-candles:** authorized as a future cross-venue
  replication site. **Deferred.** Reachability probe from the current host
  returned HTTP 403 Cloudflare error 1010 (ASN-level block) on every
  attempt; until access is restored or the work is moved to a host that can
  reach `www.okx.com`, OKX is not actionable.

No other venues are authorized by this design lock. Adding a new venue
requires a separate explicit owner approval and an extension of this file.

## Frozen Symbols

- BTCUSDT, ETHUSDT, SOLUSDT.
- Per-venue symbol-naming maps (data layer only):
  - Bitget: `BTCUSDT`, `ETHUSDT`, `SOLUSDT` (USDT-FUTURES).
  - Binance: `BTCUSDT`, `ETHUSDT`, `SOLUSDT` (USDT-M Futures).
  - OKX (deferred): `BTC-USDT-SWAP`, `ETH-USDT-SWAP`, `SOL-USDT-SWAP`.
- No symbol additions, no symbol substitutions, no per-venue symbol
  expansions. The analyzer's `FROZEN_SYMBOLS = ("BTCUSDT","ETHUSDT","SOLUSDT")`
  is the canonical key set.

## Timeframe

- 4H.
- No timeframe additions, no timeframe changes.

## Windows

Same locked windows as the single-venue C7 design lock, reused verbatim per
venue:

- **Development window:** `2023-12-17T16:00:00+00:00` to
  `2026-05-06T08:00:00+00:00`.
- **Expanded backward window:** `2022-01-01T00:00:00+00:00` to
  `2023-12-17T12:00:00+00:00`.
- **Direction:** `backward`.

No window changes. No per-venue window adjustments. Each venue must produce
evidence on the same locked windows.

## Frozen Detector and Gates

The C7 analyzer
(`research/signal_observation/setup_c_c7_expanded_validation.py`) is the
sole evaluator. No detector, gate, or analyzer-logic change is authorized
for any cross-venue evidence run. Specifically frozen:

- 40-bar primary lookback (20- and 60-bar sensitivity unchanged).
- Rebalance every 6 bars.
- Volatility proxy ATR(20) / close.
- Cost tiers (`optimistic = 2`, `moderate = 4`, `conservative = 6` bps per
  turnover unit). Moderate remains the primary cost scenario.
- Funding scenario in-gate: `high_cost = 0.0003` per 8H (intervals per
  rebalance = 3).
- Random baseline: seed `RANDOM_SEED + PRIMARY_LOOKBACK = 5443`, iterations
  `1000`, expanded intervals only.
- Five C7 gate conditions:
  1. expanded vt-post-cost-moderate > 0;
  2. expanded > random p75;
  3. funding-adjusted high_cost > 0;
  4. ≥ 2 of 3 symbols non-negative;
  5. combined-retention ratio ≥ 50%.

## Public-Data-Only Constraints

- Public unauthenticated endpoints only.
- No credentials, no API keys, no signed payloads, no account IDs, no
  secret-derived values in repo, docs, prompts, or chat.
- No private endpoints (account / order / position / withdraw / transfer /
  leverage / userDataStream / listenKey / openOrders / myTrades).
- No order, cancel, withdraw, transfer, set_leverage, live reconcile, or
  live execution calls of any kind.
- One approved public download per venue per window; no re-download after
  seeing analyzer results.

## Anti-Cherry-Picking Rules

- Locked bounds recorded at download time; record SHA256 of each new CSV
  and the data commit SHA.
- No boundary changes after seeing analyzer results.
- No symbol changes, no timeframe changes, no lookback / rebalance /
  cost / funding / random / gate changes between venues.
- Every authorized venue's evidence must be reported. A venue may be
  marked "deferred" or "blocked" with cause; venues must not be silently
  dropped because their result is inconvenient.
- Cross-venue PASS counts gate replication, not magnitude replication
  (see Interpretation Rules below).

## Interpretation Rules

- **Cross-venue PASS = gate replication, not magnitude replication.** A
  venue passes if and only if all five C7 gate conditions are independently
  satisfied on that venue's evidence. Cross-venue PASS does not require
  any venue's numeric magnitudes to match another venue's; it requires only
  that each venue independently satisfies the locked gate.
- **Binance dev-magnitude divergence must be recorded.** The Binance
  evidence run at `775d739` reports a development-window vt-post-cost-moderate
  ≈ 25% of the Bitget value at `c108197`. This is observational, not a
  gate violation. Any cross-venue decision record must surface it.
- **SOL concentration must be recorded per venue.** SOL share of the
  expanded headline differs across venues (~53% on Bitget, ~70% on
  Binance). This is observational, not a gate violation. Any cross-venue
  decision record must surface it.
- **No paper, runtime, trading, probe, or live readiness is implied** by
  any number of venue PASSes. Cross-venue both-PASS is research evidence
  only; promotion to any non-research lane remains gated by a separate
  explicit Human Owner decision recorded in repo docs.

## Current Evidence

- **Bitget:** decision `C7_PASS`. Artifact:
  `research/signal_observation/output/bitget/setup_c_c7_expanded_report.json`.
  Data commit: `16ae508`. Evidence commit: `c108197`. Post-C7 review record:
  `research/signal_observation/SETUP_C_C7_POST_REVIEW_DECISION.md`.
- **Binance:** decision `C7_PASS`. Artifact:
  `research/signal_observation/output/binance/setup_c_c7_expanded_report.json`.
  Data commit: `583e724`. Evidence commit: `775d739`.
- **OKX:** deferred. Reachability probe blocked by Cloudflare 1010 on the
  current host. No data download attempted. No evidence.

Cross-venue **gate replication state:** both Bitget and Binance
independently satisfy the locked C7 gate. OKX is deferred and not counted.

## Next Allowed Step

- **Cross-venue decision record** (parallel to
  `SETUP_C_C7_POST_REVIEW_DECISION.md`) covering Bitget + Binance both-PASS,
  the Binance dev-magnitude divergence, the SOL concentration delta, and
  the OKX-deferred reachability blocker. Owner-only research decision.
- **Recommended next research gate after the decision record:**
  - If OKX becomes accessible (e.g., move to a host that does not hit
    Cloudflare 1010 on `www.okx.com`): run OKX C7 evidence on the same
    locked windows and add it to the cross-venue both-PASS state. Owner-only.
  - Otherwise: a **direction-call agreement diagnostic** comparing
    per-rebalance direction sign across Bitget and Binance over the locked
    expanded window — observational only, no gate change, no readiness
    promotion. A diagnostic that asks whether the venues actually agree on
    direction calls, not just on aggregate headline. Owner-only.
- No paper, runtime, trading, probe, or live readiness step is authorized
  by this design lock or by any cross-venue PASS.

## What This Design Lock Does Not Authorize

- Paper trading. Live trading.
- Runtime or service wiring.
- Private exchange endpoints, credentials, signed payloads, API keys, or
  secret-derived values.
- Orders, cancels, set_leverage, withdraw, transfer, live reconcile, or
  live execution on any venue.
- Any form of readiness claim (paper / runtime / probe / trading / live).
- Parameter optimization, symbol additions, lookback changes, rebalance
  changes, timeframe changes, threshold changes, regime-filter
  introduction, or gate-criteria changes — on any venue.
- Re-download of expanded or dev data on any venue that already has locked
  data committed (Bitget `16ae508`, Binance `583e724`).
- Adding a new venue without a separate explicit owner approval and an
  extension of this file.
