"""CLI runner: assess OHLCV CSV quality and write a .quality.json artifact.

Usage:
    python -m research.signal_observation.run_data_quality <csv_path>

Writes <csv_path>.quality.json next to the CSV. Exits 1 on FAIL.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print(
            "Usage: python -m research.signal_observation.run_data_quality <csv_path>",
            file=sys.stderr,
        )
        return 2

    csv_path = Path(args[0])

    # Import here to keep startup cost visible and to allow test overrides.
    from research.signal_observation.csv_loader import load_ohlcv_csv
    from research.simcore.quality import assess_candles, passes, to_json_dict

    candles = load_ohlcv_csv(csv_path)
    report = assess_candles(candles)
    ok, reasons = passes(report)

    artifact = to_json_dict(report)
    artifact["dataset"] = str(csv_path)
    artifact["generated_at"] = datetime.now(UTC).isoformat()

    out_path = csv_path.with_name(csv_path.name + ".quality.json")
    out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    if ok:
        print(f"PASS — {csv_path}")
        return 0

    print(f"FAIL — {csv_path}")
    for reason in reasons:
        print(f"  • {reason}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
