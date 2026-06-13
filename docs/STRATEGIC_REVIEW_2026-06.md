# Strategic Review — What Four Negative Results Are Telling Us

Status: discussion document for owner, 2026-06-13. Not a constitution amendment,
not a decision record. Written to inform the next candidate choice.
Proposed location if kept: `docs/STRATEGIC_REVIEW_2026-06.md`

---

## 1. The scoreboard

Every edge family taken to a real test on public crypto-perp data has failed
to clear its gate:

| Family | Class | Data | Verdict |
|---|---|---|---|
| Setup A — breakout-retest | price-action | 4H OHLCV | retired |
| Setup B — pullback BOS / continuation | price-action | 4H OHLCV | retired |
| Setup C — TSMOM + vol targeting | price/trend | 4H OHLCV | historical-only (passed locked windows, failed recent-data rerun DR1) |
| Funding normalization | carry/positioning | funding + OHLCV | discovery WEAK, validation NO-GO |
| Setup E — post-liquidation reversal | forced-flow | liq + 4H OHLCV | PARK (−0.11R, below random baseline p95) |

Five honest attempts. Zero surviving edges. This is itself a result, and it
deserves to be read rather than worked around by reaching for candidate #6.

## 2. What the pattern actually rules out

Be precise about what has died, because the temptation is to over-conclude.

- **Price-derived signals on liquid majors at 4H are dead.** A, B, C all
  reduce to "structure in recent price predicts next price." Three independent
  formulations, three deaths. This is the strongest conclusion: it is well
  supported and should be treated as settled for this data class. Do not
  re-run price-action variants.
- **Setup C is the instructive one.** It PASSED locked discovery and validation
  and then died on recent data. That is not a methodology failure — it is the
  pipeline working. But it also means: even a signal that clears two locked
  windows can be a single-regime artifact. The 2022–2023 windows and the
  recent window were different regimes; the edge lived in one.
- **Two non-price families also failed** (funding, liquidations). This is the
  more sobering signal. The hope was that structural/forced-flow data would
  succeed where price failed. So far it has not — though note both were tested
  on coarse, short, free public data (Setup E: ~8 months of free Coinalyze 4H).

## 3. The honest diagnosis: three competing explanations

Before choosing the next candidate, decide which of these you believe, because
they imply different actions.

**H1 — The data class is too efficient.** Liquid majors on public 4H bars are
the most-watched series in crypto; any simple edge is arbitraged. If true, no
candidate on this data class will work, and choosing Basis or Options is just
buying lottery tickets in the same dead lottery.

**H2 — The signals are real but the resolution is too coarse.** 4H bars and
free, short, low-granularity feeds (8 months of liquidation data; funding
without order-book context) may be too blunt to see effects that exist at finer
timescales or require richer data. If true, the fix is a different DATA class
(tick/order-book, longer history, paid feeds) — not a different signal family
on the same bars.

**H3 — The edges are real and conditional.** Setup C's regime dependence
(C4 showed real regime effects) hints that unconditional strategies lose but
regime-conditioned ones might survive. If true, the next work is not a new
family but adding a regime gate to a previously-"failed" family and
re-pre-registering it honestly.

These are not mutually exclusive, but they rank-order the next move very
differently.

## 4. The test the next candidate must pass BEFORE it gets a pre-registration

To avoid candidate #6 being lottery ticket #6, require a written answer to one
question before locking anything:

> **Why will this not die the way the previous five did?**

A satisfactory answer names a concrete structural difference, not a hope.
Examples of satisfactory vs not:

- Basis / cash-and-carry: SATISFACTORY if the claim is "this is a cross-market
  financing spread, not a price-history signal, and the counterparty (leveraged
  long paying to hold synthetic exposure) is structurally present regardless of
  regime." NOT satisfactory if it is "basis sometimes mean-reverts and the
  charts look nice."
- Options / dealer hedging: SATISFACTORY if "dealer gamma hedging is a
  mechanically forced flow with a known sign around known expiry times — a
  calendar-anchored structural constraint absent from all five dead families."
  NOT satisfactory if the data path turns out to be unavailable, in which case
  it dies at feasibility regardless of mechanism.

If no candidate can answer this, that is decisive evidence for H1/H2 and the
right move is to step off this data class, not to test another family on it.

## 5. Recommendation (for discussion, not a decision)

1. Let the two feasibility passes (Basis, Options) finish — they are cheap and
   already running.
2. Before locking either, write the §4 answer for it. If neither answer is
   concrete, do not lock; pivot the question to data class (H2): what would it
   take to get longer history or finer granularity, and is that worth it given
   no edge has yet justified the cost?
3. Strongly consider explicitly testing H3 in parallel-of-thought: a
   regime-conditioned re-pre-registration of Setup C is arguably a better bet
   than a brand-new family, because C already showed *something* on locked
   windows. It would need a fresh pre-registration (the recent-data window is
   now seen) and must count against the comparison budget.
4. Keep expecting PARK. With five deaths, the base rate for the sixth is low.
   The system's value is not a winning strategy yet — it is that it has
   prevented five losing strategies from reaching real money. That is the
   correct thing for it to be doing right now.

## 6. What would change the picture

A single surviving edge through Stage 4 (recent data) changes everything,
because the machinery to exploit it (execution skeleton, kill switch, paper
harness) already exists and is audited-pending. The bottleneck is genuinely
the search, not the plumbing. So the resource question is narrow: is the
expected value of more searching on THIS data class positive, or is it time
to invest in a different data class? That is the real strategic fork, and it
should be decided explicitly rather than by momentum.
