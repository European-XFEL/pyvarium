import os
from pathlib import Path
from typing import List

import pytest
from pytest import TempPathFactory
from typer.testing import CliRunner

from pyvarium.cli import app
from pyvarium.installers.spack import SpackEnvironment

runner = CliRunner()


PIPFILE = """[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
setuptools = "==63.0.0"

[dev-packages]
"""

SPACK = """spack:
    concretizer:
        unify: true
    specs:
        - python
        - py-pip
        - py-numpy
    view:
        default:
            root: {dir}/.venv
            link_type: symlink
            link: run
"""


@pytest.fixture(autouse=True, scope="module")
def tmp_cwd(tmp_path_factory: TempPathFactory):
    tmpdir: Path = tmp_path_factory.mktemp("cli.sync")
    os.chdir(tmpdir)

    pipfile = tmpdir / "Pipfile"
    pipfile.write_text(PIPFILE)

    spack = tmpdir / "spack.yaml"
    spack.write_text(SPACK.format(dir=str(tmpdir)))

    runner.invoke(app, ["install"])

    pipfile.write_text(PIPFILE)

    yield tmpdir


def test_call():
    res = runner.invoke(app, ["sync"])
    assert res.exit_code == 0


def test_pipenv_synced():
    se = SpackEnvironment(Path.cwd())
    packages_python = se.find_python_packages()
    package_names = [package["name"] for package in packages_python]
    assert "numpy" in package_names
