from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    project_root = Path(__file__).resolve().parent.parent.parent
    default_trace = project_root / "data" / "trace_20240514-5min.json"

    parser = argparse.ArgumentParser(description="Rolling-horizon LLM allocation simulator")
    parser.add_argument(
        "--methods", nargs="+", default=["gh", "agh", "milp"],
        choices=["gh", "agh", "milp"],
    )
    parser.add_argument(
        "--trace", type=str,
        default=str(default_trace) if default_trace.exists() else None,
        help="path to a JSON trace file (list of per-window load multipliers)",
    )
    parser.add_argument("--azure-csv", type=str, default=None, help="path to raw Azure CSV")
    parser.add_argument("--day", type=str, default="2024-05-14", help="day to extract from Azure CSV")
    parser.add_argument("--busiest", type=int, default=0, help="keep only the N busiest windows")
    parser.add_argument(
        "--dimensions", type=int, nargs=3, default=None,
        metavar=("I", "M", "K"),
        help="base instance size (e.g. 6 6 10); omit for 2x2x2",
    )
    parser.add_argument("--budget-fraction", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument("--time-limit", type=float, default=None, help="MILP time limit per window (seconds)")
    parser.add_argument("--out-dir", type=str, default="out")
    return parser


def build_output_paths(args, dimensions: tuple[int, ...] | None, actual_windows: int) -> tuple[str, Path, Path]:
    size = f"{dimensions[0]}x{dimensions[1]}x{dimensions[2]}" if dimensions else "2x2x2"

    if args.busiest > 0:
        window_part = f"busiest{args.busiest}"
    else:
        window_part = f"full-{actual_windows}w"

    methods_part = "-".join(args.methods)
    file_tag = f"{window_part}_{methods_part}"

    out_dir = Path(args.out_dir) / size
    window_csv = out_dir / f"windows_{file_tag}.csv"
    summary_csv = out_dir / f"summary_{file_tag}.csv"

    run_label = f"{size}/{file_tag}"
    return run_label, window_csv, summary_csv
