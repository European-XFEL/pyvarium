"""
Module for handling environment creation, but not the installation phases.
This should only set up the required configuration files, similar to how `poetry
new` only creates the `pyproject.toml` file but does not install anything.
"""

from pathlib import Path

import typer
from loguru import logger
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn

from pyvarium.installers import pipenv, spack

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(
    path: Path = typer.Argument(..., file_okay=False),
):
    """Create a new environment - requires existing instances"""

    if path.exists():
        raise typer.Abort(f"Path {path} already exists")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Creating new Pyvarium environment")
        se = spack.SpackEnvironment(path)
        progress.update(task, description="Creating Spack environment")
        se.new()
        progress.update(task, description="Adding `python` and `pip`")
        se.add("python@3:")
        se.add("py-pip")
        progress.update(task, description="Concretizing")
        se.concretize()
        progress.update(task, description="Installing")
        se.install()

        pe = pipenv.PipenvEnvironment(path)
        pe.new(python_path=se.path / ".venv" / "bin" / "python")
        se_python = [
            f"{p['name']}=={p['version']}"
            for p in se.find_python_packages()
            if p["name"] != "pip"
        ]
        pe.add(*se_python)


if __name__ == "__main__":
    app()
