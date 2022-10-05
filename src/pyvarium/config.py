import shutil
from pathlib import Path
from typing import Optional, Tuple

import rtoml
from dynaconf import Dynaconf
from pydantic import BaseSettings, FilePath, root_validator

THIS_DIR = Path(__file__).parent.absolute()


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

    @root_validator
    def which_path(cls, values):
        paths = {"pipenv", "pipx", "poetry", "spack"}

        for p in paths:
            if values[p] is None:
                if _ := shutil.which(p):
                    values[p] = Path(_)

        return values

    __dynaconf_settings__: Optional[Dynaconf]

    @classmethod
    def load_dynaconf(
        cls,
        settings_files: Tuple[Path, ...] = (
            THIS_DIR / "settings.toml",
            Path("~/.config/pyvarium/settings.toml").expanduser(),
        ),
    ) -> "Settings":
        """Load configurations via Dynaconf and parse them into a Settings object."""

        cls.__dynaconf_settings__ = Dynaconf(
            settings_files=settings_files,
            environments=False,
        )

        # TODO: there is a planned feature for dynaconf to allow defining schemas with
        # pydantic directly, which would avoid this weird dynaconf -> dict -> dict with
        # different keys -> pydantic steps
        __dynaconf_dict__ = to_snake_case(cls.__dynaconf_settings__.to_dict())  # type: ignore

        return cls.parse_obj(__dynaconf_dict__)

    def user_write(self):
        settings = self.dict()

        settings_file = Path("~/.config/pyvarium/settings.toml").expanduser()
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        s = to_str(settings)
        settings_file.write_text(rtoml.dumps(s))


settings = Settings.load_dynaconf()
