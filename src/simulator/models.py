from __future__ import annotations

from dataclasses import dataclass


def _round_or_blank(value: float | None) -> object:
    return "" if value is None else round(value, 6)


@dataclass(frozen=True, slots=True)
class WindowResult:
    window_index: int
    load_multiplier: float
    method: str
    feasible: bool
    total_cost: float | None
    gpu_rental: float | None
    model_storage: float | None
    data_storage: float | None
    delay_penalty: float | None
    unmet_penalty: float | None
    total_residual_demand: float
    runtime_seconds: float

    def as_row(self) -> dict[str, object]:
        return {
            "window_index": self.window_index,
            "load_multiplier": round(self.load_multiplier, 6),
            "method": self.method,
            "feasible": int(self.feasible),
            "total_cost": _round_or_blank(self.total_cost),
            "gpu_rental": _round_or_blank(self.gpu_rental),
            "model_storage": _round_or_blank(self.model_storage),
            "data_storage": _round_or_blank(self.data_storage),
            "delay_penalty": _round_or_blank(self.delay_penalty),
            "unmet_penalty": _round_or_blank(self.unmet_penalty),
            "total_residual_demand": round(self.total_residual_demand, 6),
            "runtime_seconds": round(self.runtime_seconds, 6),
        }


@dataclass(frozen=True, slots=True)
class HorizonSummary:
    method: str
    windows: int
    feasible_windows: int
    total_cost_sum: float
    mean_cost_per_window: float
    mean_runtime_seconds: float
    violation_rate: float

    def as_row(self) -> dict[str, object]:
        return {
            "method": self.method,
            "windows": self.windows,
            "feasible_windows": self.feasible_windows,
            "total_cost_sum": round(self.total_cost_sum, 4),
            "mean_cost_per_window": round(self.mean_cost_per_window, 4),
            "mean_runtime_seconds": round(self.mean_runtime_seconds, 6),
            "violation_rate_percent": round(100.0 * self.violation_rate, 3),
        }
