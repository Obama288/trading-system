# H1 Phase A Transport Result - 2026-07-17

Status: PASS / TRANSPORT AND CURRENT SCHEMA ONLY

Acquisition ID: `h1_phase_a_transport_20260717_v1`
Implementation commit: `39ba91f`
Lock commit: `25dd4eb`

## Verdict

All four frozen unauthenticated public funding-history endpoints returned HTTP
200 and passed the locked contract-identity, envelope, timestamp, duplicate,
size, redirect, and no-leak structural checks.

This result does not establish historical coverage, funding-sign semantics,
contract equivalence, venue eligibility, selected pair, Phase B readiness, or
edge. No funding, price, spread, return, or PnL value was printed or recorded in
this report.

## Structural Results

| Venue | Contract | Rows | Returned UTC coverage | Bytes | Result |
|---|---|---:|---|---:|---|
| Binance | BTCUSDT | 500 | 2026-01-31T08:00:00.001Z to 2026-07-16T16:00:00.002Z | 52,704 | VALID |
| Bitget | BTCUSDT | 100 | 2026-06-13T16:00:00Z to 2026-07-16T16:00:00Z | 7,642 | VALID |
| Bybit | BTCUSDT | 200 | 2026-05-11T08:00:00Z to 2026-07-16T16:00:00Z | 17,486 | VALID |
| OKX | BTC-USDT-SWAP | 100 | 2026-06-13T16:00:00Z to 2026-07-16T16:00:00Z | 19,586 | VALID |

The latest-page ranges above are transport metadata, not the full available
history. They are insufficient to prove the intended 2023-2026 windows.

## Artifact Binding

Raw and metadata files remain under the ignored local root
`research/signal_observation/data/h1/phase_a/h1_phase_a_transport_20260717_v1/`.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| metadata.json | 1,315 | `d7c539694135beced638e6d4279cecd73ad3fca7e025265c4b06a8cba067f513` |
| raw/binance.json | 52,704 | `916c58185da077055da19b71ada07e552220c6fc128441d3ab2a3f89375bd94b` |
| raw/bitget.json | 7,642 | `33f6d5aa61f22aa0a4beb3a2ffeeedd84ae0057904045ac647114755242bf08f` |
| raw/bybit.json | 17,486 | `6f8e5b50ffafdde5a44a161598f48c960548b23571178951f2c353663904b903` |
| raw/okx.json | 19,586 | `d65a84d185fa7bc81b32c6b70b76a2fc9a0637cdcf3a88253929e35becf566f4` |

## Next Gate

Commit a separate bounded coverage/pagination lock before another network call.
That lock must define exact UTC windows, source-specific cursor semantics,
maximum pages and bytes, and metadata-only completion criteria. Phase B and
outcome inspection remain unauthorized.
