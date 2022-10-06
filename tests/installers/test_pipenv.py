from pathlib import Path
from typing import Generator
import pytest
import subprocess

from pyvarium.installers.pipenv import PipenvEnvironment


class TestPipenv:
    pe: PipenvEnvironment

    @pytest.fixture(autouse=True, scope="class")
    def root(self, tmp_path_factory) -> Generator[Path, None, None]:
        tmpdir = tmp_path_factory.mktemp("TestPipenv")
        yield Path(tmpdir) / "pipenv"

    @pytest.fixture(autouse=True)
    def environment(self, root):
        pipenv_root = root.parent / "environment"
        subprocess.check_output(["python3", "-m", "venv", pipenv_root / ".venv"])
        self.pe = PipenvEnvironment(pipenv_root)

    def test_venv_in_project_set(self):
        self.pe.program.env["PIPENV_VENV_IN_PROJECT"]

    def test_new(self):
        self.pe.new()
        assert (self.pe.path / "Pipfile").is_file()
        assert (self.pe.path / ".venv" / "bin" / "python3").is_file()

    def test_lock(self):
        lockfile = self.pe.path / "Pipfile.lock"
        lockfile.unlink(missing_ok=True)

        self.pe.lock()

        assert lockfile.is_file()

    def test_add(self):
        res = self.pe.add("cowsay")
        res.check_returncode()
        assert (self.pe.path / ".venv" / "bin" / "cowsay").is_file()
