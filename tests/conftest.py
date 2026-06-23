from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("baseline")
    group.addoption(
        "--baseline",
        action="store",
        default="all",
        choices=["cold", "generic", "all"],
        help="Baseline selection for notebook execution tests.",
    )
    group.addoption(
        "--cold-kernel",
        action="store",
        default="python3",
        help="Kernel name used for cold baseline.",
    )
    group.addoption(
        "--generic-kernel",
        action="store",
        default="python3",
        help="Kernel name used for generic baseline.",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "baseline" in metafunc.fixturenames:
        requested = metafunc.config.getoption("baseline")
        baselines = ["cold", "generic"] if requested == "all" else [requested]
        metafunc.parametrize("baseline", baselines, ids=baselines)


@pytest.fixture
def kernel_name(request: pytest.FixtureRequest, baseline: str) -> str:
    return request.config.getoption(f"{baseline}_kernel")
