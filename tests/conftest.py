from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest


def pytest_addoption(parser):
    parser.addoption(
        "--integration-only",
        action="store_true",
        default=False,
        help="Run only integration tests",
    )

    parser.addoption(
        "--cached-spack",
        action="store",
        default=None,
        help="Path to Spack instance with python and py-pip already installed",
    )


@pytest.fixture(scope="session")
def cached_spack(request: FixtureRequest) -> Path:
    cached_spack = request.config.option.cached_spack

    if cached_spack is None:
        pytest.skip("No cached spack environment specified")

    return Path(cached_spack)


@pytest.fixture(scope="function", autouse=True)
def integration_only(request: FixtureRequest) -> None:
    integration_only = request.config.option.integration_only

    if integration_only and "cached_spack" not in request.fixturenames:
        pytest.skip("Integration only specified")
