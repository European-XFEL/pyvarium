from pathlib import Path

import typer
from rich.pretty import pprint

from pyvarium.config import Scope, settings

app = typer.Typer(no_args_is_help=True, help="Modify user settings for pyvarium.")


@app.command(name="list")
def _list() -> None:
    """List configuration."""
    pprint(settings.dict(), expand_all=True, indent_guides=False)


@app.command(name="set")
def _set(key: str, value: str, scope: Scope = Scope.local) -> None:
    """Set a key value pair for configuration, e.g.
    `pyvarium set poetry_exec /opt/poetry/bin/poetry`."""
    settings.__setattr__(key, value)
    settings.write(scope)
    _list()


@app.command()
def unset(key: str, scope: Scope = Scope.local) -> None:
    """Remove a custom settings from configuration (this reverts to the default, to
    disable a default set it to an empty string, e.g. `pyvarium set poetry_exec ""`)."""
    settings.__delattr__(key)
    settings.write(scope)
    _list()


@app.command()
def info() -> None:
    """Show information about the current configuration."""

    files = settings.settings_scopes()

    pprint(
        files,
        indent_guides=False,
        expand_all=True,
    )
