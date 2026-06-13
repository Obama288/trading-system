"""Tests for Setup H regime-gated TSMOM detector.

All expectations are derived by hand from the fixture values defined below.
Fixtures use reduced parameters (atr_period=2, median_window=3, lookback=1,
rebalance_every=2) to keep warmup small and enable manual verification.

Standard parameters via hand calculation
-----------------------------------------
With atr_period=2, median_window=3, lookback=1, rebalance_every=2:
  warmup = max(lookback, atr_period-1 + median_window-1)
         = max(1, 1+2) = 3

Wilder ATR period=2:
  ATR[1] = (TR[0] + TR[1]) / 2
  ATR[i] = (ATR[i-1] * 1 + TR[i]) / 2

For a candle with close=c, high=c+h, low=c-h (symmetric HL):
  TR[0] = 2h (no previous close)
  TR[i] = max(2h, |c+h - prev_close|, |c-h - prev_close|)

For constant-price candles (close=100, h=1):
  TR[i] = max(2, 1, 1) = 2
  ATR[1] = 2.0  →  vol_proxy[1] = 2/100 = 0.020

LOW-VOL fixture (bars 0-2 wide, bar 3 narrow):
  Bars 0-2: close=100, h=1  →  ATR[1]=ATR[2]=2.0  →  vp[1]=vp[2]=0.020
  Bar 3:    close=101, h=0.5 (H=101.5, L=100.5)
    TR[3] = max(1, |101.5-100|, |100.5-100|) = max(1, 1.5, 0.5) = 1.5
    ATR[3] = (2*1+1.5)/2 = 1.75  →  vp[3] = 1.75/101 = 0.01733...
  trailing_median(window=3, index=3) = median of [vp[1], vp[2], vp[3]]
    = median of [0.020, 0.020, 0.01733] = 0.020
  0.01733 < 0.020  →  LOW ✓

HIGH-VOL fixture (bars 0-2 narrow, bar 3 wide):
  Bars 0-2: close=100, h=0.5  →  ATR[1] = (1+1)/2 = 1.0  →  vp[1]=vp[2]=0.010
  Bar 3:    close=101, h=5 (H=106, L=96)
    TR[3] = max(10, |106-100|, |96-100|) = max(10, 6, 4) = 10
    ATR[3] = (1*1+10)/2 = 5.5  →  vp[3] = 5.5/101 ≈ 0.05446
  trailing_median(window=3, index=3) = median of [0.010, 0.010, 0.05446] = 0.010
  0.05446 >= 0.010  →  HIGH ✓
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from research.signal_observation.candles import Candle
from research.signal_observation.setup_h_detector import (
    GatedObs,
    COST_BPS,
    build_gated_obs,
    classify_regime,
    obs_expectancy,
    percentile_of,
    shuffled_regime_baseline,
    trailing_median,
)


# ---------------------------------------------------------------------------
# Candle factory helpers
# ---------------------------------------------------------------------------

_BASE_TS = datetime(2020, 1, 1, tzinfo=UTC)
_4H = timedelta(hours=4)


def _candle(
    index: int,
    *,
    close: float = 100.0,
    hl_half: float = 1.0,  # half of H-L range (symmetric)
    cutoff_ts: datetime | None = None,
) -> Candle:
    ts = _BASE_TS + index * _4H
    c = Decimal(str(close))
    h = Decimal(str(hl_half))
    return Candle(
        timestamp=ts,
        open=c,
        high=c + h,
        low=c - h,
        close=c,
        volume=Decimal("1000"),
    )


def _candles_uniform(
    count: int,
    *,
    close: float = 100.0,
    hl_half: float = 1.0,
) -> list[Candle]:
    return [_candle(i, close=close, hl_half=hl_half) for i in range(count)]


def _make_obs(
    *,
    symbol: str = "TSTSYM",
    bar_index: int = 0,
    timestamp: datetime | None = None,
    regime: str = "LOW",
    direction_signal: int = 1,
    direction_gated: int | None = None,
    interval_return: str = "0.05",
    vol_proxy: str = "0.02",
    turnover_ungated: int = 1,
    turnover_gated: int = 1,
) -> GatedObs:
    if direction_gated is None:
        direction_gated = direction_signal if regime == "LOW" else 0
    return GatedObs(
        symbol=symbol,
        bar_index=bar_index,
        timestamp=timestamp or _BASE_TS,
        regime=regime,
        direction_signal=direction_signal,
        direction_gated=direction_gated,
        interval_return=Decimal(interval_return),
        vol_proxy=Decimal(vol_proxy),
        turnover_ungated=turnover_ungated,
        turnover_gated=turnover_gated,
    )


# ---------------------------------------------------------------------------
# trailing_median tests
# ---------------------------------------------------------------------------

class TestTrailingMedian:
    def test_odd_window_returns_middle_value(self):
        series = [Decimal("1"), Decimal("3"), Decimal("5")]
        assert trailing_median(series, 2, 3) == Decimal("3")

    def test_even_window_returns_average_of_two_middle(self):
        series = [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")]
        result = trailing_median(series, 3, 4)
        assert result == Decimal("2.5")

    def test_returns_none_when_index_too_small_for_window(self):
        series = [Decimal("1"), Decimal("2"), Decimal("3")]
        # window=3 at index 1 → start = -1 → None
        assert trailing_median(series, 1, 3) is None

    def test_returns_none_when_not_enough_non_none_values(self):
        series = [None, Decimal("1"), None, Decimal("2")]
        # window=3 at index 3 → slice [1..3] = [Decimal('1'), None, Decimal('2')]
        # only 2 non-None values but window=3
        assert trailing_median(series, 3, 3) is None

    def test_excludes_none_values_from_count_when_within_window(self):
        # window=2: need exactly 2 non-None values; None in window makes it None
        series = [Decimal("1"), None, Decimal("3")]
        assert trailing_median(series, 2, 2) is None

    def test_window_of_one_returns_that_value(self):
        series = [Decimal("1"), Decimal("7"), Decimal("3")]
        assert trailing_median(series, 2, 1) == Decimal("3")

    def test_uses_only_trailing_window_not_full_series(self):
        # [100, 200, 300, 1, 2, 3] window=3 at index 5 → slice [3,4,5] = [1,2,3]
        series = [Decimal(x) for x in (100, 200, 300, 1, 2, 3)]
        result = trailing_median(series, 5, 3)
        assert result == Decimal("2")

    def test_unordered_values_are_sorted_correctly(self):
        series = [Decimal("5"), Decimal("1"), Decimal("9"), Decimal("3"), Decimal("7")]
        # window=5 → sorted [1,3,5,7,9] → median = 5
        assert trailing_median(series, 4, 5) == Decimal("5")


# ---------------------------------------------------------------------------
# classify_regime tests
# ---------------------------------------------------------------------------

class TestClassifyRegime:
    def test_strictly_below_median_is_low(self):
        assert classify_regime(Decimal("0.019"), Decimal("0.020")) == "LOW"

    def test_equal_to_median_is_high(self):
        assert classify_regime(Decimal("0.020"), Decimal("0.020")) == "HIGH"

    def test_above_median_is_high(self):
        assert classify_regime(Decimal("0.025"), Decimal("0.020")) == "HIGH"

    def test_zero_proxy_below_any_positive_median_is_low(self):
        assert classify_regime(Decimal("0"), Decimal("0.001")) == "LOW"


# ---------------------------------------------------------------------------
# build_gated_obs: structural tests
# ---------------------------------------------------------------------------

SMALL_PARAMS = dict(
    atr_period=2,
    median_window=3,
    lookback=1,
    rebalance_every=2,
)
# warmup = max(1, 1+2) = 3; first rebalance at index 3


class TestBuildGatedObsStructure:
    def _build(self, candles: list[Candle], *, cutoff: datetime | None = None):
        kw = dict(SMALL_PARAMS)
        if cutoff is not None:
            kw["cutoff"] = cutoff
        return build_gated_obs(candles, symbol="TST", **kw)

    def test_empty_sequence_returns_empty(self):
        obs = build_gated_obs([], symbol="TST", **SMALL_PARAMS)
        assert obs == []

    def test_too_short_for_warmup_returns_empty(self):
        # warmup=3, need at least warmup + rebalance_every + 1 = 6 candles for 1 obs
        candles = _candles_uniform(5)
        obs = self._build(candles)
        assert obs == []

    def test_rebalance_bars_step_by_rebalance_every(self):
        candles = _candles_uniform(20)
        obs = self._build(candles)
        assert len(obs) >= 2, "expected at least 2 observations"
        for i in range(len(obs) - 1):
            assert obs[i + 1].bar_index - obs[i].bar_index == 2  # rebalance_every

    def test_first_obs_bar_index_equals_warmup(self):
        candles = _candles_uniform(20)
        obs = self._build(candles)
        assert obs[0].bar_index == 3  # warmup=3

    def test_obs_bar_index_increases_monotonically(self):
        candles = _candles_uniform(30)
        obs = self._build(candles)
        for i in range(len(obs) - 1):
            assert obs[i + 1].bar_index > obs[i].bar_index

    def test_cutoff_excludes_bar_beyond_cutoff(self):
        candles = _candles_uniform(20)
        # cutoff = timestamp of bar 5; bar at index 3 has outcome at 5 = cutoff (≤ ok)
        # bar at index 5 has outcome at 7 = after bar 5; the bar itself IS at cutoff → OK
        # bar at index 7 has timestamp AFTER bar 5 cutoff → excluded
        cutoff_ts = _BASE_TS + 5 * _4H  # timestamp of bar 5
        obs = self._build(candles, cutoff=cutoff_ts)
        for o in obs:
            assert o.timestamp <= cutoff_ts

    def test_cutoff_excludes_obs_whose_outcome_exceeds_cutoff(self):
        candles = _candles_uniform(20)
        # cutoff = timestamp of bar 4
        # bar at index 3 → outcome at index 5 → bar 5 ts = base + 5*4H > cutoff → excluded
        # So the only way to get an obs at index 3 is if outcome bar (3+2=5) has ts <= cutoff
        # cutoff = bar 4 ts. bar 5 ts > bar 4 ts → obs at index 3 excluded
        cutoff_ts = _BASE_TS + 4 * _4H
        obs = self._build(candles, cutoff=cutoff_ts)
        # bar at index 3 has outcome at bar 5 whose ts > cutoff → no obs
        assert all(o.bar_index != 3 for o in obs)

    def test_symbol_propagated_to_all_obs(self):
        candles = _candles_uniform(20)
        obs = build_gated_obs(candles, symbol="XYZUSDT", **SMALL_PARAMS)
        assert all(o.symbol == "XYZUSDT" for o in obs)

    def test_timestamp_matches_candle_open_time(self):
        candles = _candles_uniform(20)
        obs = self._build(candles)
        for o in obs:
            assert o.timestamp == candles[o.bar_index].timestamp


# ---------------------------------------------------------------------------
# build_gated_obs: regime and gate tests
# ---------------------------------------------------------------------------

class TestBuildGatedObsRegimeAndGate:
    """
    LOW-VOL fixture (computed by hand in module docstring):
      Bars 0-2: close=100, h=1.0  →  vp[1]=vp[2]=0.020
      Bar  3:   close=101, h=0.5  →  vp[3] = 1.75/101 ≈ 0.0173  <  median 0.020  →  LOW
      Bars 4-5: close=102/103, h=1.0  (used only as outcome candles)
    """

    def _low_candles(self) -> list[Candle]:
        # 3 wide bars + 1 narrow rebalance bar + 2 outcome bars
        result: list[Candle] = []
        for i, (c, h) in enumerate([
            (100.0, 1.0),   # 0 - wide
            (100.0, 1.0),   # 1 - wide
            (100.0, 1.0),   # 2 - wide
            (101.0, 0.5),   # 3 - narrow (rebalance bar)
            (102.0, 1.0),   # 4 - outcome context
            (103.0, 1.0),   # 5 - outcome bar (3+rebalance_every=2)
        ]):
            result.append(Candle(
                timestamp=_BASE_TS + i * _4H,
                open=Decimal(str(c)),
                high=Decimal(str(c + h)),
                low=Decimal(str(c - h)),
                close=Decimal(str(c)),
                volume=Decimal("100"),
            ))
        return result

    def _high_candles(self) -> list[Candle]:
        # 3 narrow bars + 1 wide rebalance bar + 2 outcome bars
        result: list[Candle] = []
        for i, (c, h) in enumerate([
            (100.0, 0.5),   # 0 - narrow
            (100.0, 0.5),   # 1 - narrow
            (100.0, 0.5),   # 2 - narrow
            (101.0, 5.0),   # 3 - very wide (rebalance bar)
            (102.0, 0.5),   # 4
            (103.0, 0.5),   # 5
        ]):
            result.append(Candle(
                timestamp=_BASE_TS + i * _4H,
                open=Decimal(str(c)),
                high=Decimal(str(c + h)),
                low=Decimal(str(c - h)),
                close=Decimal(str(c)),
                volume=Decimal("100"),
            ))
        return result

    def test_low_vol_bar_has_regime_low(self):
        candles = self._low_candles()
        obs = build_gated_obs(candles, symbol="TST", **SMALL_PARAMS)
        assert len(obs) == 1
        assert obs[0].regime == "LOW"

    def test_high_vol_bar_has_regime_high(self):
        candles = self._high_candles()
        obs = build_gated_obs(candles, symbol="TST", **SMALL_PARAMS)
        assert len(obs) == 1
        assert obs[0].regime == "HIGH"

    def test_low_vol_direction_gated_equals_direction_signal(self):
        candles = self._low_candles()
        obs = build_gated_obs(candles, symbol="TST", **SMALL_PARAMS)
        assert len(obs) == 1
        # Direction signal is based on close[3] vs close[2]: 101 vs 100 → +1
        assert obs[0].direction_signal == 1
        assert obs[0].direction_gated == 1  # LOW → pass through

    def test_high_vol_direction_gated_is_zero(self):
        candles = self._high_candles()
        obs = build_gated_obs(candles, symbol="TST", **SMALL_PARAMS)
        assert len(obs) == 1
        # Direction signal: close[3]=101 vs close[2]=100 → +1
        assert obs[0].direction_signal == 1
        assert obs[0].direction_gated == 0  # HIGH → gate forces flat

    def test_interval_return_computed_from_close_prices(self):
        candles = self._low_candles()
        obs = build_gated_obs(candles, symbol="TST", **SMALL_PARAMS)
        # interval_return = close[5] / close[3] - 1 = 103/101 - 1
        expected = Decimal("103") / Decimal("101") - Decimal("1")
        assert obs[0].interval_return == expected

    def test_vol_proxy_is_positive(self):
        for candles in (self._low_candles(), self._high_candles()):
            obs = build_gated_obs(candles, symbol="TST", **SMALL_PARAMS)
            for o in obs:
                assert o.vol_proxy > Decimal("0")


# ---------------------------------------------------------------------------
# build_gated_obs: turnover tracking tests
# ---------------------------------------------------------------------------

class TestBuildGatedObsTurnover:
    """
    Construct 3 rebalance bars with known signals:
      Bar 3 (LOW, signal=+1): prev_ungated=0, prev_gated=0
        turnover_ungated = 1 (enter from flat)
        turnover_gated   = 1 (enter from flat)

      Bar 5 (HIGH, signal=+1): prev_ungated=+1, prev_gated=+1
        turnover_ungated = 0 (stay long, same direction)
        turnover_gated   = 1 (exit long to flat)

      Bar 7 (LOW, signal=+1): prev_ungated=+1, prev_gated=0
        turnover_ungated = 0 (stay long)
        turnover_gated   = 1 (enter from flat)
    """

    def _make_sequence(self) -> list[Candle]:
        """
        Ascending closes to give signal=+1 everywhere.
        Regime alternates LOW/HIGH/LOW by controlling H-L width.
        10 candles cover indices 0-9; rebalance bars at 3, 5, 7.
        """
        # hl_half schedule: [wide, wide, wide, narrow, wide, wide(=H), wide, narrow, wide, wide]
        params = [
            (100.0, 1.0),   # 0  wide
            (101.0, 1.0),   # 1  wide → vp[1] = 2/101
            (102.0, 1.0),   # 2  wide → vp[2] = 2/102
            (103.0, 0.01),  # 3  narrow rebalance (LOW regime expected)
            (104.0, 1.0),   # 4
            (105.0, 5.0),   # 5  wide rebalance (HIGH regime expected)
            (106.0, 1.0),   # 6
            (107.0, 0.01),  # 7  narrow rebalance (LOW regime expected)
            (108.0, 1.0),   # 8
            (109.0, 1.0),   # 9
        ]
        candles = []
        for i, (c, h) in enumerate(params):
            candles.append(Candle(
                timestamp=_BASE_TS + i * _4H,
                open=Decimal(str(c)),
                high=Decimal(str(c + h)),
                low=Decimal(str(c - h)),
                close=Decimal(str(c)),
                volume=Decimal("100"),
            ))
        return candles

    def test_first_obs_enter_from_flat_turnover_is_one(self):
        obs = build_gated_obs(self._make_sequence(), symbol="TST", **SMALL_PARAMS)
        first = obs[0]
        assert first.turnover_ungated == 1
        assert first.turnover_gated == 1

    def test_high_vol_obs_ungated_has_zero_turnover_when_same_direction(self):
        obs = build_gated_obs(self._make_sequence(), symbol="TST", **SMALL_PARAMS)
        # Second obs should be HIGH-VOL; ungated direction stays +1 → turnover_ungated=0
        high_obs = next((o for o in obs if o.regime == "HIGH"), None)
        assert high_obs is not None
        assert high_obs.turnover_ungated == 0

    def test_high_vol_obs_gated_has_turnover_one_when_exiting_long(self):
        obs = build_gated_obs(self._make_sequence(), symbol="TST", **SMALL_PARAMS)
        high_obs = next((o for o in obs if o.regime == "HIGH"), None)
        assert high_obs is not None
        # Exiting from +1 long to 0 flat = 1 turnover unit
        assert high_obs.turnover_gated == 1

    def test_low_vol_after_flat_gated_has_turnover_one(self):
        obs = build_gated_obs(self._make_sequence(), symbol="TST", **SMALL_PARAMS)
        low_obs = [o for o in obs if o.regime == "LOW"]
        assert len(low_obs) >= 2
        # Second LOW obs re-enters after HIGH flat
        second_low = low_obs[1]
        assert second_low.turnover_gated == 1


# ---------------------------------------------------------------------------
# obs_expectancy tests
# ---------------------------------------------------------------------------

class TestObsExpectancy:
    def test_empty_list_returns_none(self):
        assert obs_expectancy([], gated=True, cost_bps=Decimal("8")) is None

    def test_single_long_obs_gated(self):
        """
        direction_gated=+1, interval_return=0.05, vol_proxy=0.02, turnover_gated=1
        gross = 1 * 0.05 = 0.05
        cost  = 1 * 8/10000 = 0.0008
        net   = (0.05 - 0.0008) / 0.02 = 0.0492 / 0.02 = 2.46
        """
        o = _make_obs(
            regime="LOW",
            direction_signal=1,
            direction_gated=1,
            interval_return="0.05",
            vol_proxy="0.02",
            turnover_gated=1,
            turnover_ungated=1,
        )
        result = obs_expectancy([o], gated=True, cost_bps=Decimal("8"))
        expected = (Decimal("1") * Decimal("0.05") - Decimal("1") * Decimal("8") / 10000) / Decimal("0.02")
        assert result == expected

    def test_high_vol_obs_gated_contributes_zero_gross(self):
        """
        direction_gated=0, interval_return=0.10, turnover_gated=0
        gross = 0 * 0.10 = 0; cost = 0; net = 0 / vol_proxy = 0
        """
        o = _make_obs(
            regime="HIGH",
            direction_signal=1,
            direction_gated=0,
            interval_return="0.10",
            vol_proxy="0.03",
            turnover_gated=0,
            turnover_ungated=0,
        )
        result = obs_expectancy([o], gated=True, cost_bps=Decimal("8"))
        assert result == Decimal("0")

    def test_gated_outperforms_ungated_when_high_vol_has_negative_returns(self):
        """
        Two obs: LOW (positive return) + HIGH (negative return).

        Obs1 (LOW, signal=+1, prev dirs both 0):
          turnover_ungated=1, turnover_gated=1
          interval_return=0.05, vol_proxy=0.02

        Obs2 (HIGH, signal=+1, prev_ungated=+1, prev_gated=+1):
          turnover_ungated=0 (stay long), turnover_gated=1 (exit to flat)
          interval_return=-0.04, vol_proxy=0.03
        """
        obs1 = _make_obs(
            regime="LOW",
            direction_signal=1,
            direction_gated=1,
            interval_return="0.05",
            vol_proxy="0.02",
            turnover_ungated=1,
            turnover_gated=1,
        )
        obs2 = _make_obs(
            regime="HIGH",
            direction_signal=1,
            direction_gated=0,
            interval_return="-0.04",
            vol_proxy="0.03",
            turnover_ungated=0,
            turnover_gated=1,
        )
        gated_exp = obs_expectancy([obs1, obs2], gated=True, cost_bps=Decimal("8"))
        ungated_exp = obs_expectancy([obs1, obs2], gated=False, cost_bps=Decimal("8"))
        assert gated_exp is not None
        assert ungated_exp is not None
        assert gated_exp > ungated_exp

    def test_ungated_uses_direction_signal_not_gated(self):
        """On a HIGH obs, ungated still uses direction_signal (not 0)."""
        o = _make_obs(
            regime="HIGH",
            direction_signal=1,
            direction_gated=0,
            interval_return="0.05",
            vol_proxy="0.02",
            turnover_ungated=1,
            turnover_gated=1,
        )
        ungated = obs_expectancy([o], gated=False, cost_bps=Decimal("8"))
        # Should use direction_signal=1, not 0
        expected = (Decimal("1") * Decimal("0.05") - Decimal("1") * Decimal("8") / 10000) / Decimal("0.02")
        assert ungated == expected


# ---------------------------------------------------------------------------
# percentile_of tests
# ---------------------------------------------------------------------------

class TestPercentileOf:
    def test_value_above_all_returns_100(self):
        dist = [1.0, 2.0, 3.0]
        assert percentile_of(10.0, dist) == 100.0

    def test_value_below_all_returns_0(self):
        dist = [1.0, 2.0, 3.0]
        assert percentile_of(0.0, dist) == 0.0

    def test_value_equal_to_some_counts_strictly_below(self):
        dist = [1.0, 2.0, 2.0, 3.0]
        # values strictly below 2.0: only 1.0 → 1/4 = 25%
        assert percentile_of(2.0, dist) == 25.0

    def test_empty_distribution_returns_zero(self):
        assert percentile_of(5.0, []) == 0.0


# ---------------------------------------------------------------------------
# shuffled_regime_baseline tests
# ---------------------------------------------------------------------------

class TestShuffledRegimeBaseline:
    def _make_obs_list(self, *, n: int = 10, n_low: int = 5) -> list[GatedObs]:
        """Create n obs where first n_low are LOW, rest are HIGH."""
        result = []
        for i in range(n):
            regime = "LOW" if i < n_low else "HIGH"
            result.append(_make_obs(
                bar_index=i,
                regime=regime,
                direction_signal=1,
                direction_gated=1 if regime == "LOW" else 0,
                interval_return="0.02",
                vol_proxy="0.02",
                turnover_ungated=1 if i == 0 else 0,
                turnover_gated=1 if i == 0 else (1 if i == n_low else 0),
            ))
        return result

    def test_returns_n_resamples_values(self):
        obs = self._make_obs_list()
        dist = shuffled_regime_baseline({"TST": obs}, n_resamples=50, seed=1)
        assert len(dist) == 50

    def test_seeded_results_are_reproducible(self):
        obs = self._make_obs_list()
        dist1 = shuffled_regime_baseline({"TST": obs}, n_resamples=20, seed=42)
        dist2 = shuffled_regime_baseline({"TST": obs}, n_resamples=20, seed=42)
        assert dist1 == dist2

    def test_different_seeds_give_different_results(self):
        obs = self._make_obs_list(n=20, n_low=10)
        dist1 = shuffled_regime_baseline({"TST": obs}, n_resamples=20, seed=1)
        dist2 = shuffled_regime_baseline({"TST": obs}, n_resamples=20, seed=999)
        assert dist1 != dist2

    def test_zero_n_active_symbol_contributes_zeros(self):
        """Symbol with no LOW-VOL bars (n_active=0) produces zero contribution."""
        obs = self._make_obs_list(n=5, n_low=0)  # all HIGH
        dist = shuffled_regime_baseline({"TST": obs}, n_resamples=10, seed=1)
        assert len(dist) == 10
        # All values should be 0 (no active positions)
        assert all(v == 0.0 for v in dist)

    def test_multiple_symbols_contribute_independently(self):
        """With two symbols both having 5 obs each, should pool 10 obs per resample."""
        obs1 = self._make_obs_list(n=5, n_low=3)
        obs2 = self._make_obs_list(n=5, n_low=2)
        dist = shuffled_regime_baseline({"SYM1": obs1, "SYM2": obs2}, n_resamples=10, seed=1)
        assert len(dist) == 10
        # Just verify it runs without error and returns numeric values
        assert all(isinstance(v, float) for v in dist)
