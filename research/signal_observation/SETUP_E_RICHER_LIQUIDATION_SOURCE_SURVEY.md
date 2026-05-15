# Setup E Richer Liquidation Source Survey

## Purpose

Survey whether a richer free or genuinely low-friction liquidation-data path
exists that could support a more mechanism-aligned future Setup E EXPLORE after
the BTC daily coarse liquidation EXPLORE returned `EXPLORE_WEAK`.

This is source research only. It does not run EXPLORE, download datasets,
retrieve market data through APIs, implement anything, or alter Setup E status.

## Current Setup E State

- Setup E hypothesis note exists.
- Free source verification found a BTC daily GitHub path.
- BTC daily coarse EXPLORE completed off-repo with result `EXPLORE_WEAK`.
- That result is non-evidence / non-validation and does not disprove the
  intraday liquidation-cascade hypothesis.
- The unresolved question is whether a richer, more mechanism-aligned source
  path exists.

## Survey Question

Is there a richer source path, better aligned with the Setup E
liquidation-cascade mechanism, that is free or genuinely low-friction enough to
justify a later owner-approved EXPLORE pass?

## Target Source Properties

- multi-asset;
- finer than daily preferred;
- directional long/short split;
- historical depth ideally at least 18 months;
- machine-readable;
- reproducible;
- free or genuinely low-friction for research use.

## Sources Surveyed

| Source | Asset coverage | Granularity | Historical depth | Long/short split? | Machine-readable? | Access friction | Suitability for future Setup E EXPLORE |
|---|---|---|---|---|---|---|---|
| Coinalyze liquidation history API | Supported futures markets; docs examples include perpetual symbols and max 20 symbols/request | 1min, 5min, 15min, 30min, 1h, 2h, 4h, 6h, 12h, daily | Daily history not deleted; intraday keeps only 1500-2000 datapoints | Yes, response fields `l` and `s` | Yes, JSON API | Free API key signup; 40 calls/min; owner approval needed before retrieval | Strongest free / low-friction first candidate; multi-asset and directional, but intraday history is rolling and may not reach 18 months below 12h/daily |
| The Graph Hyperliquid market liquidations | Hyperliquid perps; filter by coin, including core perps such as BTC | Event rows with timestamps; page/limit and time filters | Historical depth not confirmed in docs checked | Yes via `direction` / `liquidation_kind` | Yes, JSON API | Bearer token required; plan-restricted limits | Strong mechanism fit for Hyperliquid event-level EXPLORE, but access/depth conditions need owner-approved narrow check before retrieval |
| Hyperliquid official historical data | Hyperliquid market and node data; per-coin raw fills/book/state paths | Raw fills / blocks; potentially event-level after reconstruction | S3 archives exist, updates monthly, data may be missing; requester pays transfer costs | Liquidation reconstruction possible from fills / state, not a simple ready table | Yes, raw archive formats | Advanced; requester-pays S3; reconstruction work | Mechanism-aligned but not low-friction enough for the next cheap EXPLORE source unless owner approves a reconstruction/data-engineering path |
| hyperliquid-dex/historical_data GitHub | Hyperliquid; public repo includes `liquidations.csv` | CSV event-like file | Visible file is only 63 lines; license/depth unclear | Likely liquidation rows, but schema/depth not sufficient from docs view | Yes, CSV | Public GitHub | Too small/unclear to replace a richer source; useful clue only |
| Kaggle BTC Historical, Leverage, Liquidations, Order Data | BTC / Hyperliquid only | Dataset appears event/order-like | About 3 months from October 2024 | Likely liquidation labels, but not verified by download | Downloadable dataset | Kaggle account/download flow | More detailed than BTC daily but still BTC-only and short; partial orientation source, not enough for multi-asset richer EXPLORE |
| CoinGlass aggregated liquidation API | Multiple exchanges and coins | 1m through 1w intervals | Historical endpoint documented | Yes, long and short aggregate history | Yes, JSON API | Login/API/pricing dependency; not confirmed free for this use | Strong data product but not a free/low-friction source path for this task |
| CandleFeed aggregated liquidation API | BTC, ETH, SOL and more; Binance/Bybit/OKX/Hyperliquid by tier | 4h, 6h, 8h, 12h, 1d aggregated; tick-level March 2026+ | Aggregated history 2019+ for major symbols, but Builder tier or higher required | Yes, long/short USD fields | Yes, JSON/CSV API | Free tier excludes liquidations; Builder tier starts paid | Good low-cost vendor candidate, but using it would be a paid subscription decision, not authorized here |
| Kwery | BTC, ETH, SOL, XRP across Binance futures and Hyperliquid among other venues | 15m, 1h, 4h, 24h on free; paid tiers add more | Free 14 days; Pro 60 days; Business 90 days | Binance force-order liquidations have side/qty/price/USD value | Yes, REST API | Free key but very short retention for this task | Too short for the desired historical EXPLORE despite useful schema |
| PurrData HyperLiquid Liquidations | Hyperliquid perpetuals; sample includes BTC, ETH, SOL | Event stream and hourly/daily CSV/Parquet partitions claimed | Historical backfills claimed, depth/pricing unclear | Yes, side/size/price/timestamp claimed | API/WebSocket/CSV/Parquet claimed | Early access / waitlist / plan limits | Promising but not currently reproducible enough to choose |
| PanicShell / dashboards / heatmaps | BTC, ETH, SOL dashboard views | Visual bars/feed | Dashboard history only | Visual long/short displays | Not enough for reproducible data | Dashboard UI | Rejected as direct source; visual UI is not a reproducible EXPLORE data path |
| DeFi lending liquidation datasets | Aave/Compound/Maker-style lending protocols | On-chain event tables | Often historical | Different liquidation semantics | Often machine-readable | Varies | Changes the mechanism too much; different candidate family, not direct Setup E source |

References checked:

- Coinalyze API docs: https://api.coinalyze.net/v1/doc/
- The Graph Hyperliquid market liquidations:
  https://thegraph.com/docs/en/token-api/hyperliquid-markets/liquidations/
- Hyperliquid historical data:
  https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
- Hyperliquid liquidation mechanism:
  https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations
- Hyperliquid public historical data GitHub:
  https://github.com/hyperliquid-dex/historical_data
- Kaggle BTC / Hyperliquid liquidation dataset:
  https://www.kaggle.com/datasets/ollibolli/btc-historical-leverage-liquidations-order-data
- CoinGlass aggregated liquidation history:
  https://docs.coinglass.com/reference/aggregated-liquidation-history
- CandleFeed API docs: https://candlefeed.ai/docs/
- Kwery API/product docs: https://kwery.xyz/
- PurrData HyperLiquid liquidations: https://www.purrdata.io/
- PanicShell dashboard: https://www.panicshell.xyz/

## Key Findings

Strongest candidate paths:

- Coinalyze is the strongest free / low-friction first candidate. It has a
  documented liquidation-history endpoint, multiple intervals from 1 minute to
  daily, directional long/short fields, JSON output, max 20 symbols per request,
  and free API-key access. The major caveat is retention: intraday history is
  only 1500-2000 datapoints, while daily history is retained. This means a
  future EXPLORE must choose between shorter finer-granularity history or
  longer coarser history.
- The Graph Hyperliquid market-liquidations endpoint is the strongest
  mechanism-aligned event-level candidate. It returns one row per liquidation
  event, with coin, direction, kind, notional, fill price, mark price, method,
  time filters, pagination, and JSON output. The unresolved condition is access:
  it requires a bearer token and plan-restricted limits, and the documentation
  checked did not prove enough free historical depth for the target window.

Weaker or partial paths:

- Hyperliquid official historical data is transparent and mechanism-aligned,
  but the official archive is an advanced raw-data path. It may require
  requester-pays S3 transfer and reconstruction from fills/blocks rather than a
  simple liquidation-history table.
- Kaggle's BTC / Hyperliquid dataset appears more detailed than the prior BTC
  daily aggregates, but it is BTC-only and about 3 months, so it does not solve
  the multi-asset / historical-depth need.
- CandleFeed has an attractive schema for aggregated liquidations back to 2019
  across major symbols, but liquidations require paid Builder tier or higher.
  That makes it a vendor/subscription decision rather than a free source path.
- Kwery is low-friction and covers BTC/ETH/SOL/XRP with liquidation flow, but
  free retention is only 14 days and paid retention appears capped at 90 days.
  That is too short for the desired richer historical EXPLORE.

Rejected paths:

- CoinGlass is a strong underlying data product but was not treated as an
  acceptable free/low-friction source because API access appears tied to login,
  credentials, and pricing.
- Dashboard-only or heatmap-only sources are not acceptable because visual UI
  access is not a reproducible machine-readable EXPLORE path.
- Public GitHub liquidation datasets stronger than the already verified BTC
  daily JSON path were not confirmed, except for small/unclear Hyperliquid CSV
  clues that are not sufficient by themselves.

Paths that change the mechanism too much:

- DeFi lending liquidations are real liquidation data, but they concern
  collateralized lending protocols rather than perp/CEX-style forced flow.
  They belong to a different candidate family/question unless Setup E is
  explicitly reformulated.
- Proxy liquidation maps, price-level heatmaps, open-interest-derived levels,
  or dashboard-derived signals must not be silently substituted for historical
  long/short liquidation data.

## Survey Outcome

`RICHER_SOURCE_PATH_FOUND`

## Recommendation

The strongest path for a future bounded Setup E EXPLORE is:

`Coinalyze liquidation-history API`

Why it is the best first candidate:

- It is free with an API key, rather than obviously paid-only.
- It is machine-readable and documented.
- It supports multiple futures symbols, so BTC can be expanded to ETH, SOL, and
  other liquid perpetuals if supported-market lookup confirms symbols.
- It provides directional long/short liquidation fields.
- It supports fixed intervals down to 1 minute, while also offering daily
  history that is not deleted.

Required owner-approved choices before retrieval:

- authorize API-key use and retrieval;
- choose symbols and venues;
- choose the fixed interval knowing the retention tradeoff:
  short finer-granularity history, or longer coarser history;
- define an off-repo EXPLORE script/output location;
- reaffirm discovery-contamination rules for all retrieved data.

Secondary candidate:

- If the owner wants event-level Hyperliquid-only liquidation data instead of a
  multi-venue aggregate source, run a narrow access/depth check for The Graph
  Hyperliquid market liquidations before retrieval. That check should verify
  free-token availability, plan limits, historical depth, and whether BTC/ETH/SOL
  event history can be paginated reproducibly.

## What This Does Not Authorize

- no EXPLORE run
- no data download
- no API retrieval
- no paid subscription decision
- no proxy substitution
- no implementation
- no readiness claims

## Next Allowed Step

A docs-only owner decision may choose one of:

- authorize a bounded off-repo Coinalyze source-selection / EXPLORE design;
- authorize a narrow The Graph Hyperliquid access/depth check;
- park Setup E rather than forcing weak sourcing.
