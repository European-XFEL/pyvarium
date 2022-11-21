import shutil
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple

import rtoml
from dynaconf import Dynaconf  # type: ignore
from pydantic import BaseSettings, FilePath, root_validator

THIS_DIR = Path(__file__).parent.absolute()


class Scope(str, Enum):
    builtin = "builtin"
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

    @staticmethod
    def settings_scopes() -> Dict[Scope, Path]:
        return {
            Scope.builtin: THIS_DIR / "settings.toml",
            Scope.user: Path("~/.config/pyvarium/settings.toml").expanduser(),
            Scope.local: Path("./pyvarium.toml").absolute(),
        }

    @classmethod
    def load_dynaconf(cls) -> "Settings":
        """Load configurations via Dynaconf and parse them into a Settings object."""

        cls.__dynaconf_settings__ = Dynaconf(
            includes=list(cls.settings_scopes().values()),
            environments=False,
        )

        # TODO: there is a planned feature for dynaconf to allow defining schemas with
        # pydantic directly, which would avoid this weird dynaconf -> dict -> dict with
        # different keys -> pydantic steps
        __dynaconf_dict__ = to_snake_case(cls.__dynaconf_settings__.to_dict())  # type: ignore

        return cls.parse_obj(__dynaconf_dict__)

    def write(self, scope: Scope = Scope.local):
        settings = self.dict()
        target = self.settings_scopes()[scope].expanduser().absolute()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rtoml.dumps(to_str(settings)))


settings = Settings.load_dynaconf()
