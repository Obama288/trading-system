# Data Source Survey II — Order Book, On-Chain/Whales, News, Sessions

Status: research note for owner, 2026-06-13. Extends FREE_DATA_SOURCE_SURVEY.md
to four classes raised after Setup H: paid order-book depth, on-chain/whale
flow, news/sentiment, and market-session timing. Verified against provider
pages on 2026-06-13.
Proposed location: `docs/DATA_SOURCE_SURVEY_II.md`

The job of this note is NOT to recommend buying anything. It is to record what
exists, at what cost, at what quality, and — most importantly — what
mechanism-and-overfitting risk each class carries before it could become a
pre-registered family.

---

## 1. Session timing — CHEAP, ALREADY HAVE, use only as pre-registered mechanism

No purchase needed. We already derive Asia/Europe/US/overlap from timestamps
(sessions.py). The honest use is NOT "slice every signal by session and keep
the best bucket" — that is selection bias and inflates the comparison budget by
×4. The honest use is: a family pre-registers, with a mechanism, that its edge
should concentrate in a named session ("liquidation reversals should be
stronger in low-liquidity Asia hours because thin books exaggerate forced
flow"), and the session split is the PRIMARY variant, declared before the run.
Verdict: usable now, free, but only as pre-registered mechanism, never as a
post-hoc filter. Add to the §2.5 budget when used.

## 2. On-chain / whale flow — REAL DATA, SEVERE MECHANISM TRAP

What exists: Whale Alert (free-ish real-time large-transfer pings), Glassnode
(free basic; Studio ~$49/mo; pro ~$999/mo), Nansen/Arkham (labeled wallets,
paid), CryptoQuant (exchange-flow focus, paid), Dune/Flipside (build-your-own
queries, free tiers), Apify scrapers (cheap, low reliability). Historical depth
and entity labeling are the paid features; raw pings are near-free.

The traps, in plain terms (and the sources themselves say this):
- **Visibility is not causal power.** On-chain flow tells you what happened, not
  what will happen. A raw address is "a string", not a whale, until it is
  labeled and clustered — and good labeling is exactly the paid part.
- **30–40% of whale alerts are non-market-impacting** (per industry sources):
  exchange deposits for derivatives, market-making, arbitrage, custody — not
  selling. "Big transfer to exchange = sell" is a documented misconception.
- **Latency / look-ahead.** By the time a transfer is observed, labeled, and
  delivered, the market has often already reacted. Backtesting on-chain
  timestamps must use the OBSERVABLE time, not the block time, or it embeds
  look-ahead — a subtle, easy-to-miss version of the trap that killed nothing
  yet only because we have not gone here.

Verdict: NOT a next step. It could pass our three conditions ONLY with (a) paid
labeling for a real counterparty story, (b) a mechanism beyond "whales move →
price follows", and (c) a backtest using observed-time, not block-time. That is
a large, paid, high-overfitting-risk project. Park as a future candidate with
these three preconditions written down. Do not pursue before the free
order-flow class (Setup I) resolves.

## 3. News / sentiment — DEFER, LOOK-AHEAD IS THE KILLER

What exists: CryptoPanic (aggregator, votes/sentiment, API + scrapers, cheap),
Santiment (since 2014, GraphQL, paid tiers), CryptoCompare news archive (to
2014), CoinMarketCap / alternative.me Fear & Greed Index (free, historical,
daily). Free structured news with clean history is limited; the cheap paths are
scrapers of dubious reliability.

The killer problem is look-ahead, worse than anywhere else:
- A news item's published timestamp is frequently LATER than the price move it
  "explains" (leaks, insider flow, the move precedes the headline). Backtests
  that align trades to publish-time silently trade on information that was not
  actionable then. This is extremely hard to audit and very easy to fool
  yourself with.
- "News moves markets" is a truism, not a mechanism with a counterparty.
- Sentiment is a near-infinite feature space (sources, scoring, windows,
  keyword sets) — fertile ground for overfitting; something will always fit.

The one low-risk exception: the Fear & Greed Index is a single, free, daily,
historical series — usable as a regime CONTEXT variable (like vol regime in
Setup H), not as a news-event signal. That sidesteps the look-ahead problem
because it is a slow daily aggregate, not an event timestamp.

Verdict: news-event trading is DEFERRED until there is (a) a concrete mechanism
with a counterparty and (b) a source with reliable actionable-time stamps. The
Fear & Greed Index may be used earlier as a regime context input, pre-
registered, if a family has a mechanism for sentiment-regime conditioning.

## 4. Paid order-book depth — the genuine, narrow paid frontier

(From FREE_DATA_SOURCE_SURVEY.md §2, restated.) Historical L2/L3 depth is the
one class that is genuinely behind a paywall and genuinely less picked-over:
Tardis.dev, CoinAPI, Crypto Lake (free sample only), CoinGlass. It enables
book-imbalance, vanishing-liquidity, and true slippage/queue-position signals.
But it is HFT territory on majors; retail latency likely loses the fast version.
Verdict unchanged: pursue ONLY if a Setup-I-class flow result specifically
demands depth, as a budgeted experiment with a kill date.

## 5. Ranking the four by (cost, mechanism clarity, overfitting risk)

| Class | Cost | Mechanism/counterparty | Overfitting/look-ahead risk | Next-step rank |
|---|---|---|---|---|
| Session timing | free | only if pre-registered | budget inflation (×sessions) | usable now, as mechanism |
| Fear&Greed regime | free | weak, context-only | low (slow daily) | usable as context |
| Order-book depth | high paid | clear (book pressure) but HFT-contested | medium | only on demand from a flow result |
| On-chain/whale | mid-high paid | trap-laden, needs labeling | high (block-time look-ahead) | parked w/ 3 preconditions |
| News/sentiment events | mixed | truism, weak | severe look-ahead | deferred |

## 6. Recommendation

1. Finish Setup I (free order flow) first. It is the cheapest test of the one
   unexplored class and resolves whether microstructure has any life for us
   before any money is spent.
2. Session timing and Fear&Greed are free and may enter a FUTURE family as
   pre-registered mechanism/context — not as post-hoc filters. They do not
   justify their own family today.
3. Order-book depth: hold for an on-demand, budgeted experiment, only if a flow
   result asks for depth.
4. On-chain/whale and news/sentiment: do not pursue now. Each carries a
   specific, severe trap (block-time look-ahead; publish-time look-ahead) and
   needs a named mechanism + a clean-timestamp source before it could pass our
   three conditions. Recorded here so the ideas are not lost and the
   preconditions are explicit.

## 7. The principle this survey reinforces

Every class here is "available". Almost none is "good" without a mechanism and a
clean-time backtest. The constraint has never been data availability — it is
finding information the crowd lacks AND a counterparty who must lose AND an
effect above cost AND a backtest free of look-ahead. New data widens the search;
it does not relax that bar. Adding sessions, whales, or news without a
pre-registered mechanism would just be more lottery tickets, now also exposed to
look-ahead. The discipline does not change because the data is shinier.
