import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyvarium.cli import app
from pyvarium.installers.spack import SpackEnvironment

runner = CliRunner()


@pytest.fixture(autouse=True, scope="module")
def tmp_cwd(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("cli.modulegen")
    os.chdir(tmpdir)
    res = runner.invoke(app, ["new", "test-env"])
    assert res.exit_code == 0
    os.chdir(tmpdir / "test-env")
    yield tmpdir / "test-env"


def test_call(tmp_cwd):
    res = runner.invoke(app, ["modulegen"])
    se = SpackEnvironment(Path("."))
    assert res.exit_code == 0

    assert "mode load" in res.stdout
    assert "mode remove" in res.stdout

    assert se.program.env["PATH"].strip(";").strip(":") not in res.stdout


def test_call_with_name(tmp_cwd):
    res = runner.invoke(app, ["modulegen", "--name", "foobar"])
    assert res.exit_code == 0

    assert "#  foobar" in res.stdout
    assert "VIRTUAL_ENV foobar" in res.stdout
