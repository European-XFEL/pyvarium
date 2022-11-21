import shutil
import subprocess
import sys
from enum import Enum
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.prompt import Confirm

from . import add, config, install, modulegen, new, sync

app = typer.Typer()

CONSOLE = Console()


class LogLevel(str, Enum):
    """Enum of valid logging levels for console output."""

    trace = "TRACE"
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"

    @classmethod
    def _missing_(cls, name):
        for member in cls:
            if member.name.lower() == name:
                return member

        raise ValueError(f"{name} is not a valid log level")


def pre_checks():
    real_python_path = Path(sys.executable).resolve()
    external_dependencies = {
        "pipx": (shutil.which("pipx"), f"{real_python_path} -m pip install pipx"),
        "pipenv": (shutil.which("pipenv"), "pipx install pipenv"),
    }

    for name, (path, install_cmd) in external_dependencies.items():
        if path is None:
            CONSOLE.print(
                Markdown(
                    f"`{name}` is **required** for pyvarium to work but cannot be"
                    "installed as a direct dependency. Would you like to install it? "
                    f"This will run the command `{install_cmd}`."
                )
            )
            if Confirm.ask(f"Run `{install_cmd}`?"):
                subprocess.run(install_cmd, shell=True)
            else:
                raise FileNotFoundError(name)


@app.callback(invoke_without_command=True, no_args_is_help=True)
def main(
    log_level: LogLevel = typer.Option(
        LogLevel.info, help="Pick which level of output to show", case_sensitive=False
    ),
):
    """Deploy mixed computational environments with dependencies and packages
    provided by Spack and Pipenv"""

    pre_checks()

    logger.remove()

    logger.configure(
        handlers=[
            {
                "sink": RichHandler(markup=True),
                "format": "{message}",
                "level": log_level,
            }
        ]
    )


app.add_typer(add.app, name="add")
app.add_typer(config.app, name="config")
app.add_typer(install.app, name="install")
app.add_typer(modulegen.app, name="modulegen")
app.add_typer(new.app, name="new")
app.add_typer(sync.app, name="sync")


if __name__ == "__main__":
    app()
