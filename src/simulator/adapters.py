from __future__ import annotations

from typing import Callable

from llm_resource_allocation.algorithms.agh import run_agh
from llm_resource_allocation.algorithms.gh import run_gh
from llm_resource_allocation.algorithms.gh_phase1 import GHPhase1Config
from llm_resource_allocation.domain.types import ProblemInstance
from llm_resource_allocation.optimization.pdm_run import execute_and_record_pdm_run
from llm_resource_allocation.optimization.problem_data import PdmProblemData
from llm_resource_allocation.optimization.solver import SolverBackend, SolverConfig

RESIDUAL_TOLERANCE = 1e-6


def _solve_gh(instance: ProblemInstance, phase1: GHPhase1Config, seed: int):
    result = run_gh(instance, phase1)
    breakdown = result.objective_breakdown
    residual = sum(result.residual_demand_by_query.values())
    return result.independently_feasible, breakdown, residual


def _solve_agh(instance: ProblemInstance, phase1: GHPhase1Config, seed: int):
    result = run_agh(instance, phase1, random_seed=seed)
    breakdown = result.final_objective_breakdown
    residual = 0.0
    feasible = result.completed
    return feasible, breakdown, residual


def _solve_milp(instance: ProblemInstance, phase1: GHPhase1Config, seed: int,
                *, time_limit: float | None = None):
    solver_cfg = SolverConfig(backend=SolverBackend.HIGHS)
    if time_limit is not None:
        solver_cfg = SolverConfig(backend=SolverBackend.HIGHS,
                                  time_limit_seconds=time_limit)
    run = execute_and_record_pdm_run(PdmProblemData(instance), solver_cfg)
    breakdown = run.scientific_evidence.objective_breakdown
    feasible = run.accepted_run
    residual = 0.0
    return feasible, breakdown, residual


SOLVERS: dict[str, Callable] = {
    "gh": _solve_gh,
    "agh": _solve_agh,
    "milp": _solve_milp,
}
