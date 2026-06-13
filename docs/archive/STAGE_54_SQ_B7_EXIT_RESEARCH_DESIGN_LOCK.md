# Stage 54-SQ-B7-DL - Exit Research Design Lock

## 1. Stage Objective

Stage:
54-SQ-B7-DL.

Status:
Docs-only design lock for a bounded exit-logic research stage.

Objective:
Define one strictly bounded research stage for exit handling on the already
validated high-volatility Setup B observation subset.

This stage is for frozen high-vol Setup B entries only. It does not implement
exit logic, does not change the detector, and does not authorize paper trading,
runtime wiring, private API use, exchange-account access, or live trading.

Live trading remains NO-GO.

If this document conflicts with `docs/PROGRESS.md`, `docs/PROGRESS.md` wins.

## 2. Current Evidence

B5 high-vol validation evidence:
- validation high-vol observations: n = 62;
- validation target: 1.5R;
- raw 1.5R expectancy: +0.008064516129032258064516129032R;
- B5 formal validation gate passed against the conditional random baseline;
- the margin was weak and exploratory only.

B6 cost-aware evidence:
- optimistic cost, 0.04R round trip: -0.03193548387096774193548387097R;
- moderate cost, 0.08R round trip: -0.07193548387096774193548387097R;
- conservative cost, 0.12R round trip: -0.1119354838709677419354838710R;
- cost-adjusted edge is negative under all scenarios.

Flat-trade MFE evidence from B6:
- flat_count: 40;
- median_flat_mfe_r: 0.763110634974942283868400540R;
- flat MFE >= 0.7R: 52.5 percent;
- flat MFE >= 1.0R: 25 percent;
- near_win flats: 19;
- dead_flat flats: 0.

B6 decision:
B7_EXIT_RESEARCH_LONG_SHOT.

Interpretation:
B7 is a long-shot exit research stage only. It does not claim edge, profitability,
paper readiness, trading readiness, live readiness, or runtime readiness.

## 3. Frozen Components

B7 must not change:
- Setup B detector;
- entry logic;
- pivot trend logic;
- pullback logic;
- BOS logic;
- stop placement;
- volatility-regime definition;
- high-vol threshold semantics;
- 4H timeframe;
- BTCUSDT, ETHUSDT, and SOLUSDT symbol set;
- validation and discovery windows;
- local data files;
- conditional random baseline bucket matching;
- private/runtime/execution scope.

B7 must not use:
- private API;
- API keys or secrets;
- account data;
- balances;
- positions;
- orders;
- cancels;
- set_leverage;
- runtime wiring;
- paper execution;
- live trading.

## 4. Exit Variants To Test

B7 may test exactly three variants, no more.

### Variant A - Fixed 1R Target

Rules:
- entry unchanged;
- stop unchanged;
- target = 1R;
- timeout = 10 bars;
- cost scenarios same as B6.

Purpose:
Check whether the already observed MFE shape is better captured by a smaller
fixed target without changing entries or filters.

### Variant B - Protective Pullback After 0.7R

Rules:
- entry unchanged;
- stop unchanged;
- if MFE reaches >= 0.7R, activate protective exit;
- if price later retraces to +0.3R before target, stop, or timeout, exit at
  +0.3R;
- target remains 1.5R if reached before the protective exit;
- timeout remains 10 bars;
- stop-first same-candle ambiguity remains conservative.

Purpose:
Test whether flat trades with meaningful MFE can be harvested without changing
entry, stop, target, volatility tag, or data.

### Variant C - Breakeven After 1R

Rules:
- entry unchanged;
- stop unchanged until price reaches +1R;
- after +1R is reached, stop moves to breakeven;
- target remains 1.5R;
- timeout remains 10 bars;
- stop-first same-candle ambiguity remains conservative.

Purpose:
Test whether the high-vol subset benefits from defensive stop movement after a
strong enough favorable move, without adding new filters or changing entry
logic.

## 5. Random Baseline Rule

Each exit variant must be tested against a conditional random baseline using the
same exit logic.

Required baseline controls:
- same symbol and direction bucket matching as the existing random baseline;
- same high-vol validation subset size requirement;
- same local 4H data source;
- deterministic seeded randomness;
- same cost assumptions;
- same timeout;
- same stop-first ambiguity rule.

If an exit variant improves Setup B but the conditional random baseline improves
equally or more under the same exit logic, the variant does not pass.

## 6. Cost Model

Use the same B6 round-trip cost assumptions in R units:
- optimistic: 0.04R;
- moderate: 0.08R;
- conservative: 0.12R.

Primary gate:
Moderate cost, 0.08R.

Report all three scenarios. Do not hide raw pre-cost metrics.

## 7. B7 Pass Gate

At least one variant must satisfy all conditions:
- post-cost expectancy > 0 under moderate 0.08R cost;
- post-cost expectancy beats conditional random p75 under the same exit logic;
- sample size remains n = 62;
- result does not depend on changing entry, filter, data, timeframe, symbols, or
  detector parameters;
- report labels the result as a research candidate only, not paper-ready.

Passing B7 does not authorize paper trading, runtime wiring, private API use, or
live trading.

## 8. B7 Fail Gate

If no variant passes:
- retire high-vol Setup B fully;
- move to Setup C design lock;
- no B7b or B7c rescue stage.

Failure must be recorded plainly. Do not soften a failed result with additional
subgroup slicing or parameter changes.

## 9. Anti-Overfitting Rules

B7 anti-overfitting rules:
- no more than three exit variants;
- no target sweeps;
- no threshold sweeps;
- do not change 0.7R, 0.3R, or 1R after seeing results;
- no adding filters from B6 output;
- no subgroup slicing;
- no changing volatility regime definition;
- no changing validation/discovery windows;
- no changing data files;
- no paper trading claim;
- no live trading claim.

Any future parameter relaxation or new exit idea requires a new hypothesis
document after B7 is accepted or retired.

## 10. Future Path

If B7 passes:
- require independent review;
- do not mark the result paper-ready;
- next stage must either validate the exit candidate out-of-sample or define a
  forward-observation plan;
- no runtime or trading integration is authorized by the pass.

If B7 fails:
- retire the current high-vol Setup B definition fully;
- begin Setup C design lock as a separate hypothesis;
- do not create B7b/B7c rescue stages.

## 11. Next-Stage Implementation Guidance

Possible next stage:
Stage 54-SQ-B7 should implement the three frozen exit variants and the matching
conditional random baselines as research-layer analysis only.

Allowed future implementation scope:
- local JSON/CSV artifacts only;
- local 4H data only;
- no downloads;
- no detector changes;
- no entry/filter changes;
- no target or threshold sweeps;
- no runtime wiring;
- no private API.

Likely future files:
- `research/signal_observation/setup_b_exit_research.py`;
- `research/signal_observation/run_setup_b_exit_research.py`;
- `tests/research/test_signal_observation_setup_b_exit_research.py`;
- output artifacts under `research/signal_observation/output/bitget/`.

Forbidden future scope unless a separate Human Owner-approved stage changes it:
- `apps/`;
- `libs/`;
- `config/`;
- `infra/`;
- `alembic/`;
- runtime services;
- risk_engine;
- execution_service;
- orchestrator;
- position_manager;
- kill_switch;
- private exchange clients;
- account, balance, position, order, cancel, or set_leverage paths.
