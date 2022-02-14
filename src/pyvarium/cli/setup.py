from pathlib import Path

import typer
from fastcore.meta import delegates
from loguru import logger

from ..installers import poetry as poetry_installer
from ..installers import spack as spack_installer

app = typer.Typer(help="Set up Spack/Poetry instances")


def _pre_setup(prefix: Path, name: str, force: bool = False) -> None:
    if prefix.is_dir():
        if not force:
            logger.warning(f"{prefix} already exists, use `--force` to overwrite")
            raise FileExistsError(prefix)

        logger.info(f"Removing existing {name} instance at {prefix}")
        prefix.rmdir()


@delegates(spack_installer.Spack.setup)
@app.command()
def spack(
    prefix: Path,
    force: bool = False,
    **kwargs,
) -> None:
    _pre_setup(prefix, "Spack", force=force)

    spack_installer.Spack.setup(prefix, **kwargs)


@delegates(poetry_installer.Poetry.setup)
@app.command()
def poetry(prefix: Path, force: bool = False, **kwargs):
    _pre_setup(prefix, "Poetry", force=force)

    poetry_installer.Poetry.setup(prefix, **kwargs)


if __name__ == "__main__":
    app()
