# Q1 EMA Spec and Review Checklist

## 1. Status

- Status: DRAFT
- Current mode: paper trading only
- Live trading: NO-GO
- Stage 53-B implementation: BLOCKED until OI-1..OI-9 are answered
- Purpose: define the required spec and review gate before Q1-FIX-3 true EMA implementation

## 2. Scope

- This document is docs-only.
- This document does not implement EMA.
- This document does not change signal behavior.
- This document does not enable live trading.
- Future Q1-FIX-3 allowed files:
  - apps/market_data/domain/snapshot_builder.py
  - apps/market_data/tests/test_snapshot_builder.py

## 3. EMA formula

- alpha = 2 / (N + 1)
- EMA_t = alpha * price_t + (1 - alpha) * EMA_(t-1)
- Equivalent form: EMA_t = EMA_(t-1) + alpha * (price_t - EMA_(t-1))
- price input: close
- periods: 20 and 50 for current snapshot fields
- process closes oldest to newest
- insufficient data behavior must remain unchanged

## 4. Seed policy

Use SMA of the first N closes as the initial EMA seed:
EMA_(N-1) = SMA(close_0 ... close_(N-1))
Then recursively apply EMA from index N onward.
The final EMA value at the latest close is used as ema_20 or ema_50.

## 5. Test vectors

Q1-FIX-3 tests must include deterministic golden values for:

- ema_20 on a non-linear close series
- ema_50 on a non-linear close series
- insufficient-data behavior unchanged
- EMA value must not equal the simple average of only the last N closes on a non-linear series

Keep this section concise. Do not include huge tables.

## 6. Legacy paper data note

- Before Q1-FIX-3, ema_20 and ema_50 used legacy SMA-as-EMA behavior.
- After Q1-FIX-3, ema_20 and ema_50 must use true EMA.
- Do not compare pre/post Q1-FIX-3 paper signal stats without calculation-version context.

## 7. Review checklist before Q1-FIX-3 merge

Checklist:

- Only allowed Q1-FIX-3 files changed.
- No live/exchange/order routing changes.
- No risk/orchestrator/execution_service/position_manager changes.
- No config/infra/alembic/dependency changes.
- No secrets.
- Formula matches this spec.
- Seed policy matches this spec.
- Tests include ema_20, ema_50, insufficient-data behavior.
- Targeted tests pass.
- Relevant market_data tests pass.

## 8. Non-goals

- Do not add RSI, MACD, Bollinger, ML, regime detection, slippage, event bus, FSM implementation, or Stage 53-B auth work.
- Do not modify live trading gates.
- Do not change risk authority.
