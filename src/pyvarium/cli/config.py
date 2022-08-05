import rich
import rich.pretty
import typer

from pyvarium.config import Settings, settings

app = typer.Typer(no_args_is_help=True, help="Modify user settings for pyvarium")


@app.command(name="list")
def _list() -> None:
    """List configuration"""
    rich.pretty.pprint(
        Settings.load_dynaconf().dict(), expand_all=True, indent_guides=False
    )


@app.command(name="set")
def _set(key: str, value: str) -> None:
    """Set a key value pair for configuration, e.g.
    `pyvarium set poetry_exec /opt/poetry/bin/poetry`"""
    settings.__setattr__(key, value)
    s = Settings(**settings.dict())
    s.user_write()
    _list()


@app.command()
def unset(key: str) -> None:
    """Remove a custom settings from configuration (this reverts to the default, to
    disable a default set it to an empty string, e.g. `pyvarium set poetry_exec ""`)"""
    settings.__delattr__(key)
    s = Settings(**settings.dict())
    s.user_write()
    s.user_write()
    _list()


@app.command()
def info() -> None:
    """Show information about the current configuration"""

    rich.print("Files used for configuration:")
    rich.pretty.pprint(
        list(Settings.load_dynaconf.__defaults__[0]),  # type: ignore
        indent_guides=False,
        expand_all=True,
    )
