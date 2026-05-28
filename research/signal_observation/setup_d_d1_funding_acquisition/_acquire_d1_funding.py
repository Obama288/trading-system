"""
D1 Funding Data Acquisition — Binance USDT-M public REST only.
Authorized scope: BTCUSDT, ETHUSDT, SOLUSDT; 2022-01-01T00:00:00Z to 2023-12-17T12:00:00Z.
No authentication. No analysis. No data outside the locked window.
"""

import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ── Locked constants (must not be changed without a new design lock) ──────────
BASE_URL = "https://fapi.binance.com"
ENDPOINT = "/fapi/v1/fundingRate"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
WINDOW_START_MS = 1640995200000  # 2022-01-01T00:00:00Z
WINDOW_END_MS   = 1702814400000  # 2023-12-17T12:00:00Z
EXPECTED_INTERVAL_H = 8
EXPECTED_INTERVAL_MS = EXPECTED_INTERVAL_H * 3600 * 1000
PAGE_LIMIT = 1000  # max per Binance docs
SLEEP_BETWEEN_PAGES = 0.25  # seconds, polite pacing

OUTPUT_DIR = "research/signal_observation/setup_d_d1_funding_acquisition"


def fetch_funding_page(symbol: str, start_ms: int, end_ms: int) -> list:
    params = {
        "symbol": symbol,
        "startTime": start_ms,
        "endTime": end_ms,
        "limit": PAGE_LIMIT,
    }
    url = BASE_URL + ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib/research-only"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_all(symbol: str) -> list:
    all_rows = []
    cursor = WINDOW_START_MS
    while cursor <= WINDOW_END_MS:
        page = fetch_funding_page(symbol, cursor, WINDOW_END_MS)
        if not page:
            break
        # filter to locked window (defensive — should already be bounded)
        page = [r for r in page if WINDOW_START_MS <= r["fundingTime"] <= WINDOW_END_MS]
        if not page:
            break
        all_rows.extend(page)
        last_ts = page[-1]["fundingTime"]
        if len(page) < PAGE_LIMIT:
            break
        cursor = last_ts + 1
        time.sleep(SLEEP_BETWEEN_PAGES)
    return all_rows


def validate(rows: list, symbol: str) -> dict:
    if not rows:
        return {"symbol": symbol, "row_count": 0, "error": "NO_DATA"}

    times = [r["fundingTime"] for r in rows]
    times_sorted = sorted(set(times))

    row_count = len(rows)
    dup_count = row_count - len(set(times))
    first_ts = min(times)
    last_ts = max(times)
    first_dt = datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc).isoformat()
    last_dt  = datetime.fromtimestamp(last_ts  / 1000, tz=timezone.utc).isoformat()

    # outside window check
    out_of_window = [t for t in times if t < WINDOW_START_MS or t > WINDOW_END_MS]

    # gap analysis (sorted unique timestamps)
    gaps = []
    missing_intervals = 0
    max_gap_ms = 0
    for i in range(1, len(times_sorted)):
        gap = times_sorted[i] - times_sorted[i - 1]
        if gap > max_gap_ms:
            max_gap_ms = gap
        if gap > EXPECTED_INTERVAL_MS:
            gaps.append({"from": times_sorted[i-1], "to": times_sorted[i], "gap_ms": gap})
            missing_intervals += round(gap / EXPECTED_INTERVAL_MS) - 1

    max_gap_h = max_gap_ms / 3600000

    # monotonicity
    monotonic = times == sorted(times)

    # coverage vs expected
    expected_count = round((WINDOW_END_MS - WINDOW_START_MS) / EXPECTED_INTERVAL_MS) + 1

    return {
        "symbol": symbol,
        "row_count": row_count,
        "duplicate_count": dup_count,
        "first_fundingTime_ms": first_ts,
        "last_fundingTime_ms": last_ts,
        "first_fundingTime_utc": first_dt,
        "last_fundingTime_utc": last_dt,
        "monotonic": monotonic,
        "out_of_window_count": len(out_of_window),
        "max_gap_ms": max_gap_ms,
        "max_gap_h": round(max_gap_h, 4),
        "missing_8h_intervals": missing_intervals,
        "large_gaps": gaps[:10],  # first 10 for report
        "expected_intervals": expected_count,
        "coverage_pass": (
            dup_count == 0
            and len(out_of_window) == 0
            and missing_intervals == 0
            and monotonic
        ),
    }


def main():
    import os, sys
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    out_dir = os.path.join(repo_root, OUTPUT_DIR)
    os.makedirs(out_dir, exist_ok=True)

    print(f"Output directory: {out_dir}")
    print(f"Window: {datetime.fromtimestamp(WINDOW_START_MS/1000, tz=timezone.utc).isoformat()} "
          f"to {datetime.fromtimestamp(WINDOW_END_MS/1000, tz=timezone.utc).isoformat()}")
    print(f"Symbols: {SYMBOLS}\n")

    all_data = {}
    validation_results = []
    acquisition_label = "FUNDING_DATA_ACQUIRED"

    for symbol in SYMBOLS:
        print(f"Fetching {symbol}...")
        try:
            rows = fetch_all(symbol)
            print(f"  {symbol}: {len(rows)} rows fetched")
            all_data[symbol] = rows
            vr = validate(rows, symbol)
            validation_results.append(vr)
            if not vr.get("coverage_pass"):
                acquisition_label = "FUNDING_DATA_FAIL"
            print(f"  {symbol}: first={vr.get('first_fundingTime_utc')} last={vr.get('last_fundingTime_utc')}")
            print(f"  {symbol}: dups={vr.get('duplicate_count')} max_gap_h={vr.get('max_gap_h')} missing={vr.get('missing_8h_intervals')}")
        except Exception as exc:
            print(f"  {symbol}: ERROR — {exc}", file=sys.stderr)
            validation_results.append({"symbol": symbol, "error": str(exc)})
            acquisition_label = "FUNDING_DATA_BLOCKED"

    # ── Save raw data ────────────────────────────────────────────────────────
    raw_path = os.path.join(out_dir, "d1_funding_raw.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, separators=(",", ":"))
    print(f"\nRaw data saved: {raw_path}")

    # ── Save validation report ───────────────────────────────────────────────
    report = {
        "acquisition_label": acquisition_label,
        "endpoint": BASE_URL + ENDPOINT,
        "symbols": SYMBOLS,
        "window_start_utc": "2022-01-01T00:00:00Z",
        "window_end_utc": "2023-12-17T12:00:00Z",
        "window_start_ms": WINDOW_START_MS,
        "window_end_ms": WINDOW_END_MS,
        "expected_interval_h": EXPECTED_INTERVAL_H,
        "private_endpoint_used": False,
        "credentials_used": False,
        "reserved_window_touched": False,
        "per_symbol": validation_results,
    }
    report_path = os.path.join(out_dir, "d1_funding_validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Validation report saved: {report_path}")

    # ── Plain-text summary ───────────────────────────────────────────────────
    lines = [
        "D1 Funding Data Acquisition Report",
        "===================================",
        f"Result: {acquisition_label}",
        f"Endpoint: {BASE_URL + ENDPOINT}",
        f"Window: 2022-01-01T00:00:00Z to 2023-12-17T12:00:00Z",
        f"Symbols: {', '.join(SYMBOLS)}",
        f"Private endpoint: No | Credentials: No | Reserved window touched: No",
        "",
    ]
    for vr in validation_results:
        sym = vr["symbol"]
        if "error" in vr:
            lines.append(f"{sym}: ERROR — {vr['error']}")
        else:
            cp = "PASS" if vr.get("coverage_pass") else "FAIL"
            lines.append(f"{sym}: {cp}")
            lines.append(f"  rows={vr['row_count']} dups={vr['duplicate_count']} "
                         f"out_of_window={vr['out_of_window_count']}")
            lines.append(f"  first={vr['first_fundingTime_utc']}")
            lines.append(f"  last={vr['last_fundingTime_utc']}")
            lines.append(f"  max_gap_h={vr['max_gap_h']} missing_8h={vr['missing_8h_intervals']}")
            lines.append(f"  monotonic={vr['monotonic']}")
        lines.append("")

    summary_path = os.path.join(out_dir, "d1_funding_acquisition_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Summary saved: {summary_path}")
    print(f"\nAcquisition label: {acquisition_label}")
    return acquisition_label


if __name__ == "__main__":
    main()
