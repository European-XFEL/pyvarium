from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from ..installers.poetry import Poetry
from ..installers.pyvarium import Pyvarium
from ..installers.spack import Spack

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(
    path: Path = typer.Argument(..., file_okay=False),
):
    path = Path(path).absolute()

    if not path.exists() or not path.is_dir():
        logger.critical(f"path {path} is not a directory", err=True)
        raise typer.Abort()

    config_path = path / "pyproject.toml"

    if not config_path.is_file():
        logger.critical(f"{config_path} not found, did you run `pyvarium new`?")
        raise typer.Abort()

    installer = Pyvarium.env_load(path)

    installer.sync_python_packages()


if __name__ == "__main__":
    app()
