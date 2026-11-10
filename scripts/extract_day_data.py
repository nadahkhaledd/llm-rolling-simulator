from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract one day from the Azure trace CSV"
    )
    parser.add_argument(
        "--input", required=True,
        help="path to the full Azure CSV (e.g. AzureLLMInferenceTrace_code_1week.csv)",
    )
    parser.add_argument(
        "--day", default="2024-05-14",
        help="which day to extract (YYYY-MM-DD format, default: 2024-05-14)",
    )
    parser.add_argument(
        "--output", default=None,
        help="output CSV path (default: azure_trace_{day}.csv)",
    )
    args = parser.parse_args()

    output_path = args.output or f"azure_trace_{args.day}.csv"

    print(f"Reading: {args.input}")
    print(f"Extracting day: {args.day}")

    rows_written = 0
    total_context_tokens = 0
    total_generated_tokens = 0

    with (
        Path(args.input).open("r", encoding="utf-8") as infile,
        Path(output_path).open("w", newline="", encoding="utf-8") as outfile,
    ):
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(
            outfile,
            fieldnames=["TIMESTAMP", "ContextTokens", "GeneratedTokens"],
        )
        writer.writeheader()

        for row in reader:
            ts = row["TIMESTAMP"].strip()
            if not ts.startswith(args.day):
                continue
            writer.writerow({
                "TIMESTAMP": ts,
                "ContextTokens": row["ContextTokens"].strip(),
                "GeneratedTokens": row["GeneratedTokens"].strip(),
            })
            rows_written += 1
            total_context_tokens += int(row["ContextTokens"].strip())
            total_generated_tokens += int(row["GeneratedTokens"].strip())

    if rows_written == 0:
        print(f"WARNING: no rows found for {args.day}!")
        print("Available days are 2024-05-10 through 2024-05-16.")
        return

    print(f"\nDone! Wrote {rows_written:,} rows to {output_path}")
    print(f"File size: {Path(output_path).stat().st_size / 1_000_000:.1f} MB")
    print(f"\nStats for {args.day}:")
    print(f"  Total requests:         {rows_written:,}")
    print(f"  Requests per hour:      {rows_written / 24:,.0f}")
    print(f"  Avg context tokens:     {total_context_tokens / rows_written:,.1f}")
    print(f"  Avg generated tokens:   {total_generated_tokens / rows_written:,.1f}")
    print(f"  Total context tokens:   {total_context_tokens:,}")
    print(f"  Total generated tokens: {total_generated_tokens:,}")


if __name__ == "__main__":
    main()