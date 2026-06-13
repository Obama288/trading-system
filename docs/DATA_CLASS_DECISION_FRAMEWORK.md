# Data-Class Decision Framework

Status: discussion document for owner, 2026-06-13. Not a decision; a frame for
one. Follows STRATEGIC_REVIEW_2026-06.md, after Setup E PARK, Setup G dead
(no free data), Setup F feasible-but-cost-bound.
Proposed location if kept: `docs/DATA_CLASS_DECISION_FRAMEWORK.md`

---

## 1. Why we are here

The search has been paused — deliberately — to answer a deeper question than
"which signal family next?". The new question:

> **On what data class can an edge plausibly exist for our trading profile,
> and is acquiring that data worth it before any edge is proven?**

The record forcing this question:

| Family | Data class | Outcome | What killed it |
|---|---|---|---|
| A, B | 4H OHLCV majors | retired | no edge (price-action) |
| C (TSMOM) | 4H OHLCV majors | historical-only | died on recent regime |
| Funding norm. | funding + OHLCV | NO-GO | weak |
| E (liquidations) | free 4H liq + OHLCV | PARK | below random baseline |
| F (basis) | 4H spot+perp majors | feasible but **basis ≈ 4-5 bps < 16 bps round-trip cost** |
| G (options) | — | dead | no free historical positioning data |

Two distinct walls, not one:
- **Edge wall** (A, B, C, E, funding): the signal isn't there, or is too weak.
- **Cost wall** (F): the signal may be there but is smaller than the spread it
  must pay to trade.
- **Data wall** (G, and most richer sources below): the data needed to even
  test the hypothesis is paid.

## 2. The honest read on 4H OHLCV majors

Five edge-wall failures on the most-watched series in crypto is strong
evidence: **simple, unconditional signals on liquid-major 4H bars are
arbitraged out.** This should now be treated as established for this project.
Continuing to test new families on this exact data class is low expected value.

That does NOT mean "no edge anywhere" — it means the cheap, public, coarse
corner is picked clean. Which is unsurprising: it is the corner everyone else
also searches first and for free.

## 3. The three explanations, now scored against evidence

From the strategic review:

- **H1 (data class too efficient).** Strongly supported for 4H majors
  specifically. The cost wall in F is a sharp instance: even where structure
  exists, it's below cost on majors.
- **H2 (resolution too coarse / data too poor).** Plausible and now the most
  actionable. F's basis is tiny at 4H bar-close but intrabar dislocations and
  finer venues may be larger; E used only ~8 months of free liquidation data.
  The fix here is a *better data class*, not a new family.
- **H3 (edge is conditional, not unconditional).** Live hint from Setup C's
  real regime dependence. Cheapest to test — needs no new data, only a
  regime-gated re-pre-registration of an existing family.

These rank-order the options below.

## 4. The realistic moves, by cost and expected value

### Move A — Test H3 first (cheapest, no new data)
Re-pre-register Setup C (or another died-but-not-cost-bound family) WITH a
regime gate, as a fresh Stage 0 candidate (recent windows are now seen, so it
counts against the cumulative comparison budget, constitution v1.2). Cost:
days of work, zero data spend. Value: directly tests the one explanation we
have positive evidence for. **Recommended first** precisely because it is cheap
and evidence-backed.

### Move B — Go finer on a data class we can still get free
Before paying, exhaust the free-but-finer frontier: 1m/5m Binance OHLCV
(free, full history) for intraday-microstructure or basis-intrabar effects;
funding + OI + basis *combined* as a multi-signal state rather than each alone.
Cost: moderate engineering (simcore already handles any timeframe), zero data
spend. Value: tests H2 without committing money. Caveat: finer bars raise the
cost wall too (more trades, more spread) — any candidate here must clear the
cost test up front, as F failed to.

### Move C — Pay for a richer data class (only if A and B disappoint)
The repo already scouted this for Setup E (RESEARCH_STATE.md): Hyperliquid L2
order book + trades from 2024-10 (via Tardis, paid), CoinGlass aggregated
liquidations ($29-699/mo), Allium on-chain (paid, unclear depth). This is the
H2 fix at its strongest — order-book/event-level data is genuinely less
picked-over than OHLCV. Cost: real money + real engineering, BEFORE any edge is
proven. Value: highest ceiling, highest risk. **Only justified if A and B both
fail and you are willing to fund a speculative search.**

### Move D — Stop active search, harden what exists
A legitimate choice: accept that no edge has cleared the pipeline, freeze
research, and instead close the pre-paper audit items (R1 signal-source, R2
account authority) so that IF an edge appears later the machine is ready. Cost:
low. Value: preserves optionality, spends nothing on speculative data.

## 5. The decision, framed

Two questions, in order:

1. **Have we exhausted the free frontier?** Moves A and B cost no data money
   and test the two explanations with the most support (H3, H2). If either
   produces a candidate that passes the §4-strategic-review test ("why won't
   this die like the others?") AND clears the cost wall up front — continue.
2. **Only if A and B disappoint:** is the expected value of a *paid* speculative
   search (Move C) positive for you, given five-plus failures? This is a
   capital-allocation question, not a research question. A rational answer can
   be "no — Move D instead."

## 6. Recommendation (for discussion)

1. Do Move A now: regime-gated re-pre-registration of Setup C. Cheap, tests our
   best-supported hypothesis, uses existing data and simcore.
2. In parallel-of-thought, scope Move B: one finer-data candidate (e.g.
   intrabar basis or a combined funding+OI+basis state), with the cost test
   applied BEFORE locking — if the effect can't plausibly exceed round-trip
   cost, don't lock it.
3. Defer Move C until A and B resolve. If you reach it, treat the data spend as
   an explicit budgeted experiment with a kill date, not an open commitment.
4. Keep Move D as the honorable floor: there is no shame in a system whose
   current output is "no tradeable edge found yet." That is the system working.

## 7. The one principle under all of this

We have built a machine that refuses to trade noise. Its value to date is the
losses it prevented, not the gains it made — and that is correct for this
stage. The data-class decision is about where to point that machine next, not
about forcing it to bless something. Point it at the cheapest unexplored corner
with the clearest mechanism, demand the cost test up front, and let it keep
saying "no" until something honestly survives.
