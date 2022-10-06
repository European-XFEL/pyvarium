from pathlib import Path
from typing import Optional

import typer
from rich.status import Status

from pyvarium.installers import pipenv, spack

app = typer.Typer(help="Sync Spack-managed packages with Pipenv.")


@app.callback(invoke_without_command=True)
def main(
    path: Optional[Path] = typer.Option(".", file_okay=False),
):
    if path is None:
        path = Path(".")

    path = path.resolve()

    with Status("Syncing Spack and Pipenv packages") as status:
        se = spack.SpackEnvironment(path, status=status)
        pe = pipenv.PipenvEnvironment(path, status=status)
        if se_python := se.find_python_packages(only_names=True):
            pe.add(*se_python)


if __name__ == "__main__":
    app()
