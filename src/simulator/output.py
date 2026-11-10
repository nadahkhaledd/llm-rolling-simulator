from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping, Sequence

from simulator.models import HorizonSummary, WindowResult


def write_window_csv(results: Sequence[WindowResult], path: str | Path) -> None:
    rows = [r.as_row() for r in results]
    _write_csv(rows, path)


def write_summary_csv(summaries: Sequence[HorizonSummary], path: str | Path) -> None:
    rows = [s.as_row() for s in summaries]
    _write_csv(rows, path)


def _write_csv(rows: Sequence[Mapping[str, object]], path: str | Path) -> None:
    if not rows:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
