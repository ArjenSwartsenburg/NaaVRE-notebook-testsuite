# NaaVRE-notebook-testsuite

Starter validation project for **Stage 2 (Notebook execution)** of the master's thesis validation methodology for the NaaVRE Conda environment service.

## Tech stack

- Python 3.10+
- pytest
- nbclient
- nbformat

## Install

```bash
python -m pip install -e ".[test]"
```

## Run tests

Run all notebook execution tests against both baselines:

```bash
pytest
```

Run only one baseline:

```bash
pytest --baseline generic
pytest --baseline cold
```

Optionally set distinct kernels per baseline:

```bash
pytest --baseline all --generic-kernel python3 --cold-kernel python3
```

## What the tests validate

Synthetic notebooks (nbformat 4.5, Python 3 kernelspec):

- `happy_path_numpy.ipynb`: imports `numpy` and performs a computation
- `happy_path_requests.ipynb`: imports `requests`
- `missing_import.ipynb`: imports a non-existent module (expected import failure)
- `syntax_error.ipynb`: contains invalid Python syntax
- `runtime_error.ipynb`: raises runtime division-by-zero

The pytest module executes each notebook with `nbclient` and records KPIs per run:

- success/failure
- failure category (if any)
- wall-clock execution time

Failure categories follow the thesis taxonomy:

- `extraction_failure`
- `unsatisfiable_constraints`
- `package_resolution_failure`
- `kernel_startup_failure`
- `missing_module_at_runtime`
- `file_or_path_error`
- `data_access_error`
- `timeout`
- `notebook_runtime_exception`

## Baselines

- **Cold**: intended for a fresh, dependency-specific kernel (`--cold-kernel`)
- **Generic**: intended for a default system Python kernel (`--generic-kernel`)

By default both baselines are exercised (`--baseline all`).
