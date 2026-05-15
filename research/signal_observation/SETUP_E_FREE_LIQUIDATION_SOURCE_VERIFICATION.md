# Setup E Free Liquidation Source Verification

## 1. Purpose

Verify whether a free/public, machine-readable, historical liquidation-data
path exists that could support a later bounded non-evidence Setup E EXPLORE
pass on liquidation cascades.

This is source research only. No EXPLORE run, market-data download, API
retrieval, implementation, or readiness claim is authorized by this note.

## 2. Current Setup E State

- Liquidation Cascades triage advanced to a hypothesis note.
- Setup E hypothesis note exists.
- Setup E remains hypothesis-note only.
- The prior liquidation data feasibility note recommended
  `HOLD_FOR_SOURCE_VERIFICATION`.
- No Pre-E1 gate, EXPLORE run, data work, implementation, or readiness
  promotion is authorized.

## 3. Verification Question

Is there a free/public historical liquidation source suitable for a later retro
EXPLORE pass on liquidation cascades, without paid vendor dependency and
without silently changing the candidate into a proxy-only idea?

Scope: Setup E EXPLORE suitability only. Findings may inform other
liquidation-family ideas later, but this is not a universal survey of every
liquidation-data use case.

## 4. Sources Checked

| Source | Type | Historical? | Free? | Machine-readable? | Suitability |
|---|---|---:|---:|---:|---|
| ErcinDedeoglu/crypto-market-data GitHub | Public GitHub dataset | Yes, visible BTC daily liquidation JSON from 2022-12-03 to 2026-03-29 in checked file | Yes | Yes, JSON | Suitable only for a coarse BTC daily aggregate EXPLORE; not event-level and not multi-asset in the visible liquidation files |
| Comparable public GitHub repos | Public GitHub datasets | No stronger comparable free historical CEX/perp liquidation event dataset confirmed in this pass | Unclear | Unclear | No stronger path confirmed |
| Binance USD-M Futures REST docs | Official exchange docs | No public historical liquidation backfill confirmed | No public backfill | No public backfill | Not suitable as public historical source |
| Binance `GET /fapi/v1/forceOrders` | Official signed USER_DATA endpoint | User-only force orders; only past 90 days | Requires signed user data access | Yes, but private/user-scoped | Not suitable for public market-wide historical EXPLORE |
| Binance `liquidationOrders` v1/v2 claims | Claimed REST endpoints | Not confirmed in official USD-M docs | No | No | Unsupported/falsified for this task |
| Binance liquidation WebSocket streams | Official live streams | Live snapshots only | Public live stream | Yes while subscribed | Not historical backfill; not suitable alone |
| Kaggle BTC Historical, Leverage, Liquidations, Order Data | Downloadable public dataset | About 3 months from October 2024, BTC/Hyperliquid | Appears free; Kaggle account/download flow applies | Likely yes | Potential narrow orientation source; short span and single asset limit Setup E usefulness |
| Hyperliquid official historical data | Official/public archive docs | Raw historical market/node/fill data exists, but official docs do not expose a simple historical liquidation event table | Requester pays transfer costs for S3 examples | Yes for raw archives | Possible reconstruction path, but not a low-friction free liquidation-event source |
| Hyperliquid official liquidation docs | Official mechanism docs | Mechanism only | Yes | Documentation only | Useful mechanism context, not data source |
| The Graph Hyperliquid market liquidations | Public third-party API docs | Yes, event rows with `start_time`/`end_time` filters | Requires bearer token; plan restricted | Yes | Promising third-party Hyperliquid path, but token/API dependency means it is not the cleanest free/public source for this note |
| Dune / DeFi liquidation datasets | On-chain analytics / DeFi lending | Yes for lending protocol liquidation events | Often browsable/queryable depending plan | Yes in Dune tables | Different candidate family: DeFi lending liquidations, not direct CEX/perp liquidation-cascade source as Setup E is formulated |
| CoinGlass | Dashboard/API vendor | Historical liquidation API exists; heatmaps/maps also exist | API key/pricing dependency not ruled out; dashboards are visual | API yes; dashboards no | Useful vendor candidate, but not a free reproducible path for this task |
| Coinalyze | API vendor | Historical liquidation endpoint exists; intraday retention limited to 1500-2000 points, daily retained | API key required; docs present as free API | Yes | Potential free API path after explicit authorization, but not a no-key public dataset |
| TradingView liquidation heatmap scripts | Charting/community indicators | Proxy or visual indicator history, not source event history | Some scripts free | Code/visual, not event data | Proxy/heatmap only; not sufficient for reproducible Setup E EXPLORE |

Source references checked:

- ErcinDedeoglu GitHub dataset:
  https://github.com/ErcinDedeoglu/crypto-market-data
- ErcinDedeoglu BTC long liquidations USD JSON:
  https://github.com/ErcinDedeoglu/crypto-market-data/blob/main/data/daily/btc_long_liquidations_usd.json
- Binance user's force orders:
  https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Users-Force-Orders
- Binance liquidation order stream:
  https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Liquidation-Order-Streams
- Binance all-market liquidation order stream:
  https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Liquidation-Order-Streams
- Kaggle BTC historical leverage/liquidations/order data:
  https://www.kaggle.com/datasets/ollibolli/btc-historical-leverage-liquidations-order-data
- Hyperliquid historical data:
  https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
- Hyperliquid liquidations:
  https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations
- The Graph Hyperliquid market liquidations:
  https://thegraph.com/docs/en/token-api/hyperliquid-markets/liquidations/
- Dune lending supply docs:
  https://docs.dune.com/data-catalog/curated/lending/supply
- CoinGlass aggregated liquidation history:
  https://docs.coinglass.com/reference/aggregated-liquidation-history
- Coinalyze API docs:
  https://api.coinalyze.net/v1/doc/
- TradingView liquidation heatmap proxy example:
  https://www.tradingview.com/script/d2LdGqQO-Liquidation-Heatmap-Proxy-victhoreb/

## 5. Key Findings

Confirmed useful paths:

- A public GitHub dataset path exists for BTC long/short liquidations in daily
  JSON files. The visible checked file is BTC long liquidations USD with daily
  granularity, first data date 2022-12-03 and last data date 2026-03-29. The
  repository README lists BTC long liquidations, BTC long liquidations USD, BTC
  short liquidations, and BTC short liquidations USD. The README presents the
  license as CC BY 4.0.
- Kaggle has at least one free-looking downloadable BTC/Hyperliquid dataset
  with liquidations, approximately 3 months from October 2024, MIT license
  visible. It is narrow but relevant as a possible orientation source.
- Coinalyze documents a `liquidation-history` endpoint with 1 minute through
  daily intervals. Its docs say intraday data retains only 1500-2000 datapoints
  while daily data is not deleted. This is machine-readable but API-key based.

Rejected or unsupported claims:

- Official Binance USD-M Futures docs do not confirm public REST endpoints
  named `/fapi/v1/liquidationOrders` or `/fapi/v2/liquidationOrders`.
- The official Binance historical-looking liquidation REST endpoint found is
  `GET /fapi/v1/forceOrders`, but it is a signed USER_DATA endpoint for the
  user's own force orders and only supports querying the past 90 days. It is
  not a public market-wide historical liquidation backfill.
- Binance WebSocket liquidation streams are live snapshot streams. They push
  only the largest liquidation order per symbol within a 1000 ms interval when
  events occur. They do not provide historical backfill.

Dashboard-only or vendor/API paths:

- CoinGlass documents historical liquidation API endpoints, but practical use
  depends on API-key/vendor terms. Its liquidation heatmap/map UI is not enough
  for reproducible Setup E EXPLORE because visual dashboard access is not a
  machine-readable historical dataset.
- The Graph documents a Hyperliquid liquidation endpoint with event rows and
  time filters, but it requires a bearer token and has plan-restricted limits.
  It is promising, but not a clean no-key public dataset.
- TradingView community liquidation heatmap scripts are proxies or visual
  indicators. They do not substitute for liquidation event or aggregate history.

Proxy or different-market paths:

- Dune and DeFi liquidation datasets commonly concern lending protocol
  liquidations such as Aave, Compound, MakerDAO, and other collateralized debt
  systems. That is a different market mechanism from current Setup E as
  formulated around perp/CEX-style liquidation cascades.
- Heatmaps, liquidation maps, and open-interest-derived levels can be useful
  later, but they are proxy candidates. They must not be silently substituted
  for historical liquidation event or aggregate data.

## 6. Verification Outcome

FREE_HISTORICAL_SOURCE_FOUND

The found path is narrow. It supports only a bounded, coarse, non-evidence
EXPLORE framing unless a later owner-approved source-selection step explicitly
chooses a richer API or dataset. It does not prove Setup E quality and does not
authorize EXPLORE.

## 7. Recommendation

For a later Setup E EXPLORE source-selection decision, the strongest no-paid,
no-API starting path is:

`ErcinDedeoglu/crypto-market-data` BTC daily long/short liquidation JSON.

Why it is strongest relative to alternatives:

- It is public GitHub-hosted and directly machine-readable.
- It has visible historical coverage over multiple years for BTC in the
  checked long-liquidation USD file.
- It avoids paid vendor dependency, private exchange endpoints, signed user
  data, and live-stream capture requirements.
- It is closer to actual liquidation aggregates than heatmap/proxy paths.

Required caveat for any later EXPLORE authorization:

- The path is BTC-only in the visible liquidation files and daily aggregate,
  not event-level or intraday. A later EXPLORE must be explicitly framed as a
  coarse BTC daily liquidation-cluster sanity check. If the owner wants
  intraday or event-level Setup E, Coinalyze, The Graph Hyperliquid, Kaggle
  Hyperliquid, or another richer source would need a separate source-selection
  decision before any retrieval.

## 8. What This Does Not Authorize

- no EXPLORE run
- no market-data download
- no API retrieval
- no paid subscription decision
- no proxy substitution
- no implementation
- no readiness claims

## 9. Next Allowed Step

A docs-only owner/source-selection decision may choose whether the next Setup E
step should be:

- a bounded non-evidence BTC daily aggregate EXPLORE design using the public
  GitHub JSON path;
- a narrower source check for an intraday/event-level free path; or
- parking Setup E until a stronger liquidation-history source is approved.
