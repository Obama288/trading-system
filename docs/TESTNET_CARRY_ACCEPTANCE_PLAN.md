# Testnet Carry Acceptance Plan

Status: DRAFT / ACCEPTANCE SPECIFICATION

Scope: future testnet/demo verification of two-legged perpetual funding carry
and cross-venue funding-dispersion execution. This document authorizes no API
call, credential use, runtime change, order, cancel, deployment, or readiness
promotion.

Current exchange gate:

- Bybit testnet is BLOCKED because usable testnet credentials are unavailable.
- Bitget Demo is PARKED / planning only.
- No scenario in this plan may run until the Human Owner separately authorizes
  Protected Lane work for one named environment and frozen implementation.

## 1. Purpose And Evidence Boundary

The plan tests whether a frozen implementation can control two coordinated
legs safely in an isolated exchange test environment. It applies to a long leg
on one venue/instrument and a short leg on another venue/instrument, including
same-venue demo variants where useful for plumbing verification.

Passing this plan is **implementation evidence** for the exact commit,
configuration, venue environments, instruments, and test interval recorded in
the run artifact. It may support claims about API compatibility, state-machine
correctness, failure containment, reconciliation, and observability.

Passing this plan is **not edge evidence**. Testnet/demo fills, order-book
depth, queue position, slippage, funding rates, mark prices, participant
behavior, and availability may differ materially from production. Testnet PnL,
fill rate, funding capture, and apparent profitability must never be used to
promote H1, estimate capacity, tune thresholds, or claim post-cost expectancy.
Edge evidence requires separately governed research on real public market data
with locked costs, windows, holdout, and gates under
`docs/RESEARCH_CONSTITUTION.md`.

## 2. Preconditions And Frozen Run Manifest

Before any run, create a reviewable run manifest outside logs containing only
non-secret metadata:

- owner authorization reference and approved Protected Lane scope;
- Git commit SHA and assertion that the working tree is clean;
- strategy family and immutable scenario identifier;
- venue names and explicit environment labels (`testnet` or `demo`);
- instrument identifiers, contract type, settlement asset, tick size, quantity
  step, minimum quantity, and minimum notional;
- configured leg ordering policy and hedge-ratio rule;
- maximum unhedged interval and maximum unhedged notional;
- retry, timeout, cancel/replace, and duplicate-request policy;
- kill-switch initial state and authoritative source;
- redaction policy version and correlation/run identifier;
- expected account baseline captured by reconciliation, without balances or
  account identifiers in committed artifacts;
- start/end UTC timestamps and operator identity by non-sensitive role label.

The manifest must not contain credentials, account IDs, balances, signed
payloads, request signatures, secret-derived values, or private endpoint
responses. Any implementation/configuration change invalidates the run and
requires a new manifest and full rerun.

## 3. Environment Isolation And Credential Hygiene

### 3.1 Isolation gates

- Use accounts created solely for the named testnet/demo environment.
- Run from an isolated process profile with no mainnet credentials present.
- Use separate environment variable names and configuration namespaces for
  each venue and environment.
- Do not reuse production account IDs, API keys, IP allowlists, webhooks,
  databases, queues, Redis namespaces, or log sinks.
- Persist test state only in an explicitly named disposable test database or
  schema. It must not share authoritative paper/live tables.
- Pin every REST and WebSocket base URL to an allowlisted testnet/demo host.
- Disable environment selection by strategy input, symbol metadata, redirect,
  or exchange response.

### 3.2 Credential gates

- Credentials are process-scoped secrets supplied outside Git and docs.
- Keys must be least-privilege and limited to trading in test funds; withdrawal
  and transfer permissions are forbidden.
- Secret presence is checked without logging value, length, prefix, suffix,
  hash, account identity, or derived signature.
- Logs, exceptions, traces, HTTP recordings, fixtures, screenshots, and CI
  artifacts must pass redaction review before retention.
- Credential rotation/revocation procedure must be recorded before the run.

### 3.3 No-mainnet guard

Execution must fail closed before authentication when any of these checks is
not satisfied:

1. Explicit environment is exactly an approved `testnet` or `demo` value.
2. REST and WebSocket hosts exactly match the venue-specific allowlist.
3. Hostnames, redirects, and resolved destinations do not match any production
   endpoint denylist entry.
4. Account/environment identity check returns the expected non-production
   classification where the venue exposes one.
5. A startup assertion confirms live mode is disabled and the project kill
   switch is authoritative and reachable.

Any ambiguity, redirect, missing identity signal, unsupported environment, or
configuration conflict is a hard stop. No fallback to a production endpoint is
permitted. Evidence must show that deliberate mainnet-host injection is
rejected before a private request or order attempt.

## 4. Common Invariants And Measurements

All scenarios must preserve these invariants:

- Decimal quantities and prices comply with instrument filters before submit.
- Every intent has a stable strategy ID, run ID, trade ID, leg ID, and
  idempotency key.
- Exactly one durable state transition represents each accepted exchange
  event; duplicate and out-of-order events are tolerated.
- Local state distinguishes intended, submitted, acknowledged, partially
  filled, filled, cancel-pending, canceled, rejected, unknown, and reconciled.
- Net exposure is computed from confirmed fills, never requested quantities.
- No retry creates additional economic exposure unless explicitly represented
  as a new replace intent.
- Unknown order or position state fails closed and enters reconciliation.
- The kill switch blocks new exposure at the last authoritative boundary.

Capture monotonic and UTC timestamps for intent, submit, acknowledgement, each
fill, cancel request, cancel acknowledgement, hedge request, hedge fill,
reconnect, reconciliation start/end, and kill-switch action. Record requested
and confirmed quantities, prices, fees/funding fields if supplied, error class,
retry count, residual exposure, and state transition. Sensitive values remain
redacted according to section 8.

The maximum unhedged interval is measured from the first confirmed fill that
creates net exposure until confirmed opposing fills reduce exposure within the
predeclared hedge tolerance. It is not measured from order submission. Its
numeric limit and allowed unhedged notional must be locked in the run manifest;
this document does not invent values before strategy risk limits are approved.

## 5. Acceptance Scenarios

Each scenario starts from a reconciled baseline, uses a unique scenario ID,
and ends with a second reconciliation proving no unexplained orders,
positions, or local state remain.

### T01 - Guarded startup

- Start with valid testnet/demo configuration and kill switch engaged.
- Verify connectivity classification and read-only reconciliation only after
  separate authorization permits private test access.
- Inject a production hostname, omitted environment, mismatched venue, and
  redirect response in offline/mocked guard tests.
- Pass: valid isolated configuration initializes without orders; every invalid
  case fails before private access; no secret appears in output.

### T02 - Place and close both legs

- Submit the predeclared first leg, observe confirmed fills, and size the
  second leg from confirmed first-leg quantity and locked hedge ratio.
- Verify both legs reach the intended hedge tolerance.
- Close using the frozen close policy and reconcile flat state.
- Pass: one intent per leg, compliant quantities, traceable acknowledgements,
  exposure within limit, and no residual order/position after close.

### T03 - First-leg partial fill

- Cause or simulate an acknowledged partial fill followed by delay or no
  further fill.
- Hedge only confirmed quantity; never hedge the unfilled request.
- Apply the frozen residual policy: wait, cancel remainder, or replace within
  locked time/notional limits.
- Pass: exposure timer starts at first fill, confirmed quantity drives hedge,
  residual is resolved, and no over-hedge or duplicate order occurs.

### T04 - Second-leg failure

- After a confirmed first-leg fill, force second-leg reject, timeout, transport
  ambiguity, unavailable instrument, and insufficient test balance as separate
  cases where the environment can represent them.
- Enter emergency hedge/unwind state; reconcile ambiguous requests before any
  retry; block unrelated new trades.
- Pass: exposure never exceeds locked interval/notional; system either obtains
  the hedge or unwinds the first leg; unresolved ambiguity triggers kill switch
  and operator escalation rather than blind retry.

### T05 - Maximum unhedged interval

- Delay second-leg confirmation across warning and hard-limit boundaries using
  deterministic fault injection where testnet cannot produce the timing.
- Pass: warning is observable before the limit; at the hard limit, new exposure
  is blocked and the frozen emergency policy executes exactly once.
- Fail: the timer resets on retry/reconnect, begins at submit rather than fill,
  or exposure remains open beyond the limit without terminal escalation.

### T06 - Cancel and replace

- Cancel an unfilled order, cancel a partially filled remainder, and replace at
  an allowed price without increasing target quantity.
- Exercise late fill during cancel and duplicate cancel acknowledgement.
- Pass: replacement quantity uses reconciled remaining exposure; late fills
  are incorporated; at most one active economic intent exists per residual.

### T07 - Funding events

- Hold reconciled opposing positions across an available testnet/demo funding
  boundary, if the venue emits such events.
- Capture event identity, venue timestamp, position quantity, rate/payment
  fields as supplied, and deduplicate replayed events.
- Reconcile cumulative funding records after reconnect/restart.
- Pass: each authoritative event is recorded once and attributed to the correct
  leg/trade without altering order state.
- If the environment does not provide credible funding events, mark this
  scenario `NOT TESTABLE`; synthetic tests may verify parsing/accounting
  behavior but cannot convert it to venue evidence or edge evidence.

### T08 - Position and balance reconciliation

- Compare remote open orders, positions, and available account state with local
  durable state before entry, after each leg, after close, and after restart.
- Test remote-only order, local-only order, quantity mismatch, and position
  mismatch through deterministic fixtures or authorized test artifacts.
- Pass: every mismatch is classified; unknown state blocks new exposure;
  repair is explicit, idempotent, and auditable. Balance data is redacted.

### T09 - Restart and reconnect

- Interrupt REST response handling, WebSocket delivery, and the process at each
  critical transition: submitted/no acknowledgement, partial fill, first leg
  filled, hedge submitted, cancel pending, and closing.
- Restart from durable state and reconcile before resuming.
- Pass: no duplicate economic action, no lost fill, timers preserve original
  exposure start, and new trades remain blocked until reconciliation completes.

### T10 - Kill switch

- Engage the switch before entry, between legs, during partial fill, during
  reconnect, and before close.
- Pass: it blocks all new/increased exposure immediately at the authoritative
  boundary; it does not erase state; already exposed trades follow the frozen
  reduce-risk policy; clearing requires explicit authorized action and fresh
  reconciliation.

### T11 - Idempotency and event disorder

- Repeat identical submit/cancel/replace requests and replay duplicate,
  delayed, missing, and out-of-order acknowledgements/fills.
- Pass: stable keys map retries to one intent, cumulative fills do not exceed
  authoritative venue quantity, and state converges after reconciliation.

### T12 - Observability and redaction

- Trace one complete trade and every failure path by run/trade/leg/correlation
  IDs across structured logs and durable events.
- Scan retained artifacts for configured secrets and forbidden secret-derived
  or account data without printing the matched values.
- Pass: state transitions and timing are reconstructable; alerts identify the
  scenario and exposure severity; no prohibited value is retained.

## 6. Fault Injection Policy

Use deterministic offline/mocked faults for conditions the venue cannot safely
or reliably produce: redirects, exact timing limits, malformed events, event
reordering, transport loss, process interruption, and mainnet-host injection.
Use an authorized testnet/demo only for venue contract evidence such as accepted
request shape, acknowledgement/fill semantics, supported cancel behavior,
position reporting, and available funding events.

Every result must label its evidence source as `MOCK`, `TESTNET`, or `DEMO`.
Mock evidence cannot prove venue behavior. Testnet/demo evidence cannot prove
production execution quality or edge.

## 7. Pass, Fail, And Readiness Gates

### Scenario pass

A scenario passes only when all assertions pass on the frozen commit, required
artifacts are complete and redacted, final reconciliation is clean, and no
unexplained state transition remains. `NOT TESTABLE` is not a pass.

### Suite pass

The implementation acceptance suite passes only when:

- T01 through T06 and T08 through T12 pass;
- T07 passes or is explicitly recorded as `NOT TESTABLE` with synthetic
  behavior tests and no funding-readiness claim;
- every run stays within locked unhedged interval and notional limits;
- all terminal states reconcile with zero unexplained residual exposure;
- no secret/redaction violation occurs;
- the no-mainnet guard has independent negative-test evidence;
- an independent reviewer confirms evidence labels and unresolved limitations.

Any credential leak, production endpoint contact, unexpected account identity,
unbounded exposure, blind retry, unexplained residual, duplicate economic
action, lost fill, timer reset, reconciliation bypass, or kill-switch bypass is
an immediate suite failure and incident. Stop all exchange testing, revoke the
test credential where relevant, preserve redacted evidence, and require a new
owner decision before rerun.

### What a pass may claim

- Docs readiness: acceptance specification exists.
- Code readiness: only after the frozen implementation passes applicable mock
  checks and code review.
- Testnet/demo implementation readiness: only for the exact tested venue,
  environment, instruments, commit, and limitations.
- Runtime readiness: not implied; requires separately authorized runtime
  evidence.
- Paper readiness, production readiness, live readiness, and trading edge: not
  implied and remain NO-GO unless separately established.

## 8. Required Run Artifact

Produce one immutable, redacted report per authorized suite run containing:

- manifest fields from section 2;
- scenario table with PASS/FAIL/NOT TESTABLE and evidence source;
- exact commands or harness entry points used, without credentials;
- UTC timing and maximum observed unhedged duration/notional;
- order/fill/reconciliation state-transition summary;
- injected fault list and expected versus observed response;
- redaction scan result;
- unresolved limitations and incidents;
- implementation-evidence claim;
- explicit statement that no edge evidence was produced;
- implementer and independent reviewer sign-off;
- owner decision: reject, fix-and-rerun, or accept the bounded implementation
  evidence.

## 9. Current Decision

This plan is docs-only preparation. Bybit testnet remains BLOCKED and Bitget
Demo remains PARKED / planning only. The next permitted action is review of this
specification and later owner selection of one named environment. No private
endpoint access, credential preparation, runtime wiring, or execution follows
from this document by implication.
