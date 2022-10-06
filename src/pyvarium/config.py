import shutil
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

import rtoml
from dynaconf import Dynaconf  # type: ignore
from pydantic import BaseSettings, FilePath, root_validator

THIS_DIR = Path(__file__).parent.absolute()


class Scope(str, Enum):
    user = "user"
    local = "local"


def to_snake_case(d: dict) -> dict:
    """Recursively converts the keys of a dictionary to snake_case style."""
    res = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = to_snake_case(v)

        res[k.lower().replace("-", "_")] = v

    return res


def to_str(d: dict) -> dict:
    """Recursively converts the values of a dictionary to str."""
    res = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = to_str(v)
        else:
            v = str(v)

        res[str(k)] = v

    return res


class Settings(BaseSettings):
    pipenv: Optional[FilePath]
    pipx: Optional[FilePath]
    poetry: Optional[FilePath]
    spack: Optional[FilePath]
    __dynaconf_settings__: Optional[Dynaconf]

    @root_validator
    def which_path(cls, values):
        paths = {"pipenv", "pipx", "poetry", "spack"}

        for p in paths:
            if values.get(p, None) is None:
                if _ := shutil.which(p):
                    values[p] = Path(_)

        return values

    @classmethod
    def load_dynaconf(
        cls,
        settings_files: Tuple[Path, ...] = (
            THIS_DIR / "settings.toml",
            Path("~/.config/pyvarium/settings.toml").expanduser(),
            Path("./pyvarium.toml").absolute(),
        ),
    ) -> "Settings":
        """Load configurations via Dynaconf and parse them into a Settings object."""

        cls.__dynaconf_settings__ = Dynaconf(
            includes=settings_files,
            environments=False,
        )

        # TODO: there is a planned feature for dynaconf to allow defining schemas with
        # pydantic directly, which would avoid this weird dynaconf -> dict -> dict with
        # different keys -> pydantic steps
        __dynaconf_dict__ = to_snake_case(cls.__dynaconf_settings__.to_dict())  # type: ignore

        return cls.parse_obj(__dynaconf_dict__)

    def write(self, scope: Scope = Scope.user):
        settings = self.dict()

        if scope is Scope.user:
            settings_file = Path("~/.config/pyvarium/settings.toml").expanduser()
        elif scope is Scope.local:
            settings_file = Path("./pyvarium.toml").absolute()

        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(rtoml.dumps(to_str(settings)))


settings = Settings.load_dynaconf()
