from pathlib import Path
from typing import Optional

from pyvarium.installers.base import Environment, Program

PIPFILE = """[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]

[dev-packages]

"""


class Pipenv(Program):
    def __post_init__(self):
        self.env["PIPENV_VENV_IN_PROJECT"] = "1"


class PipenvEnvironment(Environment):
    program: Pipenv

    def __post_init__(self):
        self.program.cwd = self.path
        self.program.env["VIRTUAL_ENV"] = str((self.path / ".venv").absolute())
        self.program.env["PIPENV_PYTHON"] = str(
            (self.path / ".venv" / "bin" / "python").absolute()
        )

    def new(
        self,
        *,
        python_path: Optional[Path] = None,
    ):
        commands = []

        if python_path is not None:
            commands.extend([f"--python={str(python_path.absolute())}"])
        else:
            commands.extend(["--three"])

        self.path.mkdir(exist_ok=True, parents=True)

        (self.path / "Pipfile").write_text(PIPFILE)

        return self.program.cmd(*commands)

    def add(self, *packages):
        return self.program.cmd("install", *packages)

    def install(self):
        return self.program.cmd("install")

    def lock(self):
        return self.program.cmd("lock")
