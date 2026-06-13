# Setup G — Options Expiry / Dealer Hedging: Stage 1 Feasibility Note

Status: **NEEDS-PAID-DATA**
Date: 2026-06-13
Constitution stage: 1 (Feasibility only — no outcome metrics)
Governed by: docs/RESEARCH_CONSTITUTION.md v1.1

## 1. Hypothesis Summary (informal, pre-registration not yet written)

Near options expiry dates, dealers who are net short options (the typical
post-GFC market-maker position) accumulate delta hedging inventory that
concentrates around the "max pain" strike — the settlement price that
minimises payouts to option holders. As expiry approaches, dealer hedging
flow may pin the underlying near max pain, then release sharply after
expiry. This gamma/delta hedging dynamic could produce predictable price
behavior in the underlying (BTC, ETH) around monthly expiry windows.

Testing this mechanism requires knowing WHERE the open interest concentration
was at specific points in time (days/hours before expiry), not just the
current snapshot. Stage 1 concerns only whether that historical OI data
is publicly available for free.

## 2. Data Source Investigated

Deribit — the dominant venue for BTC/ETH crypto options. Public API:
`https://www.deribit.com/api/v2/public/`

All endpoint tests run on 2026-06-13 against live Deribit API.
No authentication used. No data files written or committed.

## 3. What IS Available Free / Public

### 3a. Current instrument list and expiry calendar

Endpoint: `get_instruments?currency=BTC&kind=option&expired=false`
- Returns all active option contracts (strike, expiry, option_type, instrument_name)
- **952 active BTC options** as of 2026-06-13 (12 unique expiry dates)
- **750 active ETH options** confirmed
- Expiry dates range from weekly to quarterly (up to 2026-07-31 visible in sample)
- Available: YES, free, real-time. History: NO (only active instruments).

### 3b. Current OI by instrument (strike x expiry)

Endpoint: `get_book_summary_by_currency?currency=BTC&kind=option`
- Returns snapshot for all 952 instruments in a single call
- Fields include: `instrument_name`, `open_interest`, `volume`, `mark_iv`,
  `underlying_price`, `bid_price`, `ask_price`
- This is a **current point-in-time snapshot only** — not historical.
- Available: YES, free, real-time. History: NO.

### 3c. OHLCV for individual option instruments (including expired)

Endpoint: `get_tradingview_chart_data?instrument_name=X&start_timestamp=...&end_timestamp=...&resolution=1D`
- Tested for BTC-27DEC24-100000-C (expired Dec 2024): returned **28 daily bars**
  (from 2024-11-30 through expiry date). Status: "ok".
- This is the positive surprise: price OHLCV for individual option contracts
  is available historically for expired instruments.
- Available: YES, free. Confirmed working for expired options.
- Limitation: OHLCV price series, NOT OI series. Cannot reconstruct OI
  evolution from OHLCV.

### 3d. Historical implied volatility (index level, not strike-specific)

Endpoint: `get_historical_volatility?currency=BTC`
- Returns **384 hourly data points spanning approximately 16 days**
  (2026-05-28 to 2026-06-13 in test run).
- Index-level vol only — no strike-by-strike IV surface history.
- Available: YES, free. Rolling ~16-day window only.

### 3e. Settlement / delivery prices (past expiry dates)

Endpoint: `get_delivery_prices?index_name=btc_usd&count=N`
- Returns per-expiry settlement prices (e.g., 2026-06-12: 62970.32).
- Fields: `date`, `delivery_price` only — NOT OI by strike.
- Useful for knowing WHAT the settlement price was, NOT for reconstructing
  where OI concentration was before expiry (which is what max pain requires).
- Available: YES, free. No OI breakdown.

## 4. What is NOT Available Free / Public

### 4a. Historical OI by strike at past dates — CORE BLOCKER

There is no Deribit public endpoint that returns OI by strike as it was on
a historical date. The only OI available is the current real-time snapshot.

A max pain calculation requires: for each expiry event, the OI at each
strike as of N hours before settlement. This snapshot data is NOT in the
free public API.

### 4b. Historical trades for expired instruments — inconsistent

Endpoint `get_last_trades_by_instrument_and_time` returned **0 trades**
for the Dec 2024 window of BTC-27DEC24-100000-C, despite OHLCV data
existing for the same instrument and period. Trade-level history for
expired instruments is not reliably available via the free API.

### 4c. Historical IV surface (strike-by-strike)

No endpoint for per-strike IV at past dates. `get_historical_volatility`
is index-level only and covers a rolling ~16-day window.

## 5. Feasibility Assessment

### What the mechanism requires

To backtest a dealer gamma / max pain signal, the minimum data needed is:
1. OI by strike for each instrument as of N days before each expiry date
   (to compute max pain at the time of the trade, not retroactively).
2. Price series (OHLCV) for the underlying around expiry.

Item 2 is available via standard Binance OHLCV (same as Setup F).
Item 1 is NOT available from Deribit's free public API.

### Free path assessment

| Data item | Free? | Available? | Notes |
|---|---|---|---|
| Expiry calendar (active) | YES | YES | Real-time only |
| Current OI by strike | YES | YES | Real-time snapshot only |
| Historical OI snapshots | NO | NO | Core blocker |
| OHLCV for individual strikes | YES | YES | Confirmed for expired options |
| Settlement prices | YES | YES | Per-expiry, no strike breakdown |
| Historical IV surface | NO | Partial | Only 16-day rolling window |

**Conclusion: historical OI snapshots — the necessary input for max pain
computation at the time of the trade — are not in the free public API.**

### Paid data alternatives

Several commercial data providers offer historical Deribit OI snapshots:
- Amberdata: options analytics with OI history
- Laevitas: Deribit-specific analytics platform
- Kaiko: institutional-grade crypto market data

None have been verified or priced. This note does not constitute a
recommendation to subscribe to any of these services.

### Forward accumulation path (self-collected)

The free API allows collecting a real-time OI snapshot on demand. If
collection were started now (one snapshot per hour or per day), a usable
historical OI dataset could be built after several months of accumulation.

This path is:
- Technically feasible (no auth required, lightweight request)
- But would require 3-6 months minimum before a discovery run is meaningful
- Out of scope for the current research calendar; noted for completeness

## 6. Verdict

**NEEDS-PAID-DATA**

The mechanism (options expiry / dealer gamma hedging) is conceptually sound
and the underlying price data path is confirmed free (Binance OHLCV). The
blocking gap is historical OI by strike, which is required to compute max
pain at the time of the trade and is not available from Deribit's free
public API.

Options to proceed (all require separate owner decision):
1. Subscribe to a paid data provider with historical Deribit OI (Amberdata,
   Laevitas, or equivalent).
2. Begin forward OI snapshot collection now and revisit in 3-6 months.
3. Park this candidate and direct research budget elsewhere.

Do NOT begin discovery or pre-registration until a historical OI data path
is confirmed and the owner authorizes it.
