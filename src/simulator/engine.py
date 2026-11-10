from __future__ import annotations

import time
from dataclasses import replace
from typing import Sequence

from llm_resource_allocation.algorithms.gh_phase1 import GHPhase1Config
from llm_resource_allocation.domain.types import ProblemInstance

from simulator.adapters import RESIDUAL_TOLERANCE, SOLVERS
from simulator.models import HorizonSummary, WindowResult


def scale_instance_load(
    base: ProblemInstance, load_multiplier: float
) -> ProblemInstance:
    scaled_queries = tuple(
        replace(q, arrival_rate_per_hour=q.arrival_rate_per_hour * load_multiplier)
        for q in base.queries
    )
    return replace(base, queries=scaled_queries)


def run_window(
    base: ProblemInstance,
    window_index: int,
    load_multiplier: float,
    method: str,
    phase1: GHPhase1Config,
    seed: int,
    *,
    milp_time_limit: float | None = None,
) -> WindowResult:
    if method not in SOLVERS:
        raise ValueError(
            f"unknown method {method!r}; choose from {sorted(SOLVERS)}"
        )
    instance = scale_instance_load(base, load_multiplier)
    solver = SOLVERS[method]

    start = time.perf_counter()
    if method == "milp" and milp_time_limit is not None:
        feasible, breakdown, residual = solver(instance, phase1, seed,
                                               time_limit=milp_time_limit)
    else:
        feasible, breakdown, residual = solver(instance, phase1, seed)
    elapsed = time.perf_counter() - start

    if breakdown is None:
        return WindowResult(
            window_index=window_index,
            load_multiplier=load_multiplier,
            method=method,
            feasible=False,
            total_cost=None,
            gpu_rental=None,
            model_storage=None,
            data_storage=None,
            delay_penalty=None,
            unmet_penalty=None,
            total_residual_demand=residual,
            runtime_seconds=elapsed,
        )

    return WindowResult(
        window_index=window_index,
        load_multiplier=load_multiplier,
        method=method,
        feasible=feasible,
        total_cost=breakdown.total,
        gpu_rental=breakdown.gpu_rental_cost,
        model_storage=breakdown.model_storage_cost,
        data_storage=breakdown.data_storage_cost,
        delay_penalty=breakdown.delay_penalty,
        unmet_penalty=breakdown.unmet_demand_penalty,
        total_residual_demand=residual,
        runtime_seconds=elapsed,
    )


def run_rolling_horizon(
    base: ProblemInstance,
    trace: Sequence[float],
    methods: Sequence[str],
    *,
    budget_fraction: float = 0.8,
    seed: int = 37,
    milp_time_limit: float | None = None,
) -> tuple[list[WindowResult], list[HorizonSummary]]:
    phase1 = GHPhase1Config(budget_fraction=budget_fraction)
    per_window: list[WindowResult] = []
    summaries: list[HorizonSummary] = []

    for method in methods:
        method_results: list[WindowResult] = []
        for index, multiplier in enumerate(trace):
            result = run_window(
                base, index, multiplier, method, phase1, seed,
                milp_time_limit=milp_time_limit,
            )
            method_results.append(result)
            per_window.append(result)

        summaries.append(_summarize(method, method_results))

    return per_window, summaries


def _summarize(method: str, results: Sequence[WindowResult]) -> HorizonSummary:
    windows = len(results)
    feasible = [r for r in results if r.feasible and r.total_cost is not None]
    costs = [r.total_cost for r in feasible]
    runtimes = [r.runtime_seconds for r in results]
    violations = sum(
        1 for r in results if r.total_residual_demand > RESIDUAL_TOLERANCE
    )
    total_cost_sum = float(sum(costs)) if costs else 0.0
    mean_cost = total_cost_sum / len(costs) if costs else 0.0
    mean_runtime = sum(runtimes) / windows if windows else 0.0
    return HorizonSummary(
        method=method,
        windows=windows,
        feasible_windows=len(feasible),
        total_cost_sum=total_cost_sum,
        mean_cost_per_window=mean_cost,
        mean_runtime_seconds=mean_runtime,
        violation_rate=violations / windows if windows else 0.0,
    )
