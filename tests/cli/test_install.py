import os
from pathlib import Path
from typing import List

import pytest
from pytest import TempPathFactory
from typer.testing import CliRunner

from pyvarium.cli import app
from pyvarium.installers.pipenv import PipenvEnvironment
from pyvarium.installers.spack import SpackEnvironment

runner = CliRunner()


PIPFILE = """[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
numpy = "==1.23.2"
setuptools = "==63.0.0"
extra-data = "*"

[dev-packages]
"""

SPACK = """spack:
    concretizer:
        unify: true
    specs:
        - python
        - py-pip
        - py-numpy
"""


class TestInstall:
    @pytest.fixture(autouse=True, scope="class")
    def tmp_cwd(self, tmp_path_factory: TempPathFactory):
        tmpdir: Path = tmp_path_factory.mktemp("cli.install", numbered=False)
        os.chdir(tmpdir)

        pipfile = tmpdir / "Pipfile"
        pipfile.write_text(PIPFILE)

        spack = tmpdir / "spack.yaml"
        spack.write_text(SPACK)

        yield tmpdir

    def test_call(self):
        res = runner.invoke(app, ["install"])
        assert res.exit_code == 0

    def test_spack_packages(self):
        se = SpackEnvironment(Path.cwd())
        packages: List[str] = [p["name"] for p in se.find()]

        assert any("python" in p for p in packages)
        assert any("py-pip" in p for p in packages)
        assert any("py-numpy" in p for p in packages)

    def test_pipenv_packages(self):
        se = SpackEnvironment(Path.cwd())
        packages_python = se.find_python_packages(only_names=True)
        assert any("extra_data" in p for p in packages_python)
