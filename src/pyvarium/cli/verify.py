from pathlib import Path

import typer
from rich.status import Status
from loguru import logger

from pyvarium.installers import spack

app = typer.Typer(
    help="Check that python packages in view are still provided by spack."
)


@app.callback(invoke_without_command=True)
def main(path: Path = typer.Option(".", file_okay=False), fix: bool = False):
    path = path.resolve()

    with Status("Checking status of Spack packages in view") as status:
        se = spack.SpackEnvironment(path, status=status)
        warnings = se.verify()

        if all(len(w) == 0 for w in warnings.values()):
            logger.info("All packages in view are correctly symlinked to spack")

        for path, warning in warnings.items():
            package_name = path.name
            if len(warning) > 0:
                logger.warning(
                    f"[bold]{package_name}[/bold] has "
                    f"[bold red]{len(warning)}[/bold red] files which are not linked correctly"
                )
                if fix:
                    logger.info(f"Fixing {package_name}")
                    for file, target in warning:
                        if file.exists():
                            file.unlink()
                        file.symlink_to(target)
