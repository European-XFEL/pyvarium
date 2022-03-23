"""
Module for handling environment creation, but not the installation phases.
This should only set up the required configuration files, similar to how `poetry
new` only creates the `pyproject.toml` file but does not install anything.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from ..installers.poetry import Poetry
from ..installers.pyvarium import Pyvarium
from ..installers.spack import Spack

from ..config import settings

app = typer.Typer()


class UseOrInstall(str, Enum):
    use = "use"
    install = "install"
    skip = "skip"


@app.callback(invoke_without_command=True)
def main(
    path: Path = typer.Argument(..., file_okay=False),
    poetry_prefix: Path = typer.Argument(settings.poetry_prefix, file_okay=False),
    spack_prefix: Path = typer.Argument(settings.spack_prefix, file_okay=False),
    name: Optional[str] = None,
    install_processes: int = 1,
    skip_py_install: bool = False,
):
    """Create a new environment - requires existing instances"""

    name = name or path.name

    spack = Spack.env_create(
        path.absolute(),
        spack_prefix.absolute(),
    )

    poetry = Poetry.env_create(
        path.absolute(),
        poetry_prefix.absolute(),
    )

    pyvarium = Pyvarium.env_create(
        path.absolute(),
        poetry,
        spack,
    )

    pyvarium.sync_python_constraint()

    if not skip_py_install:
        pyvarium.spack.add(["py-pip"])
        pyvarium.spack.install(install_processes)

        if not (path / "venv/bin/pip").exists():
            (path / "venv/bin/pip").symlink_to(path / "venv/bin/pip3")


if __name__ == "__main__":
    app()
