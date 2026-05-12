"""Run bounded Binance recent 4H acquisition for DR1 freshness validation."""

from __future__ import annotations

from research.signal_observation.binance_recent_4h_downloader import (
    create_locked_window,
    format_validation_report,
    run_binance_recent_4h_acquisition,
)


def main() -> int:
    """Lock the target window, print it, then acquire and validate data."""

    locked_window = create_locked_window()
    print(
        "Locked Binance recent 4H acquisition window:\n"
        f"task_started_utc={locked_window.as_report()['acquisition_task_started_utc']}\n"
        f"start_utc={locked_window.as_report()['locked_window_start_utc']}\n"
        f"end_utc={locked_window.as_report()['locked_window_end_utc']}\n"
    )
    report = run_binance_recent_4h_acquisition(locked_window=locked_window)
    print(format_validation_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
