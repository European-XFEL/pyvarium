"""
Module for handling environment creation, but not the installation phases.
This should only set up the required configuration files, similar to how `poetry
new` only creates the `pyproject.toml` file but does not install anything.
"""

from pathlib import Path

import typer
from loguru import logger

from pyvarium.installers import pipenv, spack

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(
    path: Path = typer.Argument(..., file_okay=False),
):
    """Create a new environment - requires existing instances"""

    # if path.exists():
    #     raise typer.Exit(f"Path {path} already exists")

    se = spack.SpackEnvironment(path)
    # se.new()
    # se.add("python", "py-pip")
    # se.concretize()
    # se.install()

    pe = pipenv.PipenvEnvironment(path)
    # pe.new(python_path=se.path / ".venv" / "bin" / "python")
    se_python = [
        f"{p['name']}=={p['version']}"
        for p in se.find_python_packages()
        if p["name"] != "pip"
    ]
    pe.add(*se_python)


if __name__ == "__main__":
    app()
