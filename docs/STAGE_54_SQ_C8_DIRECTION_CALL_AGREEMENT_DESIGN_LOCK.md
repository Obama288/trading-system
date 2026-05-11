# Stage 54-SQ-C8 Direction-Call Agreement Design Lock

## Purpose

- Determine whether Bitget and Binance C7 both-PASS is supported by similar
  per-rebalance direction calls, or whether the venues pass with materially
  different direction sequences.
- Explain whether Binance dev-magnitude divergence is more likely caused by
  direction-call differences or by volatility / micro-pricing / return
  magnitude differences.
- Observational only. No gate change. No filter. No readiness promotion.

## Scope

- Venues: Bitget and Binance only.
- Symbols: BTCUSDT, ETHUSDT, SOLUSDT only.
- Timeframe: 4H only.
- Windows: same locked C7 development and expanded windows already used by
  Bitget and Binance.
- Detector: frozen Setup C / TSMOM detector.
- Primary: 40-bar lookback.
- Sensitivities: 20/60 may be reported only if already available, but primary
  comparison is 40-bar. 20/60 sensitivities may be reported only if they are
  already present in committed C7 artifacts or can be re-derived from the same
  committed CSVs without new downloads, parameter changes, or additional data.
- No OKX work in this stage.

## Inputs

- Existing committed Bitget C7 data/artifacts.
- Existing committed Binance C7 data/artifacts.
- Committed CSVs only.
- No new downloads.
- No API calls.
- No data mutation.
- Frozen detector only.
- Rebalance timestamps and direction signs must be re-derived by running the
  frozen Setup C detector on the committed Bitget and Binance C7 CSVs. Do not
  read or infer direction calls from headline report aggregates.
- Bitget and Binance C7_PASS verdicts are read-only inputs. C8 must not revise,
  relabel, or weaken those C7 verdicts.

## Required Diagnostics

### 1. Per-symbol direction agreement rate

- Count aligned rebalance timestamps by symbol.
- Count matching direction signs.
- Count opposite direction signs.
- Count missing venue rows.
- Report agreement percentage.

### 2. Window-level direction agreement

- Development window.
- Expanded window.
- Combined window, meaning development + expanded windows together.

### 3. Outcome attribution

- If direction agreement is high but magnitude differs, classify as
  magnitude / volatility / micro-pricing divergence, using the pre-registered
  high agreement threshold of >= 80%.
- If direction agreement is low, classify as signal-disagreement divergence.
- Low agreement is pre-registered as < 60%.
- If missing alignment is material, classify as inconclusive due alignment
  coverage.
- Mixed/inconclusive is pre-registered as 60% to 80% or material missing
  coverage.

### 4. Symbol concentration check

- Report whether SOL direction agreement differs materially from BTC/ETH.
- Observational only.

### 5. No gate change

- C8 must not alter C7 PASS.
- C8 must not introduce filters.
- C8 must not authorize paper/runtime/trading/live readiness.

## Suggested Interpretation Labels

- `high_direction_agreement_magnitude_divergence`
- `low_direction_agreement_signal_divergence`
- `mixed_or_inconclusive`

## Pre-implementation Rules

- Define exact alignment key before coding: symbol + rebalance timestamp.
- Missing-row policy: a rebalance timestamp is aligned when both venues supply
  a row for that symbol and timestamp. Rows present in one venue but absent in
  the other are counted as missing, excluded from agreement-rate numerator and
  denominator, and reported as separate coverage counts.
- Define minimum coverage threshold before coding.
- Do not inspect results before locking these rules.

## Recommended Default Thresholds

- High agreement: >= 80% matched direction signs on aligned timestamps.
- Low agreement: < 60%.
- Mixed/inconclusive: 60% to 80% or material missing coverage.
- Material missing coverage: > 10% missing aligned rows for any symbol/window.
  The >10% material missing coverage threshold applies to every reported slice:
  per-symbol, per-window, and combined.

## Anti-cherry-picking

- No threshold changes after results.
- No excluding symbols.
- No excluding windows.
- No changing lookback/rebalance.
- No new venue data.
- No replacing existing CSVs.

## What C8 Does Not Authorize

- Paper trading.
- Live trading.
- Runtime wiring.
- Private API access.
- Exchange operations.
- Parameter optimization.
- Strategy filters.
- Readiness claims.

## Next Step

Independent review of this design lock is required before any C8
implementation, data processing, or analysis.
