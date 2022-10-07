import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyvarium.cli import app
from pyvarium.installers.spack import SpackEnvironment

runner = CliRunner()


class TestNew:
    @pytest.fixture(autouse=True, scope="class")
    def tmp_cwd(self, tmp_path_factory):
        tmpdir = tmp_path_factory.mktemp("TestNew")
        os.chdir(tmpdir)
        yield tmpdir

    def test_call(self):
        res = runner.invoke(app, ["new", "test-env"])
        assert res.exit_code == 0

    def test_error_on_exists(self):
        res = runner.invoke(app, ["new", "test-env"])
        assert res.exit_code != 0

    def test_expected_files(self):
        assert Path("./test-env/Pipfile").exists()
        assert Path("./test-env/Pipfile.lock").exists()
        assert Path("./test-env/spack.yaml").exists()
        assert Path("./test-env/spack.lock").exists()
        assert Path("./test-env/.venv").exists()

    def test_expected_deps(self):
        se = SpackEnvironment(Path("./test-env"))
        packages = [p["name"] for p in se.find()]
        assert "python" in packages
        assert "py-pip" in packages
