from pathlib import Path

import typer
from rich.status import Status

from pyvarium.installers import pipenv, spack

app = typer.Typer(help="Concretize and install an existing environment.")


@app.callback(invoke_without_command=True)
def main(path: Path = typer.Option(".", file_okay=False)):
    path = path.resolve()

    with Status("Spack install") as status:
        se = spack.SpackEnvironment(path, status=status)
        se.concretize()
        se.install()

    with Status("Pipenv install") as status:
        pe = pipenv.PipenvEnvironment(path, status=status)
        pe.install()
