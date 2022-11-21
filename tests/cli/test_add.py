import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyvarium.cli import app
from pyvarium.installers.spack import SpackEnvironment

runner = CliRunner()


@pytest.fixture(autouse=True, scope="module")
def tmp_cwd(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("cli.add")
    os.chdir(tmpdir)

    res = runner.invoke(app, ["new", "test-env"])
    assert res.exit_code == 0

    os.chdir(tmpdir / "test-env")

    yield tmpdir / "test-env"


def test_add_spack(tmp_cwd: Path):
    res = runner.invoke(app, ["add", "spack", "py-numpy"])
    assert res.exit_code == 0

    se = SpackEnvironment(tmp_cwd)

    # numpy should be: in spack, a detectable python package in the venv, and
    # should have been synced to Pipenv (named in Pipfile)
    assert any("numpy" in p for p in se.find_python_packages(only_names=True))
    assert "py-numpy" in [p["name"] for p in se.find()]
    assert "numpy" in (tmp_cwd / "Pipfile").read_text()

    # should be a symlink to the spack installed version
    venv_site_packages = tmp_cwd / ".venv" / "lib" / "python3.8" / "site-packages"
    assert (venv_site_packages / "numpy" / "version.py").is_symlink()


def test_add_pipenv(tmp_cwd: Path):
    res = runner.invoke(app, ["add", "pipenv", "extra-data"])
    assert res.exit_code == 0

    # should **still** be a symlink to the spack installed version
    venv_site_packages = tmp_cwd / ".venv" / "lib" / "python3.8" / "site-packages"
    assert (venv_site_packages / "numpy" / "__init__.py").is_symlink()

    # should be a real file from the direct installation into the .venv dir
    assert (venv_site_packages / "extra_data" / "__init__.py").is_file()
