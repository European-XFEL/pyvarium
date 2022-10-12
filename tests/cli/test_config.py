import os
from pathlib import Path
from unittest import mock

import pytest
from typer.testing import CliRunner

from pyvarium.cli import app
from pyvarium.config import THIS_DIR, Settings

runner = CliRunner()


@pytest.fixture(autouse=True, scope="module")
def tmp_cwd(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("cli.config")
    os.chdir(tmp_dir)
    yield tmp_dir


@pytest.fixture(scope="module")
def tmp_home(tmp_cwd: Path):
    tmp_home = tmp_cwd / ".home"
    assert tmp_home.parts[1] == "tmp"

    tmp_home_bin = tmp_home / ".local" / "bin"

    with mock.patch.dict(
        os.environ, {"HOME": str(tmp_home), "PATH": str(tmp_home_bin)}
    ):
        tmp_home_bin.mkdir(parents=True, exist_ok=False)

        (tmp_home_bin / "pipenv").touch(mode=14272)
        (tmp_home_bin / "pipx").touch(mode=14272)
        (tmp_home_bin / "poetry").touch(mode=14272)
        (tmp_home_bin / "spack").touch(mode=14272)

        yield tmp_home


@pytest.fixture(scope="module")
def invoke(tmp_home):
    import pyvarium.cli.config

    with mock.patch.object(pyvarium.cli.config, "settings", Settings.load_dynaconf()):
        yield lambda l: runner.invoke(app, l)


def test_list(invoke, tmp_home):
    res = invoke(["config", "list"])
    assert (
        res.stdout
        == f"""{{
    'pipenv': PosixPath('{tmp_home}/.local/bin/pipenv'),
    'pipx': PosixPath('{tmp_home}/.local/bin/pipx'),
    'poetry': PosixPath('{tmp_home}/.local/bin/poetry'),
    'spack': PosixPath('{tmp_home}/.local/bin/spack')
}}
"""
    )


def test_info(invoke, tmp_home, tmp_cwd):
    res = invoke(["config", "info"])
    assert (
        res.stdout
        == f"""{{
    <Scope.builtin: 'builtin'>: PosixPath('{THIS_DIR}/settings.toml'),
    <Scope.user: 'user'>: PosixPath('{tmp_home}/.config/pyvarium/settings.toml'),
    <Scope.local: 'local'>: PosixPath('{tmp_cwd}/pyvarium.toml')
}}
"""
    )


def test_set(invoke, tmp_home, tmp_cwd: Path):
    res = invoke(["config", "set", "--scope", "local", "spack", ""])
    assert res.exit_code == 0

    res = invoke(["config", "list"])
    assert (
        res.stdout
        == f"""{{
    'pipenv': PosixPath('{tmp_home}/.local/bin/pipenv'),
    'pipx': PosixPath('{tmp_home}/.local/bin/pipx'),
    'poetry': PosixPath('{tmp_home}/.local/bin/poetry'),
    'spack': ''
}}
"""
    )

    assert (tmp_cwd / "pyvarium.toml").is_file()
    assert 'spack = ""' in (tmp_cwd / "pyvarium.toml").read_text()


def test_unset(invoke, tmp_home, tmp_cwd: Path):
    res = invoke(["config", "unset", "--scope", "local", "spack"])
    assert res.exit_code == 0
    assert (
        res.stdout
        == f"""{{
    'pipenv': PosixPath('{tmp_home}/.local/bin/pipenv'),
    'pipx': PosixPath('{tmp_home}/.local/bin/pipx'),
    'poetry': PosixPath('{tmp_home}/.local/bin/poetry')
}}
"""
    )

    assert (tmp_cwd / "pyvarium.toml").is_file()
    assert "spack" not in (tmp_cwd / "pyvarium.toml").read_text()


def test_set_user(invoke, tmp_home: Path):
    res = invoke(["config", "set", "--scope", "user", "spack", ""])
    assert (
        res.stdout
        == f"""{{
    'pipenv': PosixPath('{tmp_home}/.local/bin/pipenv'),
    'pipx': PosixPath('{tmp_home}/.local/bin/pipx'),
    'poetry': PosixPath('{tmp_home}/.local/bin/poetry'),
    'spack': ''
}}
"""
    )

    tmp_home_config = tmp_home / ".config" / "pyvarium" / "settings.toml"
    assert tmp_home_config.is_file()
    assert 'spack = ""' in tmp_home_config.read_text()
