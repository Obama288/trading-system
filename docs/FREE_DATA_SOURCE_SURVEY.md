# Free Data Source Survey — What the Free Frontier Actually Offers

Status: research note for owner, 2026-06-13. Web-survey of free crypto data
availability and quality, to inform Move B (finer free data) vs Move C (paid).
Companion to DATA_CLASS_DECISION_FRAMEWORK.md. Findings verified against
provider docs/pages on 2026-06-13.
Proposed location: `docs/FREE_DATA_SOURCE_SURVEY.md`

---

## 1. The single most useful finding

**Binance publishes free, downloadable historical FLAT FILES at
`data.binance.vision` — including aggTrades (tick-level) and 1m klines — with
no account and no API key, for spot, USD-M, and COIN-M futures.** This is a
qualitatively bigger free frontier than the rate-limited REST `/klines`
endpoint the project has used so far.

What this unlocks for free, that we have NOT yet used:
- **Tick-level aggTrades** (every trade: price, qty, time, buyer-maker flag) —
  this is real microstructure: trade flow, buy/sell imbalance, realized
  intrabar path. Far richer than 4H bars.
- **1m klines** across full history — intrabar precision for basis, volatility,
  and any short-horizon effect that 4H bar-close washes out.
- **Futures `metrics`** (USD-M) — includes open interest and long/short ratios
  historically, free. This is the OI series the funding/basis families wanted
  but didn't have.

Tooling exists: the `binance-public-data` repo (official) and community
packages download and unzip these dumps in a few lines. No paid tier.

Important quality caveat to verify before relying on it: the flat-file archive
is daily/monthly zip dumps with a ~1-day publish lag, and historical depth
varies by symbol/instrument (some series start only when the instrument
launched). A quality pass (our simcore validator) must run on any series before
it's used, exactly as for Setup E/F.

## 2. What is NOT free anywhere (the real paid wall)

- **Historical L2/L3 order-book snapshots** (depth over time). NOT on
  data.binance.vision. The free REST `depth` endpoint returns only the CURRENT
  book. Historical order-book depth requires a paid vendor: Tardis.dev,
  CoinAPI flat files, Crypto Lake, CoinGlass, CoinGecko enterprise. All paid.
  - Crypto Lake offers a small anonymous SAMPLE (BTC-USDT book) for free via
    `lakeapi.use_sample_data` — enough to prototype code, not to backtest.
- **Historical options positioning by strike** (Setup G's need). Deribit free
  API gives current snapshots only; history is paid. Confirmed dead-free.
- **Event-level liquidation streams with full history.** Free sources
  (Coinalyze used in E) are short/coarse; richer is paid (CoinGlass $29-699/mo).

## 3. Free frontier, ranked by richness (all usable without payment)

| Source | What | Granularity | History | Quality note |
|---|---|---|---|---|
| data.binance.vision flat files | aggTrades, 1m klines, OI metrics | tick / 1m / per-instrument | full per instrument | daily dumps, ~1d lag; per-symbol start dates vary |
| Binance REST /klines, /aggTrades | same, live | tick / 1m+ | full, paginated | rate-limited (weight); slower for bulk |
| Binance spot+perp (already used) | OHLCV, funding | 4H+ | full | proven in Setup F |
| Crypto Lake sample | L2 book SAMPLE | tick | tiny sample | prototype-only, not backtestable |
| Deribit public | options snapshots | current only | none historical | kills Setup G free path |

## 4. What this means for the A/B/C/D moves

- **Move B is bigger and cheaper than I assumed.** "Go finer on free data" is
  not just 1m candles — it's tick-level aggTrades + historical OI, free, full
  history, for the exact majors we already handle. The microstructure data
  class is partly open for free on Binance. This materially raises Move B's
  expected value.
- **Move C's unique selling point shrinks to order-book depth specifically.**
  The argument for paying was "richer, less-picked-over data." But trade-flow
  and OI — much of that richness — turn out to be free via flat files. The ONLY
  thing genuinely behind the paywall is historical L2/L3 depth. So Move C
  becomes a narrow question: "is order-book depth specifically worth paying
  for, given trade-flow and OI are free?" — not a broad "should we buy better
  data."
- **The cost wall still applies and still bites harder at fine timescales.**
  Tick/1m strategies trade more often; the 16 bps round-trip that sank Setup F
  is even more punishing intraday. Any Move B candidate must clear the cost
  test BEFORE locking — the effect per trade must plausibly exceed round-trip
  cost after realistic fills. This is the discipline that should kill weak
  candidates early.

## 5. Recommendation update

The free survey sharpens the framework's recommendation:

1. **Move B is now the strongest next step**, not just a parallel thought.
   Concretely: build a free flat-file ingester for data.binance.vision
   (aggTrades + 1m + OI metrics), run the quality validator, and let it feed
   candidate ideas that use microstructure/OI — a data class the project has
   never actually tested. Apply the cost test up front.
2. **Move A (regime-gated Setup C) remains the cheapest single experiment** and
   can run first or alongside — it needs no new data at all.
3. **Move C narrows to "order-book depth only."** Defer it until a Move B
   candidate specifically demands depth (e.g. a queue-position or
   liquidity-imbalance signal that trade-flow alone can't capture). Then, and
   only then, treat a paid trial as a budgeted experiment with a kill date.
4. **Move D (stop/harden) stays the honorable floor** if Move A and a couple of
   Move B candidates also fail the cost test or the gates.

## 6. One caution on the survey itself

Free flat files are a real, current finding, but "available" is not "good." The
project's own discipline applies: run the quality validator, hash the files
into any pre-registration, and do not let the richness of tick data tempt a
return to price-action-style fishing. Tick data is a finer lens on the same
question — "who is forced to trade and why" — not a license to data-mine. The
mechanism-first rule (constitution 2.1, BOUNDARIES hard research boundaries)
governs here exactly as before.
