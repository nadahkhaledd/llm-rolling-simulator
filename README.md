# Rolling-Horizon Simulator (Stage 2)

Trace-replay simulator for LLM inference resource allocation on
heterogeneous GPU clusters. Replays the Azure LLM Inference Trace
window by window, calling Stage-1 solvers (GH, AGH, MILP) and
comparing their cost, runtime, and feasibility across the horizon.

Based on: "Scalable Joint Resource Allocation for SLO-Constrained LLM
Inference in Heterogeneous GPU Clouds" by Cheng & Nguyen (arXiv
2604.07472v2).

## Project structure

```
src/
├── run_simulation.py          ← Entry point
├── simulator/                 ← Core simulation package
│   ├── models.py              ← WindowResult, HorizonSummary dataclasses
│   ├── adapters.py            ← Solver wrappers + SOLVERS registry
│   ├── engine.py              ← scale_instance_load, run_window, run_rolling_horizon
│   ├── trace_loader.py        ← Load JSON/CSV traces, busiest window selection
│   └── output.py              ← CSV writers
└── cli/                       ← CLI/configuration package
    ├── parser.py              ← Argument parsing, output path construction
    └── instance.py            ← Base instance builder (tiny or scaled)

data/
└── trace_20240514-5min.json   ← Azure trace: 288 five-minute windows (May 14, 2024)

scripts/
├── extract_day_data.py        ← Extract a single day from the raw Azure CSV
└── convert_csv_to_json_trace.py ← Convert day CSV to JSON load multipliers

out/{instance_size}/           ← Results organized by instance size (gitignored)
```

## Prerequisites

- Python 3.12+
- [Antonio's Stage-1 package](https://github.com/antonioarbizzanitonelli/pacs-project)
  installed as editable: `pip install -e ../pacs-project`

## How to run

```bash
# Set the Python path
export PYTHONPATH=src

# 2×2×2 instance, busiest 5 windows, all three methods
python src/run_simulation.py --methods gh agh milp --busiest 5 --out-dir out

# 6×6×10 paper-scale instance, busiest 10, heuristics only
python src/run_simulation.py --methods gh agh --busiest 10 --dimensions 6 6 10 --out-dir out

# 6×6×10 MILP with time limit (slow — ~118s per window)
python src/run_simulation.py --methods milp --busiest 5 --dimensions 6 6 10 \
    --time-limit 120 --out-dir out

# Full 288-window trace (default)
python src/run_simulation.py --methods gh agh --dimensions 6 6 10 --out-dir out
```

Pass `--dimensions I J K` to set the instance size (query types × models
× GPU tiers). Default is 2×2×2. The `--busiest N` flag selects only the
N highest-demand windows for faster experimentation.

## Output

Each run produces two CSVs in `out/{size}/`:

**Windows CSV** — one row per (window, method):
`window_index, load_multiplier, method, feasible, total_cost,
gpu_rental, model_storage, data_storage, delay_penalty, unmet_penalty,
total_residual_demand, runtime_seconds`

**Summary CSV** — one row per method:
`method, windows, feasible_windows, total_cost_sum, mean_cost_per_window,
mean_runtime_seconds, violation_rate_percent`

## Architecture

The key design is the **adapter pattern**. Each solver is wrapped into a
uniform signature:

```python
(instance, phase1_config, seed) -> (feasible: bool, breakdown, residual: float)
```

Registered in the `SOLVERS` dict in `adapters.py`. Adding a new solver
variant is one function + one dict entry — the entire simulator
infrastructure (trace replay, timing, aggregation, CSV output) works
automatically.

## Data

[Azure LLM Inference Trace 2024](https://github.com/Azure/AzurePublicDataset/blob/master/AzureLLMInferenceDataset2024.md)
(code-completion trace). May 14 is the busiest day (~3.21M requests).
The raw CSVs are not included due to size; download from the Azure
Public Dataset and run the scripts to process:

```bash
python scripts/extract_day_data.py --day 2024-05-14 data/AzureLLMInferenceTrace_code_1week.csv
python scripts/convert_csv_to_json_trace.py data/azure_trace_2024-05-14.csv
```

The processed trace (`data/trace_20240514-5min.json`) is included.
