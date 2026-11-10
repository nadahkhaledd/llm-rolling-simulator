from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Sequence


def load_trace_from_json(path: str | Path) -> list[float]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(
        isinstance(x, (int, float)) for x in data
    ):
        raise ValueError("trace JSON must be a list of numbers")
    return [float(x) for x in data]


def load_trace_from_azure_csv(
    path: str | Path,
    day: str = "2024-05-14",
    window_minutes: int = 5,
) -> list[float]:
    from collections import Counter
    from datetime import datetime

    windows_per_day = (24 * 60) // window_minutes
    window_counts: Counter[int] = Counter()
    total = 0

    with Path(path).open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ts = row["TIMESTAMP"].strip()
            if not ts.startswith(day):
                continue
            total += 1
            dt = datetime.fromisoformat(ts.split("+")[0])
            window_idx = (dt.hour * 60 + dt.minute) // window_minutes
            window_counts[window_idx] += 1

    if total == 0:
        raise ValueError(f"no rows found for day {day!r} in {path}")

    counts = [window_counts.get(i, 0) for i in range(windows_per_day)]
    avg = sum(counts) / len(counts)
    multipliers = [round(c / avg, 4) if avg > 0 else 0.0 for c in counts]
    return multipliers


def busiest_windows(trace: Sequence[float], count: int = 10) -> list[float]:
    if count >= len(trace):
        return list(trace)
    threshold = sorted(trace, reverse=True)[count - 1]
    picked = [m for m in trace if m >= threshold]
    return picked[:count]
