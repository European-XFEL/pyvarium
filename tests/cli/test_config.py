import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyvarium.cli import app

runner = CliRunner()


def test_list():
    res = runner.invoke(app, ["config", "list"])
    assert (
        res.stdout
        == """{
    'pipenv': PosixPath('/root/.local/bin/pipenv'),
    'pipx': PosixPath('/usr/local/bin/pipx'),
    'poetry': PosixPath('/root/.local/bin/poetry'),
    'spack': PosixPath('/spack/bin/spack')
}
"""
    )


def test_info():
    res = runner.invoke(app, ["config", "info"])
    assert (
        res.stdout
        == """{
    'builtin': PosixPath('/src/pyvarium/src/pyvarium/settings.toml'),
    'user': PosixPath('/root/.config/pyvarium/settings.toml'),
    'local': PosixPath('/src/pyvarium/pyvarium.toml')
}
"""
    )


class TestSetUnset:
    @pytest.fixture(autouse=True, scope="class")
    def tmp_cwd(self, tmp_path_factory):
        tmpdir = tmp_path_factory.mktemp("TestSetUnset")
        os.chdir(tmpdir)
        yield tmpdir

    def test_set(self):
        res = runner.invoke(app, ["config", "set", "--scope", "local", "spack", ""])
        assert res.exit_code == 0

        res = runner.invoke(app, ["config", "list"])
        assert (
            res.stdout
            == """{
    'pipenv': PosixPath('/root/.local/bin/pipenv'),
    'pipx': PosixPath('/usr/local/bin/pipx'),
    'poetry': PosixPath('/root/.local/bin/poetry'),
    'spack': ''
}
"""
        )

    def test_unset(self):
        res = runner.invoke(app, ["config", "unset", "--scope", "local", "spack"])
        assert res.exit_code == 0
        assert (
            res.stdout
            == """{
    'pipenv': PosixPath('/root/.local/bin/pipenv'),
    'pipx': PosixPath('/usr/local/bin/pipx'),
    'poetry': PosixPath('/root/.local/bin/poetry')
}
"""
        )


# def test_set_user():
#     res = runner.invoke(app, ["config", "set", "--scope", "user", "spack", ""])
#     assert (
#         res.stdout
#         == """{
#     'pipenv': PosixPath('/root/.local/bin/pipenv'),
#     'pipx': PosixPath('/usr/local/bin/pipx'),
#     'poetry': PosixPath('/root/.local/bin/poetry'),
#     'spack': ''
# }
# """
#     )

#     Path("~/.config/pyvarium/settings.toml").expanduser().unlink()
