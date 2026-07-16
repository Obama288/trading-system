# H1 Phase A Historical Funding Coverage Result - 2026-07-17

Status: PARK H1 / DATA FEASIBILITY / NO OUTCOME INSPECTION

Acquisition ID: `h1_phase_a_coverage_20260717_v1`
Implementation commit: `620edab`
Lock commit: `d5f1861`

## Verdict

The locked metadata-only rule requires both uncontaminated venues, Bitget and
Bybit, to cover every exact window. Bybit passed. Bitget did not provide data
before 2026-04-18 through the locked public endpoint. Therefore fewer than two
clean venues remain and H1 is parked before outcome analysis.

Binance passed structural coverage but remains ineligible for untouched H1
validation/holdout because its funding outcomes were inspected in prior Setup
D/F work. OKX failed historical coverage as expected from its short public
retention. Neither venue may rescue Bitget under the locked rule.

No funding rate, price, spread, return, fee, or PnL value was inspected,
printed, compared, summarized, or used in this decision.

## Structural Results

| Venue | Coverage | Pages | Rows | Returned UTC bounds | Maximum gap | Clean H1 holdout |
|---|---|---:|---:|---|---:|---|
| Binance | PASS | 4 | 3,831 | 2023-01-01 to 2026-06-30 | 28,800,026 ms | No, prior funding contamination |
| Bitget | FAIL | 4 | 270 | 2026-04-18 to 2026-07-16 | 28,800,000 ms | No, insufficient coverage |
| Bybit | PASS | 20 | 4,000 | 2022-11-05 to 2026-06-30 | 28,800,000 ms | Yes |
| OKX | FAIL | 2 | 233 | 2026-04-14 to 2026-06-30 | 28,800,000 ms | No, insufficient coverage |

Coverage uses settlement timestamps only. Row counts, timestamp bounds, gaps,
and booleans are structural metadata, not economic outcomes.

## Artifact Binding

Ignored local root:
`research/signal_observation/data/h1/phase_a_coverage/h1_phase_a_coverage_20260717_v1/`

- metadata bytes: `6,094`;
- metadata SHA-256:
  `4be84765bdcb7367988853302c68c1840c1351b8b6fddc889fd2a263177cd623`;
- opaque raw pages: `30`;
- opaque raw bytes: `802,354`;
- independent raw-page SHA verification: `30/30`, zero errors.

The ignored metadata file contains the SHA-256 of every deterministic
`raw/<venue>/page_NNNN.json` artifact. Raw responses remain local and sealed.

## Decision Boundary

- H1: `PARK / DATA FEASIBILITY` for this preregistered free-data attempt.
- H2/H6: no automatic rescue; they share the carry/basis search surface.
- H3: becomes the next preregistration candidate under the July portfolio.
- Analysis, Phase B, paper, testnet orders, live trading, and profitability
  claims remain unauthorized.

Reopening H1 requires a genuinely new contamination-safe free source or a new
owner decision that changes the no-spend constraint. Re-querying the same
endpoints, shifting windows, substituting Binance, or shortening the holdout is
not allowed.
