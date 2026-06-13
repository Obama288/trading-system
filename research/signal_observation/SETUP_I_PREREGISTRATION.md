# Setup I — Pre-Registration (DRAFT)

Family: Price / Signed-Order-Flow Divergence Reversion (microstructure).
First test of the order-flow data class (Move B in DATA_CLASS_DECISION_FRAMEWORK).
Status: DRAFT — blocked on feasibility (aggTrades acquisition for BTC/ETH perp,
quality, episode counts, and a MANDATORY pre-lock cost test).
Governed by: docs/RESEARCH_CONSTITUTION.md v1.3. Follows §2 template.

## Campaign comparison-budget note (constitution §2.5)
SEVENTH hypothesis family on crypto-perp data this campaign (A, B, C, funding,
E, H all failed/parked). Six failures. A PASS here must be read against that
cumulative count and is "promising, not proven" until Stage 4. CRUCIAL
distinction from the six: this is the FIRST family using a data class other
than price/OHLCV-derived series — signed order flow is information absent from
every prior test. That is the entire reason to expect it might not die the same
way. If it dies too, the evidence for H1 (data class exhausted) becomes near-
decisive and Move D (stop active search) is the rational next step.

## 2.1 Hypothesis and mechanism

Hypothesis (one sentence): when price makes a directional move over a 1-hour
window but the signed order flow over that same window is strongly OPPOSITE in
sign (price up on net selling, or price down on net buying), price reverts
against the move over the following hours.

Mechanism / who pays: a directional price move not backed by aggressor flow is
driven by thin liquidity or stop-runs, while larger flow is already
transacting the other way. The trader chasing the price move (buying the new
high) supplies liquidity to those already trading against it; when the thin
move exhausts, price returns toward what the flow implied. The counterparty is
the momentum-chaser reacting to the price tape; the edge is on the side of the
flow that the tape hid.

Why this is NOT disguised price-action: the signal is built on SIGNED ORDER
FLOW (aggressor buy vs sell volume from the aggTrades isBuyerMaker flag), which
does not exist in OHLCV bars. It is a within-window contradiction between price
direction and flow direction — not a comparison of price structure across time
(which would be price-action and is excluded). BTC/ETH were used in Setup C,
but order flow was never analyzed on them; the data class is held-out even
though the symbols are not.

## 2.2 Primary metric and gate

- Primary metric: post-cost expectancy_R (simcore, NEXT_BAR_OPEN fill at the
  hour following signal close, moderate cost 8 bps/side, flats MTM,
  non-overlapping).
- Discovery gate: expectancy_R ≥ +0.05R AND above the random-baseline 95th
  percentile (2.4). Threshold set conservatively given family #7 and the
  intraday cost wall.
- MANDATORY pre-lock cost test (see 2.6): the median absolute price move
  following a signal must plausibly exceed round-trip cost; if not, DO NOT LOCK.

## 2.3 Signal definition (frozen at lock)

- Universe: BTCUSDT, ETHUSDT USD-M perpetuals (most liquid → least-noisy flow).
- Window: 1 hour. For each clock-hour, from aggTrades compute:
  - price move: sign of (hour close − hour open);
  - signed flow F = (taker-buy volume − taker-sell volume) over the hour, where
    isBuyerMaker=false ⇒ aggressor buy (taker-buy), isBuyerMaker=true ⇒
    aggressor sell (taker-sell);
  - flow imbalance ratio = F / (taker-buy + taker-sell volume), in [−1, +1].
- Signal (extreme-divergence only): a SHORT-reversion signal fires when price
  move is UP AND flow imbalance ratio is in the bottom 5th percentile of its
  trailing 30-day distribution (strong net selling on an up hour). LONG-
  reversion is the mirror (price down, flow imbalance top 5th percentile).
- Entry: next-hour open (constitution NEXT_BAR_OPEN). Stop: the signal hour's
  extreme (high for short, low for long) ± min(0.1% entry, 0.25×ATR20-on-1h)
  buffer. Targets 1R/1.5R/2R, primary gate at 1.5R. Outcome window: 6 hours
  (reversion is hypothesized as short-horizon). One observation per signal;
  overlap removed per constitution 3.8.

## 2.4 Random baseline
Per symbol: same number of signals placed at random hours NOT within 3 hours of
a real signal, same direction mix, same stop/target/window via simcore. 1000
resamples, seed 69 (constitution v1.3 default). Margin: observed expectancy_R
must exceed baseline p95.

## 2.5 Multiple-testing budget
PRIMARY variant: 1h window, 5th/95th percentile divergence threshold, 1.5R
target, 6h window, pooled BTC+ETH both directions. Declared non-primary
(diagnostic only): threshold {1st/99th, 10th/90th}; window {30m, 2h}; outcome
window {3h, 12h}; per-symbol split. V ≈ 1 primary + 8 diagnostic. Promotion of
any non-primary requires a fresh Stage-0 pre-registration and adds to the
campaign budget.

## 2.6 Windows, minimums, and the cost test
- Discovery: earliest ~70% of available aggTrades history for BTC+ETH perp
  [TBD-F at lock].
- Validation: following ~30%, non-overlapping [TBD-F].
- Recent-rerun (Stage 4): last 12 months (aggTrades history is deep).
- Dataset SHA-256: recorded at lock [TBD-F].
- Minimums: discovery ≥ 80, validation ≥ 40 non-overlapping signals.
- COST TEST (mandatory, pre-lock, this is the Setup F lesson hardened):
  feasibility must report the distribution of |next-6h price excursion| after
  signals (a COUNT/excursion statistic, NOT a strategy return — allowed at
  feasibility). If the median favorable excursion cannot plausibly exceed the
  16 bps round-trip cost, the family is NOT locked. Intraday signals trade
  often; this gate kills the family cheaply if the effect is sub-cost.

## 2.7 Kill criteria
- Discovery gate miss → PARK; strengthens H1 (data class exhausted) — record.
- Validation expectancy < 0 or sign flip → RETIRE.
- Stage 4 recent-rerun expectancy < 0 → historical-only.
- Stage 5: constitution v1.3 defaults + execution audit + hash check. NOTE:
  an intraday family raises live-execution realism concerns (latency, fill
  slippage) far above the 4H families — the pre-paper audit must weight this.

## Owner decisions required before lock
1. Confirm aggTrades acquisition is feasible at acceptable data volume (BTC+ETH
   tick history is large; feasibility reports size and a downsampling/streaming
   plan if needed).
2. The cost test (2.6): owner confirms the favorable-excursion distribution
   clears round-trip cost before lock. If borderline, do not lock.
3. Confirm windows, hashes at lock (seed already defaulted to 69).
