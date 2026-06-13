"""Setup E — Post-Liquidation Exhaustion Reversal detector.

Implements §2.3 of the LOCKED pre-registration (2026-06-13) exactly.

LONG signal
  Cascade bar: long-liq > 95th pct of trailing 30-day (180 × 4H bar)
               long-liq distribution AND bar close < bar open (down bar).
  Signal bar:  first subsequent bar (within LOOKAHEAD_CAP bars) where
               long-liq < trailing 30-day 25th pct of long-liq.

SHORT signal: mirror using short-liq; cascade up bar (close > open).

Stop: cascade extreme (lowest low LONG / highest high SHORT of the
      cascade-to-signal span) ± buffer = min(0.1% of entry, 0.25 × ATR20).

Entry: NEXT_BAR_OPEN (constitution §3.2).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from research.signal_observation.csv_loader import load_ohlcv_csv  # noqa: F401 (re-exported for callers)
from research.signal_observation.indicators import atr as _atr
from research.simcore.candles import Candle
from research.simcore.models import Direction

# ---------------------------------------------------------------------------
# Constants (§2.3 locked)
# ---------------------------------------------------------------------------
TRAILING_BARS = 180          # 30 days × 6 bars/day
CASCADE_PCT = 95
EXHAUSTION_PCT = 25          # LOCKED: stricter than median; see §2.3 rationale
LOOKAHEAD_CAP = 25           # max bars searched after cascade for exhaustion
ATR_PERIOD = 20
OUTCOME_WINDOW_BARS = 12     # §2.3: 12 bars (48 h)
TARGET_R_VALUES = (Decimal("1"), Decimal("1.5"), Decimal("2"))
_PERCENT_BUFFER = Decimal("0.001")   # 0.1% of entry
_ATR_BUFFER_MULT = Decimal("0.25")  # 0.25 × ATR20
_BAR_DUR = timedelta(hours=4)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class LiqBar:
    timestamp: datetime
    long: Decimal    # long-liquidation notional USD
    short: Decimal   # short-liquidation notional USD


@dataclass(frozen=True, slots=True)
class SetupESignal:
    """One detected episode (cascade + exhaustion) per §2.3."""
    symbol: str
    direction: Direction
    signal_index: int        # index into the FULL OHLCV candle array
    signal_ts: datetime      # timestamp of signal/exhaustion bar
    cascade_index: int       # index into the FULL OHLCV candle array
    cascade_extreme: Decimal # lowest low (LONG) or highest high (SHORT)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_liq_csv(path: Path) -> list[LiqBar]:
    """Load a Coinalyze liquidation CSV into sorted LiqBar objects."""
    rows: list[LiqBar] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: empty CSV")
        headers = {h.strip().lower() for h in reader.fieldnames}
        required = {"timestamp_utc", "long_notional_usd", "short_notional_usd"}
        missing = required - headers
        if missing:
            raise ValueError(f"{path}: missing columns {missing}")
        for i, row in enumerate(reader, start=2):
            ts_str = (row.get("timestamp_utc") or "").strip()
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"{path}: row {i}: bad timestamp {ts_str!r}") from exc
            rows.append(LiqBar(
                timestamp=ts,
                long=Decimal(str(row["long_notional_usd"])),
                short=Decimal(str(row["short_notional_usd"])),
            ))
    rows.sort(key=lambda r: r.timestamp)
    return rows


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _percentile_nearest(vals: list[Decimal], pct: int) -> Decimal:
    """Nearest-rank percentile (consistent with feasibility script)."""
    if not vals:
        return Decimal("0")
    s = sorted(vals)
    rank = max(0, int(len(s) * pct / 100) - 1)
    return s[rank]


def _cascade_extreme(candles_slice: Sequence[Candle], direction: Direction) -> Decimal:
    """Lowest low (LONG) or highest high (SHORT) over a candle span."""
    if direction == Direction.LONG:
        return min(c.low for c in candles_slice)
    return max(c.high for c in candles_slice)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def detect_setup_e_signals(
    symbol: str,
    candles: list[Candle],
    liq_bars: list[LiqBar],
    direction: Direction,
    discovery_cutoff_ts: datetime | None = None,
) -> list[SetupESignal]:
    """Detect non-overlapping Setup E episodes per §2.3.

    Returns signals whose signal bar is at or before discovery_cutoff_ts
    (if provided). signal_index and cascade_index are indices into `candles`.

    Trailing lookback for cascade/exhaustion detection uses the aligned
    sub-array (bars present in both candles and liq_bars). signal_index maps
    back to the full candle array so TradeSpec + simulate_trade work directly
    on `candles`.
    """
    # Build aligned arrays: only bars present in both datasets.
    liq_by_ts: dict[datetime, LiqBar] = {lb.timestamp: lb for lb in liq_bars}
    aligned_candle_idx: list[int] = []   # candle index in full array
    aligned_candles: list[Candle] = []
    aligned_liq: list[LiqBar] = []

    for ci, c in enumerate(candles):
        lb = liq_by_ts.get(c.timestamp)
        if lb is not None:
            aligned_candle_idx.append(ci)
            aligned_candles.append(c)
            aligned_liq.append(lb)

    n = len(aligned_candles)
    if n < TRAILING_BARS + 2:
        return []

    # Choose liq field by direction.
    def liq_val(lb: LiqBar) -> Decimal:
        return lb.long if direction == Direction.LONG else lb.short

    def is_cascade_bar(bar: Candle) -> bool:
        if direction == Direction.LONG:
            return bar.close < bar.open   # down bar
        return bar.close > bar.open       # up bar (SHORT)

    # Pass 1: cascade bar indices (in aligned array).
    cascade_aligned: list[int] = []
    for i in range(TRAILING_BARS, n):
        window = [liq_val(aligned_liq[j]) for j in range(i - TRAILING_BARS, i)]
        thr = _percentile_nearest(window, CASCADE_PCT)
        if liq_val(aligned_liq[i]) > thr and is_cascade_bar(aligned_candles[i]):
            cascade_aligned.append(i)

    # Pass 2: find exhaustion bar, build non-overlapping episodes.
    signals: list[SetupESignal] = []
    next_allowed = 0   # no new cascade may be processed before this index

    for ci_a in cascade_aligned:
        if ci_a < next_allowed:
            continue

        # Search for exhaustion bar.
        for j in range(ci_a + 1, min(ci_a + LOOKAHEAD_CAP, n)):
            window = [liq_val(aligned_liq[k]) for k in range(max(0, j - TRAILING_BARS), j)]
            thr25 = _percentile_nearest(window, EXHAUSTION_PCT)
            if liq_val(aligned_liq[j]) < thr25:
                signal_ts = aligned_candles[j].timestamp
                # Apply discovery cutoff (on signal bar timestamp).
                if discovery_cutoff_ts is not None and signal_ts > discovery_cutoff_ts:
                    break  # past cutoff — no need to look further on this cascade

                full_ci = aligned_candle_idx[ci_a]  # cascade index in full array
                full_si = aligned_candle_idx[j]     # signal index in full array

                extreme = _cascade_extreme(
                    aligned_candles[ci_a : j + 1], direction
                )
                signals.append(SetupESignal(
                    symbol=symbol,
                    direction=direction,
                    signal_index=full_si,
                    signal_ts=signal_ts,
                    cascade_index=full_ci,
                    cascade_extreme=extreme,
                ))
                next_allowed = j + 1
                break

        # Early termination: no point continuing past discovery cutoff.
        if (
            discovery_cutoff_ts is not None
            and aligned_candles[ci_a].timestamp > discovery_cutoff_ts
        ):
            break

    return signals


# ---------------------------------------------------------------------------
# Stop computation
# ---------------------------------------------------------------------------

def compute_setup_e_stop(candles: list[Candle], signal: SetupESignal) -> Decimal:
    """Compute stop price for signal: cascade_extreme ± min(0.1%×entry, 0.25×ATR20).

    Uses full OHLCV candle array for ATR computation and entry price lookup.
    Caller must verify signal.signal_index + 1 < len(candles).
    """
    entry_price = candles[signal.signal_index + 1].open
    atr_vals = _atr(candles, period=ATR_PERIOD)
    atr20 = atr_vals[signal.signal_index] or Decimal("0")
    buffer = min(_PERCENT_BUFFER * entry_price, _ATR_BUFFER_MULT * atr20)
    if signal.direction == Direction.LONG:
        return signal.cascade_extreme - buffer
    return signal.cascade_extreme + buffer
