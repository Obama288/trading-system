"""Run bounded DR1 Binance recent rerun."""

from __future__ import annotations

from research.signal_observation.setup_c_dr1_binance_recent_rerun import (
    format_rerun_report,
    run_dr1_binance_recent_rerun,
)


def main() -> int:
    """CLI entrypoint for deterministic rerun artifact generation."""

    report = run_dr1_binance_recent_rerun()
    print(format_rerun_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
