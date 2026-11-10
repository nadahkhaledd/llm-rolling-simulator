"""
Convert a day CSV into a JSON trace for the simulator.

Takes a CSV with columns (TIMESTAMP, ContextTokens, GeneratedTokens)
— either the full 7-day file or an already-extracted single-day file —
and produces a JSON list of per-window load multipliers.

Usage:
    # From a single-day CSV (output of extract_day.py):
    python convert_csv_to_json_trace.py --input azure_trace_2024-05-14.csv

    # From the full 7-day CSV, picking a day:
    python convert_csv_to_json_trace.py --input AzureLLMInferenceTrace_code_1week.csv --day 2024-05-14

    # Custom window size (default is 5 minutes):
    python convert_csv_to_json_trace.py --input azure_trace_2024-05-14.csv --window-minutes 15

The output JSON can be fed to the simulator:
    python run_simulation.py --trace trace_2024-05-14_5min.json --methods gh agh pdm
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a day CSV to a JSON trace of load multipliers"
    )
    parser.add_argument(
        "--input", required=True,
        help="path to the CSV (single-day or full 7-day)",
    )
    parser.add_argument(
        "--day", default=None,
        help="which day to extract (YYYY-MM-DD). If omitted, uses ALL rows "
             "in the CSV (so pass a single-day CSV or set this flag).",
    )
    parser.add_argument(
        "--window-minutes", type=int, default=5,
        help="size of each window in minutes (default: 5, giving 288 windows)",
    )
    parser.add_argument(
        "--output", default=None,
        help="output JSON path (default: auto-generated from day + window size)",
    )
    args = parser.parse_args()

    window_minutes = args.window_minutes
    windows_per_day = (24 * 60) // window_minutes

    print(f"Reading: {args.input}")
    if args.day:
        print(f"Filtering to day: {args.day}")
    print(f"Window size: {window_minutes} minutes → {windows_per_day} windows per day")

    # --- Step 1: Count requests per window ---
    window_counts: Counter[int] = Counter()
    total_rows = 0

    with Path(args.input).open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = row["TIMESTAMP"].strip()

            # If a day filter is set, skip rows from other days
            if args.day and not ts.startswith(args.day):
                continue

            total_rows += 1

            # Parse the timestamp to find which window it belongs to
            # The math: (hour * 60 + minute) // window_minutes
            dt = datetime.fromisoformat(ts.split("+")[0])
            minutes_since_midnight = dt.hour * 60 + dt.minute
            window_index = minutes_since_midnight // window_minutes

            window_counts[window_index] += 1

    if total_rows == 0:
        day_msg = f" for day {args.day}" if args.day else ""
        print(f"ERROR: no rows found{day_msg} in {args.input}")
        return

    # --- Step 2: Build the count array (fill missing windows with 0) ---
    counts = [window_counts.get(i, 0) for i in range(windows_per_day)]

    # --- Step 3: Convert counts to multipliers (relative to daily average) ---
    average = sum(counts) / len(counts)
    multipliers = [round(c / average, 4) if average > 0 else 0.0 for c in counts]

    # --- Step 4: Save ---
    day_label = args.day or "alldays"
    output_path = args.output or f"trace_{day_label}_{window_minutes}min.json"

    with Path(output_path).open("w", encoding="utf-8") as f:
        json.dump(multipliers, f)

    # --- Print summary ---
    print(f"\n{'='*50}")
    print(f"Total requests:       {total_rows:,}")
    print(f"Windows:              {windows_per_day}")
    print(f"Avg requests/window:  {average:,.1f}")
    print(f"Min window:           {min(counts):,} requests (multiplier {min(multipliers):.4f})")
    print(f"Max window:           {max(counts):,} requests (multiplier {max(multipliers):.4f})")
    print(f"Peak-to-trough ratio: {max(counts) / max(min(c for c in counts if c > 0), 1):.1f}×")
    print(f"{'='*50}")
    print(f"Saved: {output_path} ({windows_per_day} multipliers)")

    # Show a mini preview
    print(f"\nFirst 5 windows (midnight):")
    for i in range(min(5, len(multipliers))):
        bar = "█" * int(multipliers[i] * 20)
        t_start = f"{(i * window_minutes) // 60:02d}:{(i * window_minutes) % 60:02d}"
        t_end = f"{((i+1) * window_minutes) // 60:02d}:{((i+1) * window_minutes) % 60:02d}"
        print(f"  [{t_start}-{t_end}] {counts[i]:>6,} requests  ×{multipliers[i]:.4f}  {bar}")

    # Find and show the peak window
    peak_idx = multipliers.index(max(multipliers))
    t_start = f"{(peak_idx * window_minutes) // 60:02d}:{(peak_idx * window_minutes) % 60:02d}"
    t_end = f"{((peak_idx+1) * window_minutes) // 60:02d}:{((peak_idx+1) * window_minutes) % 60:02d}"
    bar = "█" * int(multipliers[peak_idx] * 20)
    print(f"\nPeak window:")
    print(f"  [{t_start}-{t_end}] {counts[peak_idx]:>6,} requests  ×{multipliers[peak_idx]:.4f}  {bar}")


if __name__ == "__main__":
    main()
