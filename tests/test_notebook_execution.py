from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import nbformat
import pytest
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError, CellTimeoutError, DeadKernelError


NOTEBOOK_DIR = Path(__file__).resolve().parents[1] / "notebooks"


REQUIRED_FAILURE_CATEGORIES = {
    "extraction_failure",
    "unsatisfiable_constraints",
    "package_resolution_failure",
    "kernel_startup_failure",
    "missing_module_at_runtime",
    "file_or_path_error",
    "data_access_error",
    "timeout",
    "notebook_runtime_exception",
}


@dataclass(frozen=True)
class NotebookCase:
    notebook_name: str
    should_succeed: bool
    expected_failure_category: str | None


@dataclass(frozen=True)
class ExecutionKPI:
    baseline: str
    kernel_name: str
    notebook_name: str
    succeeded: bool
    failure_category: str | None
    wall_clock_seconds: float


def classify_failure(exception: BaseException) -> str:
    message = str(exception).lower()

    if isinstance(exception, nbformat.reader.NotJSONError):
        return "extraction_failure"

    if isinstance(exception, CellTimeoutError) or "timeout" in message:
        return "timeout"

    if isinstance(exception, DeadKernelError) or "no such kernel" in message:
        return "kernel_startup_failure"

    if isinstance(exception, CellExecutionError):
        if "modulenotfounderror" in message or "importerror" in message:
            return "missing_module_at_runtime"
        if "filenotfounderror" in message or "no such file or directory" in message:
            return "file_or_path_error"
        if (
            "permissionerror" in message
            or "access denied" in message
            or "forbidden" in message
            or "unauthorized" in message
        ):
            return "data_access_error"
        return "notebook_runtime_exception"

    if "unsatisfiable" in message or "conflict" in message:
        return "unsatisfiable_constraints"

    if "package" in message and "resolution" in message:
        return "package_resolution_failure"

    return "notebook_runtime_exception"


def execute_notebook(notebook_path: Path, baseline: str, kernel_name: str) -> ExecutionKPI:
    started_at = perf_counter()

    try:
        notebook = nbformat.read(notebook_path, as_version=4)
        NotebookClient(
            notebook,
            kernel_name=kernel_name,
            timeout=60,
            allow_errors=False,
            record_timing=True,
        ).execute()
    except Exception as exc:  # noqa: BLE001
        return ExecutionKPI(
            baseline=baseline,
            kernel_name=kernel_name,
            notebook_name=notebook_path.name,
            succeeded=False,
            failure_category=classify_failure(exc),
            wall_clock_seconds=perf_counter() - started_at,
        )

    return ExecutionKPI(
        baseline=baseline,
        kernel_name=kernel_name,
        notebook_name=notebook_path.name,
        succeeded=True,
        failure_category=None,
        wall_clock_seconds=perf_counter() - started_at,
    )


NOTEBOOK_CASES = [
    NotebookCase("happy_path_numpy.ipynb", True, None),
    NotebookCase("happy_path_requests.ipynb", True, None),
    NotebookCase("missing_import.ipynb", False, "missing_module_at_runtime"),
    NotebookCase("syntax_error.ipynb", False, "notebook_runtime_exception"),
    NotebookCase("runtime_error.ipynb", False, "notebook_runtime_exception"),
]


@pytest.mark.parametrize("case", NOTEBOOK_CASES, ids=lambda case: case.notebook_name)
def test_notebook_execution_outcomes(
    case: NotebookCase,
    baseline: str,
    kernel_name: str,
) -> None:
    kpi = execute_notebook(NOTEBOOK_DIR / case.notebook_name, baseline, kernel_name)

    assert kpi.notebook_name == case.notebook_name
    assert kpi.baseline == baseline
    assert kpi.kernel_name == kernel_name
    assert kpi.wall_clock_seconds >= 0
    assert kpi.succeeded is case.should_succeed
    assert kpi.failure_category == case.expected_failure_category


def test_failure_taxonomy_is_complete() -> None:
    assert REQUIRED_FAILURE_CATEGORIES == {
        "extraction_failure",
        "unsatisfiable_constraints",
        "package_resolution_failure",
        "kernel_startup_failure",
        "missing_module_at_runtime",
        "file_or_path_error",
        "data_access_error",
        "timeout",
        "notebook_runtime_exception",
    }
