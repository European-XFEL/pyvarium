from pathlib import Path
import rich
import rich.pretty
import typer

from pyvarium.config import Settings, settings, Scope
from pyvarium.config import THIS_DIR as SETTINGS_DIR

app = typer.Typer(no_args_is_help=True, help="Modify user settings for pyvarium.")


@app.command(name="list")
def _list() -> None:
    """List configuration."""
    rich.pretty.pprint(
        Settings.load_dynaconf().dict(), expand_all=True, indent_guides=False
    )


@app.command(name="set")
def _set(key: str, value: str, scope: Scope = Scope.user) -> None:
    """Set a key value pair for configuration, e.g.
    `pyvarium set poetry_exec /opt/poetry/bin/poetry`."""
    settings.__setattr__(key, value)
    s = Settings(**settings.dict())
    s.write(scope)
    _list()


@app.command()
def unset(key: str, scope: Scope = Scope.user) -> None:
    """Remove a custom settings from configuration (this reverts to the default, to
    disable a default set it to an empty string, e.g. `pyvarium set poetry_exec ""`)."""
    settings.__delattr__(key)
    s = Settings(**settings.dict())
    s.write(scope)
    _list()


@app.command()
def info() -> None:
    """Show information about the current configuration."""

    files = {
        "builtin": SETTINGS_DIR / "settings.toml",
        "user": Path("~/.config/pyvarium/settings.toml").expanduser(),
        "local": Path("./pyvarium.toml").absolute(),
    }

    rich.pretty.pprint(
        files,
        indent_guides=False,
        expand_all=True,
    )
