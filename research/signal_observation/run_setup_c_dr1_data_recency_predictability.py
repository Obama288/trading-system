"""Run Setup C DR1 data recency / predictability reconnaissance."""

from __future__ import annotations

from research.signal_observation.setup_c_dr1_data_recency_predictability import (
    format_dr1_report,
    run_dr1_data_recency_predictability,
)


def main() -> int:
    """CLI entrypoint for local DR1 diagnostic artifact generation."""

    report = run_dr1_data_recency_predictability()
    print(format_dr1_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
