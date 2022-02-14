from pathlib import Path
import subprocess
import pytest

from pyvarium.installers.poetry import Poetry


class TestPoetry:
    @pytest.fixture(autouse=True, scope="class")
    def poetry_home(self, tmp_path_factory) -> Path:
        tmpdir = tmp_path_factory.mktemp("TestPoetry") / "poetry"
        yield tmpdir

    @pytest.fixture(autouse=True, scope="class")
    def environment(self, tmp_path_factory) -> Path:
        return tmp_path_factory.mktemp("environment")

    def test_setup(self, poetry_home: Path):
        poetry_exec = poetry_home / "bin" / "poetry"
        Poetry.setup(poetry_home)
        assert (poetry_exec).is_file()
        assert subprocess.run([str(poetry_exec), "--version"]).returncode == 0

    def test_setup_no_force(self, poetry_home: Path):
        with pytest.raises(FileExistsError):
            Poetry.setup(poetry_home)

    def test_init(self, poetry_home: Path, environment: Path):
        Poetry.env_create(
            env_path=environment,
            executable=poetry_home / "bin" / "poetry",
            venv_create=True,
            in_project=True,
        )
        assert (environment / "pyproject.toml").is_file()
        assert (environment / "poetry.toml").is_file()

    def test_add(self, poetry_home: Path, environment: Path):
        poetry = Poetry(environment, executable=poetry_home / "bin" / "poetry")
        # This should only create the lock file, should not create the
        # environment
        poetry.add("cowsay", lock=True)
        assert "cowsay" in (environment / "pyproject.toml").read_text()
        assert (environment / "poetry.lock").is_file()

    def test_install_env(self, poetry_home: Path, environment: Path):
        poetry = Poetry(environment, executable=poetry_home / "bin" / "poetry")
        poetry.install_env()

        assert (environment / ".venv").is_dir()
        assert (environment / ".venv" / "bin" / "python").is_file()
        assert (environment / ".venv" / "bin" / "cowsay").is_file()
