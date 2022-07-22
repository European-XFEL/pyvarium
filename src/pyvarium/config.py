from pathlib import Path

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="PYVARIUM",
    settings_files=[(Path(__file__).parent / "settings.toml")],
    environments=False,
)

settings.poetry_prefix = Path(settings.poetry_prefix)  # type: ignore
settings.spack_prefix = Path(settings.spack_prefix)  # type: ignore

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load this files in the order.
