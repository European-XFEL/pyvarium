import sys
from enum import Enum

import typer
from loguru import logger
from loguru._defaults import LOGURU_FORMAT

from . import install, modulegen, new, setup, sync

app = typer.Typer()


class LogLevel(str, Enum):
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


@app.callback()
def main(
    log_level: LogLevel = typer.Option(
        LogLevel.info, help="Pick which level of output to show", case_sensitive=False
    ),
    verbose: int = typer.Option(0, "--verbose", "-v", count=True),
):
    """Tool used to deploy computational environments managed with multiple
    tools like Poetry and Spack."""

    #  This logger is kinda weird but I wanted to play around with having all output
    #  come out via the logger, with verbosity affecting how it looks

    logger.remove()

    logger_formats = {
        0: "<level>{message}</level>",
        1: "<level>{level:2.2} | {message}</level>",
        2: "<level>{level: <8}</level> | <level>{message}</level>",
        3: LOGURU_FORMAT,  # The default loguru format
    }

    if verbose <= 1:
        #  Add two loggers, one with a filter on INFO that just shows the message
        #  without colour or any other fancy formatting
        logger.add(
            sys.__stdout__,
            format="{message}",
            level=log_level,
            colorize=True,
            filter=lambda record: record["level"].name == "INFO",
        )

        #  And one with a filter on everything that isn't INFO, with the correct
        #  formatting level
        logger.add(
            sys.__stdout__,
            format=logger_formats[verbose],
            level=log_level,
            colorize=True,
            filter=lambda record: record["level"].name != "INFO",
        )
    else:
        #  Else there's no need for filtering
        logger.add(
            sys.__stdout__,
            format=logger_formats[verbose],
            level=log_level,
            colorize=True,
        )

    spack_fmt = {
        0: "Spack worker {extra[id]: <4}: {message}",
        1: (
            "<level>{level:2.2}</level> | <yellow>{extra[id]:3.3}</yellow> | "
            "<level>{message}</level>"
        ),
        2: (
            "<level>{level: <8}</level> | <yellow>WORKER {extra[id]: <4}</yellow> | "
            "<level>{message}</level>"
        ),
        3: (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | <yellow>WORKER {extra[id]: <4}</yellow>  | "
            "<level>{message}</level>"
        ),
    }

    # Create a new logger called `SPACK`
    logger.level("SPACK", no=4, color="<magenta><bold>")
    # Add a new handler for the `SPACK` logger which outputs the process ID
    logger.add(
        sys.stdout,
        format=spack_fmt[verbose],
        colorize=True,
        level="SPACK",
        filter=lambda record: record["level"].name == "SPACK",
        enqueue=True,  # Enqueue the log message to the main thread
    )


app.add_typer(install.app, name="install")
app.add_typer(new.app, name="new")
app.add_typer(setup.app, name="setup")
app.add_typer(sync.app, name="sync")
app.add_typer(modulegen.app, name="modulegen")


if __name__ == "__main__":
    app()
