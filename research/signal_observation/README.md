# Signal Observation Skeleton

This package holds research-layer data models for Stage 54-SQ-A automated
signal observation collection.

Current scope:
- pure typed data objects only;
- local CSV candle loading only;
- no exchange calls;
- no data download from remote systems;
- no execution;
- no private API;
- no API keys or secrets;
- no runtime wiring.

## CSV input format

Stage 54-SQ-A2 accepts local public OHLCV CSV files with this header:

```csv
timestamp,open,high,low,close,volume
```

Rules:
- timestamps must be ISO-8601 values;
- OHLCV numeric values are parsed as `Decimal`;
- duplicate timestamps are rejected;
- invalid candles are rejected;
- returned candles are sorted by timestamp ascending.

Real historical CSV files should be treated as local data inputs and should
not be committed unless the Human Owner explicitly approves them.

A2 only loads candles. It does not detect setups, calculate outcomes, call
exchanges, call private APIs, place orders, or wire into runtime services.

## A3 indicator utilities

Stage 54-SQ-A3 adds deterministic research utilities:
- true range;
- ATR with Wilder smoothing;
- EMA with a simple-average seed;
- strict pivot high and pivot low markers;
- timezone-aware UTC session labels.

These utilities are pure local calculations over already-loaded candle data.
They do not detect setups, calculate outcomes, call exchanges, call private
APIs, place orders, or wire into runtime services.

## A4 Setup A detector

Stage 54-SQ-A4 adds a deterministic research detector for Setup A:
Breakout -> Retest -> Continuation.

Current scope:
- long Setup A observations only;
- already-loaded local 4H and 1H candles only;
- no Setup B detector;
- no statistics report;
- no exchange calls;
- no API calls;
- no private endpoints;
- no execution.

## A5 outcome tracker

Stage 54-SQ-A5 adds deterministic simulated R outcome tracking for an already
detected `SignalObservation` and local trigger candles.

Current scope:
- resolves stop, target, or window-close outcomes;
- calculates MFE_R, MAE_R, and final_R;
- supports long and short observation directions;
- uses local candles only;
- no statistics report;
- no account balance, position size, dollars, leverage, fees, or slippage;
- no exchange calls;
- no API calls;
- no private endpoints;
- no execution;
- no runtime wiring.

## A6 local fixture summary runner

Stage 54-SQ-A6 connects the existing local research pieces:

```text
CSV candles -> Setup A detector -> outcome tracker -> summary metrics
```

Current scope:
- local fixture CSVs only;
- summary metrics over resolved `OutcomeResult` objects;
- no real historical data download;
- no exchange calls;
- no API calls;
- no private endpoints;
- no runtime wiring;
- no trading or live readiness.

Run the local fixture summary with:

```powershell
python -m research.signal_observation.run_fixture_summary
```

## A7 local historical CSV summary runner

Stage 54-SQ-A7 runs the Setup A detector and outcome tracker against
user-provided local historical CSV files.

Example:

```powershell
python -m research.signal_observation.run_csv_summary --context-4h path\to\4h.csv --trigger-1h path\to\1h.csv --symbol BTCUSDT --source-exchange local_csv --btc-score 0
```

Current scope:
- local CSV files only;
- Setup A long detector only;
- simulated R outcome summary only;
- no output files are written;
- no real historical data download;
- no exchange calls;
- no API calls;
- no private endpoints;
- no execution;
- no runtime wiring;
- no trading, live, or probe readiness.

Real historical CSV files should stay local and should not be committed unless
the Human Owner explicitly approves them.

The package exists to support later offline detector and outcome-tracker
implementation without touching the money path.
