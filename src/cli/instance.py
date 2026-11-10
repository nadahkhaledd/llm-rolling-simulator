from __future__ import annotations

from dataclasses import replace

from llm_resource_allocation.data.tiny_instances import make_heterogeneous_tiny_instance
from llm_resource_allocation.data.scaling_experiment_instances import make_scaling_experiment_case
from llm_resource_allocation.domain.units import UnitConvention


def build_base_instance(dimensions: tuple[int, int, int] | None = None):
    if dimensions is None:
        return replace(
            make_heterogeneous_tiny_instance(),
            unit_convention=UnitConvention.COHERENT,
        )
    query_count, model_count, tier_count = dimensions
    case = make_scaling_experiment_case(query_count, model_count, tier_count)
    return case.instance
