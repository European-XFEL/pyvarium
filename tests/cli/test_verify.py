import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyvarium.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True, scope="module")
def tmp_cwd(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("cli.verify")
    os.chdir(tmpdir)

    res = runner.invoke(app, ["new", "test-env"])
    assert res.exit_code == 0

    os.chdir(tmpdir / "test-env")

    res = runner.invoke(app, ["add", "spack", "py-numpy"])
    assert res.exit_code == 0

    yield tmpdir / "test-env"


def test_verify_success(tmp_cwd: Path):
    res = runner.invoke(app, ["verify"])
    venv_site_packages = tmp_cwd / ".venv" / "lib" / "python3.8" / "site-packages"
    assert (venv_site_packages / "numpy" / "version.py").is_symlink()
    assert res.exit_code == 0
    assert "correctly symlinked to spack" in res.stdout


@pytest.mark.xfail(
    reason="binary cache injects placeholders to path which breaks tests in image"
)
def test_verify_failure(tmp_cwd: Path):
    venv_site_packages = tmp_cwd / ".venv" / "lib" / "python3.8" / "site-packages"
    numpy_file = venv_site_packages / "numpy" / "version.py"
    numpy_file.unlink()
    assert not numpy_file.is_symlink()
    res = runner.invoke(app, ["verify"])
    print(res.stdout)
    assert res.exit_code != 0
