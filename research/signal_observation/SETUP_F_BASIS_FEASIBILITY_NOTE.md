# Setup F — Basis / Cash-and-Carry Dislocation: Stage 1 Feasibility Note

Status: **FEASIBLE**
Date: 2026-06-13
Constitution stage: 1 (Feasibility only — no outcome metrics)
Governed by: docs/RESEARCH_CONSTITUTION.md v1.1

## 1. Hypothesis Summary (informal, pre-registration not yet written)

Spot-perpetual basis dislocations — episodes where the perp price trades
unusually far above or below spot price — may reflect transient financing
demand imbalances or hedging pressure. Because funding rates mechanically
correct basis toward zero (longs pay shorts when perp is at a premium, and
vice versa), extreme basis readings may mean-revert over hours-to-days.
This is the proposed mechanism; it has NOT been tested here. Stage 1 concerns
data availability only.

## 2. Data Path (verified against live endpoints, 2026-06-13)

All three endpoints are public (no API key, no paid subscription):

| Series | Endpoint | Auth required? | Verified live? |
|---|---|---|---|
| Spot 4H OHLCV | `api.binance.com/api/v3/klines?symbol=X&interval=4h` | None | YES |
| Perp 4H OHLCV | `fapi.binance.com/fapi/v1/klines?symbol=X&interval=4h` | None | YES |
| Funding rate (8h) | `fapi.binance.com/fapi/v1/fundingRate?symbol=X` | None | YES |

Max rows per request: 1000 (spot/funding), 1500 (futures klines). Pagination
via `startTime`/`endTime` works correctly. Response fields: OHLCV in standard
kline array format; funding rate with `fundingTime` (ms) and `fundingRate`.

Binance USDT-M perpetuals (`fapi`) and Binance spot (`api`) share timestamp
conventions and align cleanly on 4H open times.

## 3. Pilot Data Acquisition

Universe: BTCUSDT, ETHUSDT, SOLUSDT (Binance spot vs USDT-M perp)
Window: 2025-06-13 to 2026-06-13 (365 days)
Interval: 4H OHLCV (6 bars/day) + 8H funding rate (3 records/day)

### Per-Series Coverage

| Symbol | Series | Bars | Date range | Gaps | Quality |
|---|---|---|---|---|---|
| BTCUSDT | Spot | 2190 | 2025-06-13 to 2026-06-13 | 0 | PASS |
| BTCUSDT | Perp | 2190 | 2025-06-13 to 2026-06-13 | 0 | PASS |
| BTCUSDT | Funding | 1095 | 2025-06-13 to 2026-06-13 | 0 | PASS |
| ETHUSDT | Spot | 2190 | 2025-06-13 to 2026-06-13 | 0 | PASS |
| ETHUSDT | Perp | 2190 | 2025-06-13 to 2026-06-13 | 0 | PASS |
| ETHUSDT | Funding | 1095 | 2025-06-13 to 2026-06-13 | 0 | PASS |
| SOLUSDT | Spot | 2190 | 2025-06-13 to 2026-06-13 | 0 | PASS |
| SOLUSDT | Perp | 2190 | 2025-06-13 to 2026-06-13 | 0 | PASS |
| SOLUSDT | Funding | 1095 | 2025-06-13 to 2026-06-13 | 0 | PASS |

Quality criterion: < 5% of consecutive bar intervals deviate from 4H (or 8H
for funding) by more than 50%. All series: 0 gaps, 0.0% gap rate. ✓

### Dataset SHA-256 Hashes (binding this note to the exact pilot data)

| Symbol | Series | SHA-256 |
|---|---|---|
| BTCUSDT | spot | `fd2695f93a70292a8229bc584b34dc44fd572fac0a4901b5833081ab32d7d296` |
| BTCUSDT | perp | `bd81a3e39f2316411bcf3a4d66c8effb0327d53021da0f32d9e21a74790d7fed` |
| BTCUSDT | funding | `be410cd14b61128ebf293b31003a903a41d190b7cd6d9eeb61ae9403c63cd5d2` |
| ETHUSDT | spot | `09fdc4e816eb2c445810a51327b1de670cd0b88b3f1bd9e3c8a0e9bb02b5c13d` |
| ETHUSDT | perp | `99f6d6092d45ea91e2a8a5221b4f3dd39e7308778932a653ff2e344258192d20` |
| ETHUSDT | funding | `dad2d55574051cbfee191e0cd73ea85e3ff3229f7597479abf50e3c4be81b7ef` |
| SOLUSDT | spot | `b0da7225fe33730cefb4b0606806e4e5d798e2269ace5e31b3a61d622cd70b1f` |
| SOLUSDT | perp | `02d280c37d70e567f6ac1da50b3753710cec6945e7fcc6200c778c9ff3d2cd64` |
| SOLUSDT | funding | `cb00918920ae256f2fd3fb89d101cfb530a71a5b4ec6fede3e0b7f9345d15678` |

Data files: `research/signal_observation/data/setup_f/` (gitignored; not committed).
Metrics JSON: `research/signal_observation/data/setup_f/setup_f_feasibility_metrics.json`.

## 4. Basis Statistics (Stage 1 — counts and distribution only, NO forward returns)

Basis definition: `basis_i = perp_close_i / spot_close_i - 1`
(positive = perp premium, negative = perp discount relative to spot)

### Distribution (full pilot window, bps = basis_points × 10,000)

| Symbol | Mean | StDev | Min | Max | p10 | p90 | p95 |
|---|---|---|---|---|---|---|---|
| BTCUSDT | -4.52 | 1.18 | -8.68 | +5.52 | -5.80 | -3.29 | -2.63 |
| ETHUSDT | -4.63 | 1.29 | -25.41 | +8.32 | -5.99 | -3.34 | -2.81 |
| SOLUSDT | -5.24 | 2.60 | -45.98 | +11.05 | -7.47 | -3.15 | -2.16 |

Regime note: all three symbols show a persistently negative basis (perp
closes below spot) over the pilot window 2025-06-13 to 2026-06-13. This
likely reflects a bear-dominated or hedge-dominated period for perpetuals,
which is the relevant structural backdrop for any pre-registration.

SOL shows materially wider dispersion (stdev 2.60 bps vs ~1.2 bps for BTC/ETH)
and larger tail events (min -45.98 bps), suggesting more episodic dislocations.

### Dislocation Threshold Crossings (trailing-30d self-referential thresholds)

Trailing window: 180 bars (30 × 6 bars/day). Valid bars (full window): 2010.
Thresholds: p10 (discount extreme) and p90/p95 (premium extreme) of trailing
30d basis distribution.

| Symbol | p10 discount crossings | Rate | p90 premium crossings | Rate | p95 premium crossings | Rate |
|---|---|---|---|---|---|---|
| BTCUSDT | 228 | 11.3% | 207 | 10.3% | 106 | 5.3% |
| ETHUSDT | 217 | 10.8% | 212 | 10.5% | 112 | 5.6% |
| SOLUSDT | 219 | 10.9% | 240 | 11.9% | 145 | 7.2% |

Expected crossing rate under iid basis: 10% for p90, 5% for p95. Observed
rates are slightly above expected for all three symbols, most notably SOL p95
(7.2% vs expected 5%). This is consistent with autocorrelated basis behavior
(clustered dislocation episodes) rather than memoryless threshold exceedances.
No forward return analysis has been conducted; the above is count-only.

## 5. Feasibility Assessment

**Data availability: CONFIRMED.**
- Public endpoint, no auth, no paid plan.
- Can be downloaded via standard HTTP requests using already-demonstrated
  Binance downloader patterns (existing C7 infrastructure).
- Full alignment between spot and perp on 4H bars: 0 gaps in pilot.
- Funding rates (8H cadence, 1095 records/year) are also freely available
  and gap-free.

**Signal candidate density: ADEQUATE.**
- 2010 valid bars (full trailing window) per symbol in 365-day pilot.
- BTC + ETH + SOL combined: ~6030 valid bars.
- At 5% crossing rate (p95), ~301 events across 3 symbols in 365 days
  (~0.8 events/day/symbol). Sufficient for pre-registration minimum counts
  even on a 3-symbol discovery-only universe.

**History depth: ADEQUATE for 1-year pilot; potentially limitless.**
- Binance USDT-M futures launched 2019-09. Full spot history pre-dates this.
- A discovery/validation split over 2-3 years is feasible.
- Longer history requires the same paginated download, no additional access.

**Known limitations:**
1. Pilot window (2025-06-13 to 2026-06-13) is a single regime (persistently
   negative basis). A broader historical window is needed for pre-registration.
2. The basis measured here is a 4H bar-close ratio — intrabar extremes are not
   captured. If the signal needs intrabar precision, a higher-frequency series
   would be required.
3. Basis magnitude (mean ~4-5 bps) is in the same order as trading costs
   (8 bps moderate). The signal would need to trade on OHLCV price movements
   during the dislocation window, not the basis itself as a carry trade.

## 6. Potential Primary Signal Definition (informal sketch — NOT pre-registered)

This is a starting point for a future pre-registration. Nothing here is locked.

Candidate signal: **Basis-dislocation reversal** — when the spot-perp basis
crosses above or below a trailing-30d extreme threshold (e.g., p95 premium or
p5 discount), trade the underlying in the mean-reversion direction, using the
4H OHLCV price series for entry/exit rather than the basis itself.

Parameters to lock in pre-registration:
- Which threshold percentile (90th / 95th / 5th / 10th)
- Direction: premium-short / discount-long (requires mechanism validation)
- Stop and target (R-based, simcore compatible)
- Outcome window (e.g., 12 or 24 bars)
- Universe (3-symbol pilot or broader)
- Whether to use aligned funding data as a co-signal

This note does NOT constitute a pre-registration. Discovery requires:
(a) a locked pre-registration, (b) a held-out split, (c) owner authorization.

## 7. Verdict

**FEASIBLE** — public data path confirmed, quality PASS, adequate episode
density. A pre-registration may be drafted when the owner authorizes it.
Do NOT begin discovery or signal screening without a locked pre-registration
and separate owner authorization.
