from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from loguru import logger
from rich.status import Status

from pyvarium.installers import pipenv, spack

app = typer.Typer(no_args_is_help=True, help="Add packages via spack or pipenv.")


def main(
    path: Optional[Path] = None,
    *,
    pipenv_add: Optional[list[str]] = None,
    spack_add: Optional[list[str]] = None,
):
    if path is None:
        path = Path(".")

    path = path.resolve()

    with Status("Spack add") as status:
        se = spack.SpackEnvironment(path, status=status)

        if spack_add:
            se.add(*spack_add)

        se.install()

    with Status("Pipenv add") as status:
        pe = pipenv.PipenvEnvironment(path, status=status)
        if se_python := se.find_python_packages(only_names=True):
            logger.info(f"Python packages in spack environment: {se_python}")
            pe.add(*se_python)

        if pipenv_add:
            pe.add(*pipenv_add)


@app.command(name="spack")
def _spack(
    packages: List[str],
    *,
    path: Optional[Path] = typer.Option(".", file_okay=False),
):
    main(path, spack_add=packages)


@app.command(name="pipenv")
def _pipenv(
    packages: List[str],
    *,
    path: Optional[Path] = typer.Option(".", file_okay=False),
):
    main(path, pipenv_add=packages)
