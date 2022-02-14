"""Install the specified environment."""

from pathlib import Path

import typer
from loguru import logger

from ..installers.pyvarium import Pyvarium

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(
    path: Path = typer.Argument(...),
    install_processes: int = 1,
    force: bool = False,
    noconfirm: bool = False,
):
    """Install the specified environment."""
    path = Path(path).absolute()

    if not path.exists() or not path.is_dir():
        logger.critical(f"path {path} is not a directory", err=True)
        raise typer.Abort()

    config_path = path / "pyproject.toml"

    if not config_path.is_file():
        logger.critical(f"{config_path} not found, did you run `pyvarium new`?")
        raise typer.Abort()

    installer = Pyvarium.env_load(path)

    spack_src = (
        installer.spack.installer_config.prefix / "share" / "spack" / "setup-env.sh"
    )

    logger.info(
        f"Use `source {spack_src}` to activate the spack instance associated with this "
        "environment."
    )

    logger.info("Installing base spack packages")

    installer.spack.install(install_processes)

    logger.info("Activate spack environment with `spack env activate .`")

    logger.info(
        "Once environment is activated, follow standard spack environment setup "
        "procedures, see docs if required: "
        "https://spack.readthedocs.io/en/latest/environments.html"
    )

    installer.sync_python_constraint()

    installer.spack.cmd("add py-pip")

    installer.spack.cmd("compiler find")
    concretize = installer.spack.cmd("concretize --force")
    logger.info(concretize.stdout.decode())
    find = installer.spack.cmd("find --show-concretized --deps --only-missing")
    logger.info(find.stdout.decode())

    if (
        noconfirm
        or typer.prompt("Do you want to install packages? (y/n)", default="n") == "y"
    ):
        if install_processes > 1:
            logger.info(
                f"Running spack install with {install_processes}, this may take a while"
            )
        else:
            logger.info("Running spack install, this may take a while")

        installer.spack.install(processes=install_processes)

    installer.sync_python_packages()

    installer.poetry.install(
        prepend=f"{installer.spack.installer_config.executable} env activate . && "
    )

    logger.info(
        "Environment setup complete, add more packages to the environment with spack "
        "or poetry as normal."
    )
    logger.warning(
        "Make sure to keep any python packages added via spack locked via poetry.",
    )


if __name__ == "__main__":
    app()
