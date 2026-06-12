# Unified Outcome Simulator — Technical Specification

Status: v1.1 — post-review amendments (2026-06-12); v1.0 implements Research Constitution section 3
Target location: `research/simcore/`
Audience: implementing agent (Claude Code). Constitution decisions are binding;
where this spec and the constitution disagree, the constitution wins.

---

## 1. Goal and non-goals

Goal: one deterministic trade-outcome simulator used by every research family.
It replaces three divergent implementations:

- `research/signal_observation/outcomes.py::resolve_outcome`
- `research/signal_observation/setup_b.py::evaluate_multi_r_outcomes` (+ helpers)
- `research/hypothesis_agent/analysis/patterns.py::_simulate_trade`

Non-goals: no order routing, no portfolio accounting, no live execution. This is
research simulation only. Detector logic (how signals are found) is untouched.

## 2. Module layout

```
research/simcore/
    __init__.py        # public API re-exports
    candles.py         # Candle moved here (see 2.1)
    timeutil.py        # bar duration, decision_time, session labeling glue
    models.py          # TradeSpec, FillPolicy, CostModel, TradeSim, InvalidTrade
    simulator.py       # simulate_trade, simulate_multi_target
    selection.py       # select_non_overlapping
    costs.py           # bps→R conversion, standard scenarios
tests/research/simcore/
    test_simulator_golden.py
    test_costs.py
    test_selection.py
    test_timeutil.py
```

### 2.1 Candle relocation
Move `research/signal_observation/candles.py` to `research/simcore/candles.py`
unchanged (Decimal fields, validation, `normalize_utc`, `parse_iso_utc`).
Leave `research/signal_observation/candles.py` as a re-export shim:

```python
from research.simcore.candles import Candle, normalize_utc, parse_iso_utc  # noqa: F401
```

All 402 existing tests must keep passing through the shim.

## 3. Time semantics (`timeutil.py`)

- `Candle.timestamp` is bar OPEN time (existing convention, now documented).
- `bar_duration(candles) -> timedelta`: median of consecutive timestamp deltas;
  raise if fewer than 2 candles or if **>5% of deltas deviate >1% from the
  median** (isolated missing bars are tolerated; truly mixed timeframes are
  rejected). v1.1 amendment: the v1.0 rule (any deviation raises) was too
  strict for production feeds with occasional dropped bars.
- `decision_time(candle, duration) -> datetime`: `timestamp + duration` (UTC).
- `label_session(candle, duration) -> str`: wraps the existing
  `signal_observation.sessions.session_label` but feeds it `decision_time`.
  Per constitution 3.1, NO research code may call `session_label` with an open
  time after migration; add a lint-style grep check to the migration checklist.

## 4. Data models (`models.py`)

All numeric fields are `Decimal`. Floats are rejected with `TypeError`.

```python
class Direction(StrEnum): LONG = "long"; SHORT = "short"

class FillPolicy(StrEnum):
    NEXT_BAR_OPEN = "next_bar_open"     # default; the only gate-eligible policy
    SIGNAL_CLOSE = "signal_close"       # diagnostic-only

@dataclass(frozen=True, slots=True)
class TradeSpec:
    symbol: str
    direction: Direction
    signal_index: int                    # index of the bar whose CLOSE triggers
    stop_price: Decimal
    target_r_values: tuple[Decimal, ...] # e.g. (1, 1.5, 2)
    outcome_window_bars: int             # counted from the entry bar, inclusive
    fill: FillPolicy = FillPolicy.NEXT_BAR_OPEN

@dataclass(frozen=True, slots=True)
class TargetSim:
    target_r: Decimal
    target_price: Decimal
    outcome: str                 # "win" | "loss" | "flat"
    exit_price: Decimal
    exit_index: int              # absolute candle index
    bars_to_resolution: int      # exit_index - entry_index + 1
    gap_exit: bool               # exit price came from a bar open beyond level
    final_r_gross: Decimal
    mae_r: Decimal               # over bars [entry_index .. exit_index]
    mfe_r: Decimal

@dataclass(frozen=True, slots=True)
class TradeSim:
    spec: TradeSpec
    entry_index: int
    entry_time: datetime         # decision_time of the signal bar
    entry_price: Decimal
    initial_r: Decimal
    session: str                 # from entry_time
    targets: dict[Decimal, TargetSim]

@dataclass(frozen=True, slots=True)
class InvalidTrade:
    spec: TradeSpec
    reason: str                  # machine-readable funnel code, see 5.1
```

`simulate_trade` returns `TradeSim | InvalidTrade`. Detectors keep their funnel
counters by counting `InvalidTrade.reason`.

## 5. Simulation semantics (`simulator.py`)

### 5.0 Entry  *(v1.1 amendment)*
- `NEXT_BAR_OPEN` (default): `entry_index = signal_index + 1`,
  `entry_price = candles[entry_index].open`,
  `entry_time = decision_time(candles[signal_index])`.
- `SIGNAL_CLOSE` (diagnostic): `entry_price = candles[signal_index].close`,
  same `entry_time`. **Resolution window starts at `signal_index + 1`**
  (`entry_index = signal_index + 1`); the signal bar's own high/low range is
  look-ahead for a close fill and must not be simulated. Any artifact built
  from SIGNAL_CLOSE results MUST carry `"fill_policy": "signal_close",
  "gate_eligible": false`.

### 5.1 Entry validation (reasons for `InvalidTrade`)  *(v1.1 amendment)*
- `no_entry_bar` — `signal_index + 1 >= len(candles)` (NEXT_BAR_OPEN only).
- `no_resolution_bars` — `signal_index + 1 >= len(candles)` (SIGNAL_CLOSE only).
- `non_positive_r` — `initial_r = |entry_price − stop_price| <= 0`.
- `entry_gap_through_stop` — entry bar OPEN already at/beyond stop
  (LONG: `open <= stop`; SHORT: `open >= stop`). NEXT_BAR_OPEN only; for
  SIGNAL_CLOSE, a gap on the first resolution bar is handled as a regular gap
  exit inside the simulator.
- `incomplete_window` — `entry_index + outcome_window_bars > len(candles)`.
  Raised instead of silently truncating the window.
- `window_non_positive` — `outcome_window_bars <= 0`.

Note: `entry_gap_through_target` is removed in v1.1. For NEXT_BAR_OPEN the
check is mathematically unreachable (entry_price = open, target = entry_price +
positive). For SIGNAL_CLOSE, a gapped-through-target first resolution bar is now
correctly booked as a gapped win rather than rejected.

### 5.2 Outcome window  *(v1.1 amendment)*
`window = candles[entry_index : entry_index + outcome_window_bars]` where
`entry_index = signal_index + 1` for both fill policies.
- `NEXT_BAR_OPEN`: bar 1 of the window is the entry bar; its full high/low range
  counts (entry is at its open, so this is causal, not look-ahead).
- `SIGNAL_CLOSE`: bar 1 of the window is the first post-signal bar; its open
  may gap from the signal-bar close, and that gap is checked (see 5.3).

### 5.3 Per-bar resolution order (for each bar in window, in order)  *(v1.1 amendment)*
1. **Gap check on bar open** (skip for bar 1 of a NEXT_BAR_OPEN window only —
   its open IS the entry price, already validated in 5.1; SIGNAL_CLOSE windows
   apply the gap check to all bars including bar 1):
   - open at/beyond stop → exit at `bar.open`, outcome `loss`, `gap_exit=True`,
     `final_r_gross = signed(open − entry)/initial_r` (may be below −1).
   - open at/beyond target → exit at `bar.open`, outcome `win`, `gap_exit=True`,
     `final_r_gross` from `bar.open` (may exceed `target_r`).
   - If open is beyond BOTH (degenerate data), treat as stop (conservative).
2. **Intrabar check**: stop reachable (`low <= stop` / `high >= stop`) is
   evaluated BEFORE target (constitution 3.4). Exit price is exactly the stop
   or target level; `loss` ⇒ `final_r_gross = −1`, `win` ⇒ `final_r_gross =
   signed(target − entry)/initial_r`.
3. No exit in any bar → outcome `flat`, exit at the LAST window bar's close,
   `final_r_gross = signed(last_close − entry)/initial_r` (mark-to-market,
   constitution 3.7).

### 5.4 MAE / MFE
Computed over `candles[entry_index .. exit_index]` inclusive, relative to
`entry_price`, in R. (Matches setup_b's resolution-window convention, not
outcomes.py's full-window convention — document this delta in the migration
notes.)

### 5.5 Multi-target
`simulate_trade` resolves each `target_r` independently over the same window
(identical to setup_b's 1/1.5/2R triple). Stop and window are shared.

## 6. Costs (`costs.py`)

Constitution 3.6. Per-side cost in bps of entry notional, charged twice
(entry + exit), converted to R per trade:

```python
def cost_in_r(*, entry_price: Decimal, initial_r: Decimal, bps_per_side: Decimal) -> Decimal:
    return (Decimal(2) * bps_per_side / Decimal(10000)) * entry_price / initial_r
```

- Exit notional differences are deliberately ignored (determinism over
  precision; error is second-order).
- `SCENARIOS = {"optimistic": Decimal("5"), "moderate": Decimal("8"),
  "conservative": Decimal("15")}` — moderate is the gate scenario.
- `final_r_net(target_sim, cost_r) = final_r_gross − cost_r`. Net values are
  computed by reporting code, not stored in `TargetSim` (one gross truth,
  N cost views).
- Zero-cost output must be labeled `"cost_scenario": "zero_cost_diagnostic"`.

Note the intended consequence: tight stops (small `initial_r`) produce large
`cost_r`. This is correct and replaces the flat 0.04/0.08/0.12R scenarios.

## 7. Overlap selection (`selection.py`)

```python
def select_non_overlapping(sims: Sequence[TradeSim], *, target_r: Decimal) -> list[TradeSim]
```

Per symbol, sorted by `entry_index`: keep a sim only if its `entry_index` is
strictly greater than the `exit_index` (for the given target) of the last kept
sim for that symbol. Headline metrics (constitution 3.8) are computed on the
selected subset; the full set remains available as diagnostics.

## 8. Migration plan

Numbers WILL change (next-bar-open entry, gap rules, bps costs). That is the
point. Tests asserting old numeric outcomes are updated deliberately, never
loosened to "approximately".

### Phase 1 — simcore + golden tests (no callers touched)
Implement modules above. Golden tests use tiny hand-built candle arrays
(5–12 candles) where expected values are computed by hand in test comments.
Mandatory golden cases:

| # | Scenario | Asserts |
|---|----------|---------|
| G1 | LONG, target hit bar 3, no gaps | win, final_r = target_r, bars=3 |
| G2 | LONG, stop hit intrabar same bar as target reachable | loss (stop priority) |
| G3 | LONG, bar opens below stop (gap) | loss, gap_exit, final_r < −1 |
| G4 | SHORT mirror of G3 | symmetric values |
| G5 | No level touched in window | flat, MTM final_r from last close |
| G6 | Entry bar open beyond stop | InvalidTrade entry_gap_through_stop |
| G7 | Entry bar open beyond nearest target | InvalidTrade entry_gap_through_target |
| G8 | signal_index is last candle | InvalidTrade no_entry_bar |
| G9 | Multi-target: 1R wins, 2R flats, same window | independent outcomes |
| G10 | MAE/MFE on G1 path | exact Decimal values |
| G11 | cost_in_r: entry 100, stop 99.5, 8bps | cost_r = 0.32R exactly |
| G12 | select_non_overlapping drops overlapping 2nd sim | survivor list |
| G13 | SIGNAL_CLOSE: resolution at signal+1, gate_eligible false | entry_index=signal+1, entry_price=signal.close (v1.1) |
| G14 | bar_duration raises on truly mixed timeframes (≥40% bad) | ValueError (v1.1) |
| G15 | window extends past end of candles | InvalidTrade incomplete_window (v1.1) |

### Phase 2 — setup_b
- Replace `evaluate_multi_r_outcomes`, `_resolve_target_outcome`,
  `_excursions_for_window` with simcore calls (`signal_index = bos_index`).
- `signal_time`/`signal_hour_utc`/`session_label` now derive from
  `decision_time` (this shifts sessions by 4h vs old artifacts — expected).
- `entry_price` becomes next bar open; the `next_bar_open` column is now the
  entry and the old close-entry moves to a diagnostic column.
- Rebuild setup_b test fixtures by hand on the synthetic candle sets already in
  `tests/`; do not regenerate expectations by running the new code blindly —
  at least 3 fixture expectations must be computed manually in comments.
- Setup B is a retired family: this migration is a code-health step, not a
  re-opening (constitution: no restart without new pre-registration).

### Phase 3 — setup_a + outcomes.py
- setup_a already enters at next bar open, so semantic deltas are: gap rules
  (5.1/5.3), MAE/MFE window convention (5.4), costs. Map
  `entry_time_theoretical` → simcore `entry_index` by timestamp lookup.
- Delete `outcomes.py::resolve_outcome` after callers migrate; keep
  `OutcomeResult` only if `models.py` consumers in `libs/schemas` reference it
  (check `journal` schemas first; if referenced, deprecate instead of delete).

### Phase 4 — hypothesis_agent
- Delete `patterns.py::_simulate_trade`/`_append_trade`; route through simcore
  with `signal_index` = the bar whose close completes the pattern. This
  automatically fixes the retest-bar look-ahead (the entry bar's own range is
  simulated).
- `statistics.py::classify_confidence` and `best_session` were already removed
  in the Stage-0 demotion task; verify, don't assume.

### Acceptance criteria (whole migration)
1. All pre-existing tests pass (through shims or with deliberately updated
   fixtures, each numeric change justified in the test diff).
2. New simcore golden tests G1–G14 pass.
3. `grep -rn "session_label(" research/ | grep -v decision_time` returns only
   simcore internals.
4. No research module outside simcore computes trade exits.
5. One commit per phase; phases are independently revertible.

## 9. Out of scope, deliberately

- Funding-cost accrual for multi-day holds: pre-registered per family when
  material (constitution 3.6), not part of simcore v1.
- Partial exits / trailing stops: a future family that needs them must extend
  the contract via constitution amendment, not fork the simulator.
- Intrabar path modeling beyond stop-first: rejected; OHLC bars cannot order
  intrabar events, so the conservative rule stands.
