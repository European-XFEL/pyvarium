from pathlib import Path

import typer
from loguru import logger
from rich.status import Status

from pyvarium.installers import pipenv, spack

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(path: Path = typer.Argument(..., file_okay=False)):
    """Create a new combined Spack and Pipenv environment."""

    if path.exists():
        logger.error(
            f"Directory already exists at path {path.absolute()}\n"
            "Remove it or use another path to continue."
        )
        raise typer.Exit(code=1)

    with Status("Spack setup") as status:
        se = spack.SpackEnvironment(path, status=status)
        se.new()
        se.add("python", "py-pip")
        se.concretize()
        se.install()

    with Status("Pipenv setup") as status:
        pe = pipenv.PipenvEnvironment(path, status=status)
        pe.new(python_path=se.path / ".venv" / "bin" / "python")
        if se_python := se.find_python_packages(only_names=True):
            pe.add(*se_python)
        pe.lock()
