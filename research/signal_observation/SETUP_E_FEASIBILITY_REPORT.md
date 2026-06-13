# Setup E — Stage 1 Feasibility Report

Generated: 2026-06-13T06:39Z
Constitution: `docs/RESEARCH_CONSTITUTION.md` v1.1
Pre-registration: `research/signal_observation/SETUP_E_PREREGISTRATION.md` (DRAFT)
Universe list: `research/signal_observation/_selected_symbols.json`

**HARD RULE**: This report contains NO outcome metrics. No returns, win rates,
expectancy, MFE/MAE, or any value derived from prices after a signal bar.
(Constitution §1, Stage 1. Violation taints the discovery window.)

---

## Overall Verdict

**FEASIBLE — proceed to pre-registration lock**

| Metric | Value | Minimum | Status |
|---|---|---|---|
| Total episodes — full window | 1146 | — | — |
| Total episodes — discovery (first 70%) | 644 | 80 | **SUFFICIENT** |
| Total episodes — validation (last 30%) | 502 | 40 | **SUFFICIENT** |
| Quality (all symbols) | 20/20 PASS | 20/20 PASS | **PASS** |

---

## Window Boundaries

Window split: first 70% of per-symbol aligned bars = discovery;
remaining 30% = validation. Boundaries differ by symbol due to varying
liquidation data retention. A **single cross-symbol cut date** may be
preferred — the median of per-symbol 70% cutpoints is shown below.

**Suggested single discovery/validation cutpoint (median): `2026-03-09T00:00Z`**

Owner decision required (TBD-F in pre-registration §2.6): accept per-symbol
splits as shown, or adopt the single cutpoint. Either choice must be recorded
in the locked pre-registration before any Stage 2 run.

---

## Per-Symbol Detail

| Symbol | OHLCV bars | Aligned bars | Quality | First aligned bar | Discovery cut | Validation start | Last bar | Eps full | Eps disc | Eps val |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT_PERP.A | 2002 | 1504 | PASS | 2025-10-05T00:00Z | 2026-03-29T04:00Z | 2026-03-29T08:00Z | 2026-06-13T04:00Z | 55 | 32 | 23 |
| ETHUSDT_PERP.A | 2002 | 1504 | PASS | 2025-10-05T00:00Z | 2026-03-29T04:00Z | 2026-03-29T08:00Z | 2026-06-13T04:00Z | 46 | 22 | 24 |
| SOLUSDT_PERP.A | 2002 | 1510 | PASS | 2025-10-04T00:00Z | 2026-03-29T00:00Z | 2026-03-29T04:00Z | 2026-06-13T04:00Z | 54 | 30 | 24 |
| BNBUSDT_PERP.A | 2002 | 1609 | PASS | 2025-09-17T00:00Z | 2026-03-23T20:00Z | 2026-03-24T00:00Z | 2026-06-13T04:00Z | 48 | 27 | 21 |
| XRPUSDT_PERP.A | 2002 | 1531 | PASS | 2025-09-30T12:00Z | 2026-03-27T20:00Z | 2026-03-28T00:00Z | 2026-06-13T04:00Z | 51 | 28 | 23 |
| DOGEUSDT_PERP.A | 2002 | 1568 | PASS | 2025-09-24T08:00Z | 2026-03-26T00:00Z | 2026-03-26T04:00Z | 2026-06-13T04:00Z | 57 | 34 | 23 |
| ADAUSDT_PERP.A | 2002 | 1683 | PASS | 2025-09-02T12:00Z | 2026-03-19T12:00Z | 2026-03-19T16:00Z | 2026-06-13T04:00Z | 68 | 38 | 30 |
| AVAXUSDT_PERP.A | 2002 | 1866 | PASS | 2025-07-25T20:00Z | 2026-03-07T00:00Z | 2026-03-07T04:00Z | 2026-06-13T04:00Z | 61 | 32 | 29 |
| LINKUSDT_PERP.A | 2002 | 1763 | PASS | 2025-08-17T12:00Z | 2026-03-13T20:00Z | 2026-03-14T00:00Z | 2026-06-13T04:00Z | 58 | 33 | 25 |
| DOTUSDT_PERP.A | 2002 | 1898 | PASS | 2025-07-17T08:00Z | 2026-03-07T08:00Z | 2026-03-07T12:00Z | 2026-06-13T04:00Z | 59 | 32 | 27 |
| LTCUSDT_PERP.A | 2002 | 1858 | PASS | 2025-07-25T08:00Z | 2026-03-06T08:00Z | 2026-03-06T12:00Z | 2026-06-13T04:00Z | 59 | 35 | 24 |
| UNIUSDT_PERP.A | 2002 | 1884 | PASS | 2025-07-14T16:00Z | 2026-03-04T04:00Z | 2026-03-04T08:00Z | 2026-06-13T04:00Z | 64 | 33 | 31 |
| ATOMUSDT_PERP.A | 2002 | 1851 | PASS | 2025-07-15T08:00Z | 2026-03-04T16:00Z | 2026-03-04T20:00Z | 2026-06-13T04:00Z | 62 | 41 | 21 |
| FILUSDT_PERP.A | 2002 | 1868 | PASS | 2025-07-14T16:00Z | 2026-03-09T00:00Z | 2026-03-09T04:00Z | 2026-06-13T04:00Z | 57 | 28 | 29 |
| ARBUSDT_PERP.A | 2002 | 1912 | PASS | 2025-07-14T16:00Z | 2026-03-04T00:00Z | 2026-03-04T04:00Z | 2026-06-13T04:00Z | 64 | 34 | 30 |
| OPUSDT_PERP.A | 2002 | 1890 | PASS | 2025-07-20T20:00Z | 2026-03-05T16:00Z | 2026-03-05T20:00Z | 2026-06-13T04:00Z | 64 | 37 | 27 |
| APTUSDT_PERP.A | 2002 | 1879 | PASS | 2025-07-14T16:00Z | 2026-03-08T04:00Z | 2026-03-08T08:00Z | 2026-06-13T04:00Z | 58 | 32 | 26 |
| SUIUSDT_PERP.A | 2002 | 1557 | PASS | 2025-09-25T20:00Z | 2026-03-26T08:00Z | 2026-03-26T12:00Z | 2026-06-13T04:00Z | 52 | 32 | 20 |
| TRXUSDT_PERP.A | 2002 | 1821 | PASS | 2025-07-29T20:00Z | 2026-03-08T12:00Z | 2026-03-08T16:00Z | 2026-06-13T04:00Z | 54 | 29 | 25 |
| TONUSDT_PERP.A | 2002 | 1882 | PASS | 2025-07-14T16:00Z | 2026-03-05T12:00Z | 2026-03-05T16:00Z | 2026-06-13T04:00Z | 55 | 35 | 20 |

---

## Episode Structure Diagnostic

**HARD RULE**: this section contains NO outcome metrics. All statistics
describe signal-identification structure only (cascade→signal bar counts,
lookback validity). No prices after the signal bar are read or reported.

### 1. Cascade → Signal Lag Distribution (bars)

Lag = number of bars from cascade bar to signal/exhaustion bar (minimum 1).
A lag of 1 means exhaustion fires on the very next bar after the cascade
(immediate exhaustion — flagged separately below as a potential degeneracy).

| Window | N | min | p25 | median | p75 | p90 | max | mean | lag=1 (%) |
|---|---|---|---|---|---|---|---|---|---|
| Pooled (all) | 1146 | 1 | 1 | 2 | 4 | 6 | 24 | 3.21 | 30.4% |
| Discovery (first 70%) | 644 | 1 | 1 | 2 | 4 | 8 | 24 | 3.48 | 26.6% |
| Validation (last 30%) | 502 | 1 | 1 | 2 | 4 | 5 | 24 | 2.85 | 35.3% |

### 2. Immediate Exhaustion (lag = 1 bar) — Degeneracy Flag

An episode where the exhaustion signal fires on the bar immediately after
the cascade bar may indicate that the median threshold is too easy to reach,
or that cascade bars themselves suppress subsequent liquidation structurally.

| Window | Episodes | lag=1 | lag=1 % |
|---|---|---|---|
| Pooled | 1146 | 348 | 30.4% |
| Discovery | 644 | 171 | 26.6% |
| Validation | 502 | 177 | 35.3% |

### 3 & 4. Incomplete-Lookback Episodes

The trailing 30-day lookback (180 × 4H bars) is FULLY accumulated starting
at bar index 180. The cascade detection loop enforces this: it begins at
`range(_TRAILING_BARS=180, n)`, so no cascade bar can have index < 180.
Therefore the signal bar (cascade_idx + 1 at minimum) always has index ≥ 181,
which is outside the first 180 bars (the lookback warmup period).

| Window | Incomplete-lookback episodes | Total | Excluded count |
|---|---|---|---|
| Pooled | 0 | 1146 | 1146 episodes retained |
| Discovery | 0 | 644 | 644 episodes retained |
| Validation | 0 | 502 | 502 episodes retained |

**Result**: 0 incomplete-lookback episodes. The implementation correctly
prevents any episode from relying on a partial lookback window.
Exclusion has no effect on episode counts.

### 5. Stricter Exhaustion Definition (25th percentile vs median)

Baseline definition: signal bar = first bar where long-liq < trailing-30d **median** (50th pct).
Stricter definition: signal bar = first bar where long-liq < trailing-30d **25th percentile** (25th pct).
A lower threshold means exhaustion fires only on more extreme liq drops,
reducing episode count but potentially improving signal quality.

| Window | Baseline (median, 50th pct) | Stricter (25th pct) | Reduction |
|---|---|---|---|
| Pooled | 1146 | 954 | −192 (16.8%) |
| Discovery | 644 | 544 | −100 (15.5%) |
| Validation | 502 | 410 | −92 (18.3%) |

**Strict definition still meets minimums** (discovery ≥ 80, validation ≥ 40).

---

## Dataset SHA-256 Hashes

These hashes bind this report to the exact downloaded files.
Record these in the pre-registration §2.6 TBD-F fields at lock time.

| Symbol | Dataset | SHA-256 |
|---|---|---|
| BTCUSDT_PERP.A | ohlcv | `6836ca5066d29f71122d1092028f176ba87f05e4537ab59ba816b9de28588d22` |
| BTCUSDT_PERP.A | liquidation | `fcbcdf8b8426500e1c222fbea208f004a2c983febc9617f23be314f4a678b9b2` |
| ETHUSDT_PERP.A | ohlcv | `d5a4fcdbbc889e29c0079da5aa389b080ea2adae61252aef67ef7d0eca515b3d` |
| ETHUSDT_PERP.A | liquidation | `d9d033c028f1625853d64fd0e064263a86cc4c6a3cab946441beb44e04d1e372` |
| SOLUSDT_PERP.A | ohlcv | `1f14324eb0b9236dbf9512828591f1c4cb8d68f29d995142cf960553fef2b0d6` |
| SOLUSDT_PERP.A | liquidation | `ffc0e394785da091830251bffb65b23a90ba5df311f9703752ef69ad9b319765` |
| BNBUSDT_PERP.A | ohlcv | `f9cfa7045fdec2bed27ae8da973cbaef26bc8d52816072055b0db701e3c044d5` |
| BNBUSDT_PERP.A | liquidation | `265645c0c818ad3fc8e1cda719db92d7d51aa41f8ba2376a4646732f3ceb04d7` |
| XRPUSDT_PERP.A | ohlcv | `823668b80a7ba763e02054fdfe0ee2fd7449a84a59bfdcf26dbcb1046ea1bc3c` |
| XRPUSDT_PERP.A | liquidation | `979f92d5d43855b6d2762a6e71bf836b84d4d2925601782fe49377d8144f6f9a` |
| DOGEUSDT_PERP.A | ohlcv | `ca47a042b8278e1c10d6703ddedbbd7e49a81bff97750d57abca8ab7ef15f696` |
| DOGEUSDT_PERP.A | liquidation | `1782f005e321d65f0566ac9bbf38f4b02a5fdcdc27455624ff88955cf52024df` |
| ADAUSDT_PERP.A | ohlcv | `26ecf22e891ef6fe24a250fd4a965479a48daef294e94f50c8d475bd55ca586c` |
| ADAUSDT_PERP.A | liquidation | `ff1d42e4014303d705f43d40f8c48b6b93a6d0c4580358ceca35cd869d88b19a` |
| AVAXUSDT_PERP.A | ohlcv | `a30c46f9c3efae9652d0a09a13f178ddbadf79166c8bb000e1487a6cb3fc2c21` |
| AVAXUSDT_PERP.A | liquidation | `067c43648b3bbcd5d029a0605a8f4de35fbd1a74087b54b82ecb8393c35b0812` |
| LINKUSDT_PERP.A | ohlcv | `b6765c35abc73d0c7a5545df60f909ef952f340a98081ff8e3f528c66607e923` |
| LINKUSDT_PERP.A | liquidation | `22a2abaa5980c930627a389a6f8e7086429807e37c4c95c05f45f0be0c705d61` |
| DOTUSDT_PERP.A | ohlcv | `77e6c95c3e9bc2106aab23871030b1b80b87d7c4a1d0e9cd1f5e09b0b5150006` |
| DOTUSDT_PERP.A | liquidation | `99075f5e998de631182bbdfee9c9ff7b192d1c3d7ebdb54aa31e75e9a20bb8e3` |
| LTCUSDT_PERP.A | ohlcv | `d70842fd1a524f88ad01c341abc0e44df78312e4e5c8cd6c235733c7c869be4f` |
| LTCUSDT_PERP.A | liquidation | `b10275e397b09a2d48bcb9ee9a7890053062f9200c7c99ce8789d81e0b332dcd` |
| UNIUSDT_PERP.A | ohlcv | `4feca4df78698c7cd3d8a39b820cdabdf5ae6e1ddd41420559202d568952c5a2` |
| UNIUSDT_PERP.A | liquidation | `6a23cc7c9ffe9b5156fafaf1853fa56f7276ee8439645351c664ee12036c837e` |
| ATOMUSDT_PERP.A | ohlcv | `e97e0b65ccfcac84a25af6d9e279479b06662ddd4dc7e7295f7d54b7a56c9a2b` |
| ATOMUSDT_PERP.A | liquidation | `bf81d2ac64aaa5cce2a66f7b99ba1632af1215ecc7ab21dd1f85d7b196f860cc` |
| FILUSDT_PERP.A | ohlcv | `3a1efedfa81ee5b91fc552d77dc1ab51a34163bc3340da4b4abc983e3307db28` |
| FILUSDT_PERP.A | liquidation | `69916699482a65bc274356931bcf263e59ca88e0f3b57cd7df5d6c50112648c1` |
| ARBUSDT_PERP.A | ohlcv | `4fa6924996946e76e2ea5ff165faff98ce4258809b2e8bd6f235890b7259f60b` |
| ARBUSDT_PERP.A | liquidation | `a99269f7eda9ac609f8c74daa035a8eeae18833c962ea84789e3470ee66ff271` |
| OPUSDT_PERP.A | ohlcv | `30afa880a13d2b05ea9bce3b2fccd876c2637aca5b5bf8e425cf046aa0215149` |
| OPUSDT_PERP.A | liquidation | `4d346fa3e62eae973d82cf8e376b7b94a610f9a3952646fad4de55b08623ebb0` |
| APTUSDT_PERP.A | ohlcv | `25755bfce7728c2bf5662c031fed60a7a3ad08825d0ae219433442d5de8cf936` |
| APTUSDT_PERP.A | liquidation | `2ebbe946f344ba495bbd2ba34ea9316055b566087b00355a97e03f0385e8eb31` |
| SUIUSDT_PERP.A | ohlcv | `967b93098049ae538d7efe090fd6d487b19c1324a9c040c1059d569dbd445791` |
| SUIUSDT_PERP.A | liquidation | `04db0e60e046cf25cd15710dea07aca6ad86ccdc2f4cac55ce9328f20fe9023f` |
| TRXUSDT_PERP.A | ohlcv | `be69c1f20485954635b0539c1c6579800fa2dbc1cb06babb06f50e703e173288` |
| TRXUSDT_PERP.A | liquidation | `b236492676f130c09d891a6810f8505a9951b5619f5792bcdb4df2431f050c4c` |
| TONUSDT_PERP.A | ohlcv | `b53e753d7a23969d9ab9767106fb971cac758bc967b9cf4989b4fecd241fa28b` |
| TONUSDT_PERP.A | liquidation | `792c5fc1f6508336f586b588859e457075b718d02425188a80cb978a6a51bdf7` |

---

## Methodology Notes

- **Cascade bar**: long-liquidation notional > 95th percentile of trailing
  30-day (180 × 4H bar) long-liq distribution AND close < open (down bar).
- **Signal/exhaustion bar**: first subsequent bar where long-liq falls below
  the trailing 30-day median. Episode tagged to this bar's timestamp.
- **Non-overlapping**: new episode cannot start until prior signal bar + 1
  (constitution §3.8).
- **Window split**: episode assigned to discovery if signal bar timestamp ≤
  the 70th-percentile bar; validation if ≥ 71st-percentile bar. Trailing
  lookback for validation bars borrows from discovery data (contemporaneous,
  not outcome data — permitted at Stage 1).
- **Quality threshold**: <5% non-4H gaps → PASS.

---

## Owner Decisions Required Before Pre-Registration Lock

1. **Source approval**: approve Coinalyze free API key path as data source.
2. **Universe confirmation**: confirm the 20 symbols in `_selected_symbols.json`
   are accepted as frozen.
3. **Window boundary**: choose per-symbol 70/30 splits (as tabulated above)
   OR adopt single cutpoint `2026-03-09T00:00Z` (median of per-symbol cuts).
4. **SHA-256 lock**: copy hashes from the table above into pre-registration §2.6.
5. **Minimum confirmation**: discovery minimum is 80 (met). Validation minimum
   is 40 (met). No adjustment needed.
6. **Exhaustion definition**: review §3 (immediate exhaustion fraction) and §5
   (strict 25th-pct variant) in the diagnostic section above before locking §2.3.
