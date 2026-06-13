# Setup H Feasibility Report

Generated: E:\trading-system\research\signal_observation\run_setup_h_feasibility.py
Data directory: `research/signal_observation/data/setup_h/`

## Verdict: FEASIBLE

All 9 symbols pass quality; all meet 80/40 rebalance-observation minimums.

## Dataset SHA-256

Combined hash (all files, sorted): `30d2027f9af6f191dfa7ff0e572b60c28b91f0c68ea8f28ec021f292b5788d05`

Per-file hashes:
- `ADAUSDT`: `44945c11e75e1a50970795cc4162b6fb104205d3eae0483b740877d11418b851`
- `AVAXUSDT`: `4b5c296dfe3e03ce0d7625ce563a987d2bbd7105bbfc8183ce05c798bab6bfdc`
- `BNBUSDT`: `eefb99006c2457d8d98fd69ec435a3e1201a209bd148d74844162859e91c662e`
- `DOGEUSDT`: `9574f87ccc6232d1a58e9a97bfd2b1d964892fa73e39d96c9eb56383a1e78031`
- `DOTUSDT`: `7db30dad2d30e5d2e8d528ab6dd48e108355cbf031f2130386a11b2b2e3bf291`
- `LINKUSDT`: `2d3d8a3c39970c9e0ed00af7cbb2fab217278e53531e86c0d8e8ca6aa16f8f94`
- `SOLUSDT`: `fd54c7550de2379ffcd7783cee06e9bcba59bb06e209f3a5903d604da6ed7877`
- `XRPUSDT`: `e60fa90c400e02984d5ff4f863525ac58797e0db657d728f4f3e662c54a55f85`
- `ZECUSDT`: `ff4f6bf5eca51c602850512d2268396f3bad662c1d50b66431f791c14650e62f`

## Common date window (for 70/30 split)

- Common start (latest first bar): `2020-09-23`
- Common end (earliest last bar): `2026-06-12`
- Discovery cutoff (~70%): `2024-09-24 04:00 UTC`
- [TBD-F at lock: owner sets exact cutoff date from this estimate]

## Coverage and quality

| Symbol | Start | End | Bars | Quality |
|--------|-------|-----|------|---------|
| SOLUSDT | 2020-09-14 | 2026-06-12 | 12557 | PASS |
| BNBUSDT | 2020-02-10 | 2026-06-12 | 13888 | PASS |
| XRPUSDT | 2020-01-06 | 2026-06-12 | 14068 | PASS |
| DOGEUSDT | 2020-07-10 | 2026-06-12 | 12982 | PASS |
| ADAUSDT | 2020-01-31 | 2026-06-12 | 13948 | PASS |
| AVAXUSDT | 2020-09-23 | 2026-06-12 | 12533 | PASS |
| LINKUSDT | 2020-01-17 | 2026-06-12 | 14032 | PASS |
| DOTUSDT | 2020-08-22 | 2026-06-12 | 12725 | PASS |
| ZECUSDT | 2020-02-05 | 2026-06-12 | 13888 | PASS |

## Regime characterisation

Regime gate: ATR20/close < trailing 180-bar median = LOW-VOL; >= median = HIGH-VOL. Rebalance bar every 6th 4H bar.
Discovery/validation split cutoff: `2024-09-24 04:00 UTC`

### Discovery (first ~70%)

| Symbol | Rebalance bars | LOW-VOL | HIGH-VOL | Meets >=80? |
|--------|----------------|---------|----------|-------------|
| SOLUSDT | 1433 | 762 | 671 | YES |
| BNBUSDT | 1654 | 936 | 718 | YES |
| XRPUSDT | 1684 | 927 | 757 | YES |
| DOGEUSDT | 1503 | 876 | 627 | YES |
| ADAUSDT | 1664 | 887 | 777 | YES |
| AVAXUSDT | 1429 | 766 | 663 | YES |
| LINKUSDT | 1678 | 932 | 746 | YES |
| DOTUSDT | 1461 | 776 | 685 | YES |
| ZECUSDT | 1654 | 861 | 793 | YES |

**Pooled discovery**: 14160 rebalance obs (7723 LOW-VOL, 6437 HIGH-VOL)

### Validation (last ~30%)

| Symbol | Rebalance bars | LOW-VOL | HIGH-VOL | Meets >=40? |
|--------|----------------|---------|----------|-------------|
| SOLUSDT | 626 | 317 | 309 | YES |
| BNBUSDT | 627 | 386 | 241 | YES |
| XRPUSDT | 627 | 357 | 270 | YES |
| DOGEUSDT | 627 | 336 | 291 | YES |
| ADAUSDT | 627 | 338 | 289 | YES |
| AVAXUSDT | 626 | 335 | 291 | YES |
| LINKUSDT | 627 | 319 | 308 | YES |
| DOTUSDT | 626 | 324 | 302 | YES |
| ZECUSDT | 627 | 320 | 307 | YES |

**Pooled validation**: 5640 rebalance obs (3032 LOW-VOL, 2608 HIGH-VOL)

## ZEC liquidity check

- Avg daily quote volume (USD): **158,921,636**
- Avg 4H H/L range proxy: **3.5410%** (this is intrabar price RANGE, not bid-ask spread)
- Volume minimum threshold: $500,000/day
- Extreme-volatility flag (H/L range > 8.0%): NO

**Recommendation: INCLUDE ZEC.** Volume well above threshold ($500k/day). H/L range is normal for a mid-cap perp. Bid-ask spread not directly measurable from OHLCV; the 8 bps one-way assumption is standard and should be flagged as an assumption, not confirmed.

## Notes for pre-registration lock

1. Exact discovery/validation cutoff date: owner sets from the estimate above (`2024-09-24T04:00:00Z`).
2. Dataset SHA-256: record combined hash above at lock.
3. ZEC include/exclude: see recommendation above.
4. Baseline seed: owner fixes integer seed (§2.4).

