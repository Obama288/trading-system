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

The package exists to support later offline detector and outcome-tracker
implementation without touching the money path.
