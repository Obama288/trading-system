"""Run Setup C C8 direction-call agreement diagnostic on committed CSVs."""

from __future__ import annotations

from research.signal_observation.setup_c_c8_direction_agreement import (
    format_c8_report,
    run_c8_direction_agreement,
)


def main() -> int:
    """CLI entrypoint for local C8 diagnostic artifact generation."""

    report = run_c8_direction_agreement()
    print(format_c8_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
