# Strategy Class Map

Status: REFERENCE, 2026-06-13. A map of crypto-edge classes, used at one moment
only — when choosing the next research direction — to check we are not ignoring
a whole class by inertia. NOT a to-do list, NOT a gate, NOT updated per session.

Three guards against this becoming dead weight:
1. An empty cell is normal and often correct. The goal is "not skip a class by
   ignorance", not "fill every cell". A discarded class with a written reason is
   a CLOSED cell, not a pending one.
2. This is a taxonomy (slow-changing reference); per-attempt verdicts live in
   RESEARCH_STATE.md, not here, so this file does not rot.
3. THIS LIST IS NOT COMPLETE. It is one framing built from a trading textbook.
   Crypto-native edges outside it exist (MEV, airdrop/incentive farming, new-
   listing front-running, DeFi-protocol anomalies, on-chain liquidity games).
   Treat the map as a reminder to look wider, never as a definition of "wide".

---

## Classes by WHAT you earn from (not by indicator)

| # | Class | You earn from | Our attempts | Retail-viable? |
|---|-------|---------------|--------------|----------------|
| 1 | Directional | predicting price direction | A,B,C,E,F,H,I (ALL 7) | proven hard — 7 deaths |
| 2 | Market-making | bid-ask spread + rebates | none | likely NO (HFT/colocation) |
| 3 | Arbitrage | same price two places (spot/perp, venue/venue) | none (F touched basis as directional, not as carry hold) | maybe, on thin instruments / 2-venue exec |
| 4 | Funding/yield harvesting | premium for holding delta-neutral | none (only tested funding as a signal) | plausibly — doesn't need direction |
| 5 | Event-driven | forced flows at known times (unlocks, index rebalances, expiries, listings) | none (E was forced-flow but not event-anchored) | plausibly — counterparty named by definition |
| 6 | Microstructure/execution | queue position, latency, liquidity provision | none (I uses flow as a directional signal) | likely NO (HFT) |
| 7 | Cross-sectional | relative performance, market-neutral | none | maybe — neutrality may survive what killed absolute |

## The key reading

All seven attempts sit in ONE column (directional). The seven deaths are
therefore evidence that DIRECTIONAL edge on this data class is exhausted — NOT
that "no edge exists". This sharpens the H1 reading in
DATA_CLASS_DECISION_FRAMEWORK: what is likely exhausted is a class of
STRATEGIES, not just a class of data. We may have knocked on one locked door
seven times without trying the other five.

## What this implies for the next fork (after Setup I)

- If Setup I (the 8th directional) also dies, the rational next move is a
  DIFFERENT COLUMN, not another directional on different data.
- Most promising unexplored columns for retail: #4 (funding/yield harvesting)
  and #5 (event-driven) — both earn without predicting direction, so they do
  not obviously share the directional death. #3 (arbitrage) and #7
  (cross-sectional) are secondary candidates.
- #2 and #6 are likely closed for a non-colocated retail operator — record the
  reason, do not revisit without a latency story.

## The hard constraint that does not change with class

A new class still must clear the four-part bar (mechanism + counterparty +
information-the-crowd-lacks + effect-above-cost) and a look-ahead-clean
backtest. CRUCIALLY: classes #2–#7 may not fit the current signal-stop-target
simulator (simcore) at all — market-making and carry have continuous PnL and
inventory, not entries and exits. Pursuing them may require building new
measurement, not just a new detector. Choosing a class because simcore can
measure it would be searching under the lamppost. Decide by where edge plausibly
is, then build the measurement, not the reverse.
