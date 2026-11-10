# Rolling-Horizon Simulator (Stage 2)

This is the Stage-2 trace-replay simulator that sits on top of Antonio's
Stage-1 solvers. It is the piece the paper calls the **rolling-horizon
re-optimization** (v2 Section 5.3) and that Antonio's code did not yet
cover — he implemented the single-instance solvers (GH, AGH, P_DM); this
replays a demand trace and calls them window by window.

## What it does

1. Takes a **base instance** (the workload shape: query types, models,
   GPU tiers) — currently Antonio's heterogeneous 2×2×2 fixture in
   coherent units.
2. Takes a **trace**: a list of per-window load multipliers (e.g. 288
   five-minute windows over a day, or a real Azure diurnal curve).
3. For each window, **scales the arrival rates** by that window's load
   multiplier, then calls a **pluggable solver** (`gh`, `agh`, or `pdm`).
4. **Records** per-window cost (all five components C1–C5), feasibility,
   residual demand, and runtime.
5. **Aggregates** across the whole horizon so the three methods can be
   compared (sum cost, mean cost, mean runtime, violation rate).
6. Writes two CSVs for the comparison/plotting scripts.

## How to run

From the repository root, with the package importable:

```bash
# all three methods on a 10-window synthetic diurnal trace
PYTHONPATH=src:simulator python simulator/run_simulation.py \
    --methods gh agh pdm --windows 10 --out-dir simulator/out

# GH + AGH on the 10 busiest windows of a full 288-window day
PYTHONPATH=src:simulator python simulator/run_simulation.py \
    --methods gh agh --windows 288 --busiest 10 --out-dir simulator/out

# replay a real trace file (JSON list of load multipliers)
PYTHONPATH=src:simulator python simulator/run_simulation.py \
    --methods gh agh pdm --trace simulator/sample_diurnal_trace.json \
    --out-dir simulator/out

# paper-scale base instance: 6 query types x 6 models x 10 tiers
PYTHONPATH=src:simulator python simulator/run_simulation.py \
    --methods gh agh --windows 288 --busiest 5 --dimensions 6 6 10 \
    --out-dir simulator/out
```

By default the base instance is Antonio's fast 2x2x2 fixture. Pass
`--dimensions I M K` to build a paper-scale instance (via Antonio's
scaling builder); `--dimensions 6 6 10` is the paper's base setup.

> Note: the project's `pyproject.toml` pins `requires-python >=3.13`, but
> the code runs on 3.12 too. Running via `PYTHONPATH=src` (instead of
> `pip install -e .`) sidesteps the version pin. On your machine with
> Python 3.13 the normal `pip install -e .` works and you can drop the
> `PYTHONPATH=src` prefix (keep `simulator` on the path).

## Files

| File | What it is |
|------|-----------|
| `rolling_simulator.py` | The engine: trace replay, per-window rescaling, solver adapters, aggregation, CSV output. |
| `run_simulation.py` | CLI runner — the thing you execute. |
| `sample_diurnal_trace.json` | A 288-window synthetic diurnal trace (~10× day/night swing) to replay. |
| `out/` | CSV outputs (`window_results.csv`, `horizon_summary.csv`). |

## Output columns

**window_results.csv** — one row per (method, window):
`window_index, load_multiplier, method, feasible, total_cost,
gpu_rental, model_storage, data_storage, delay_penalty, unmet_penalty,
total_residual_demand, runtime_seconds`

**horizon_summary.csv** — one row per method:
`method, windows, feasible_windows, total_cost_sum, mean_cost_per_window,
mean_runtime_seconds, violation_rate_percent`

## How to extend (your thesis work)

The simulator is built so your heuristic variants plug in with no change
to the replay logic:

1. **New solver variant** — add a function in `rolling_simulator.py` with
   the signature `(instance, phase1, seed) -> (feasible, breakdown,
   residual)` and register it in the `_SOLVERS` dict. Then
   `--methods your_variant` just works.
2. **Real Azure trace** — replace `build_base_instance()` in
   `run_simulation.py` with a paper-scale instance, and point `--trace`
   at a JSON extracted from the Azure LLM Inference Trace (convert
   per-window request counts into load multipliers relative to the daily
   average).
3. **Keep-best rolling rule** — the paper only adopts a new deployment
   if it beats the incumbent. That logic belongs here, between windows,
   and is a natural next addition.

## Where this maps to the paper (v2)

- The per-window solve = one Stage-1 call (Section 4).
- The replay across 288 windows = the rolling horizon (Section 5.3).
- Comparing methods across the horizon = Table 4 / Table 5.
- The "10 busiest windows" shortcut = Prof. Ardagna's suggestion to
  avoid running the full trace while developing.
