from __future__ import annotations

from pathlib import Path

from cli import build_parser, build_output_paths, build_base_instance
from simulator import (
    busiest_windows,
    load_trace_from_azure_csv,
    load_trace_from_json,
    run_rolling_horizon,
    write_summary_csv,
    write_window_csv,
)


def main() -> None:
    args = build_parser().parse_args()

    if args.azure_csv:
        print(f"Reading Azure CSV: {args.azure_csv} (day={args.day}) ...")
        trace = load_trace_from_azure_csv(args.azure_csv, day=args.day)
        trace_label = f"azure-{args.day}"
    elif args.trace:
        trace = load_trace_from_json(args.trace)
        trace_label = f"file:{Path(args.trace).name}"

    if args.busiest > 0:
        trace = busiest_windows(trace, args.busiest)
        trace_label += f"|busiest:{args.busiest}"

    dimensions = tuple(args.dimensions) if args.dimensions else None
    base = build_base_instance(dimensions)

    print(f"Base instance : {base.id} ({len(base.queries)}Q x "
          f"{len(base.models)}M x {len(base.gpu_tiers)}T)")
    print(f"Trace         : {trace_label}  ->  {len(trace)} windows")
    print(f"Methods       : {', '.join(args.methods)}")
    print("Running ...")

    per_window, summaries = run_rolling_horizon(
        base, trace, args.methods,
        budget_fraction=args.budget_fraction, seed=args.seed,
        milp_time_limit=args.time_limit,
    )

    run_label, window_csv, summary_csv = build_output_paths(args, dimensions, len(trace))

    write_window_csv(per_window, window_csv)
    write_summary_csv(summaries, summary_csv)

    print(f"\n=== Horizon summary  [{run_label}] ===")
    header = f"{'method':6} {'windows':8} {'feas':5} {'sum_cost':>14} {'mean_cost':>12} {'mean_rt_s':>10} {'viol%':>7}"
    print(header)
    print("-" * len(header))
    for s in summaries:
        print(f"{s.method:6} {s.windows:8d} {s.feasible_windows:5d} "
              f"{s.total_cost_sum:14.4f} {s.mean_cost_per_window:12.4f} "
              f"{s.mean_runtime_seconds:10.5f} "
              f"{100.0 * s.violation_rate:7.2f}")

    print(f"\nCSV written to: {window_csv}")
    print(f"CSV written to: {summary_csv}")


if __name__ == "__main__":
    main()
