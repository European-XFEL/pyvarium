import os
import subprocess
from abc import ABC, abstractclassmethod, abstractmethod, abstractproperty
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from box import Box
from loguru import logger


@dataclass
class InstallerConfig:
    action: str
    prefix: Path
    executable: Path
    installed: bool
    protected: bool


class Installer(ABC):
    def __init__(
        self,
        action: str,
        prefix: Path,
        executable: Path,
        protected: Optional[bool] = None,
        pyvarium_env_path: Optional[Path] = None,
        pyvarium_env_name: Optional[str] = None,
    ) -> None:
        self.installer_config = InstallerConfig(
            action=action,
            prefix=prefix,
            executable=executable,
            installed=executable.exists(),
            protected=protected or action == "use",
        )

        self.env_path = pyvarium_env_path
        self.env_name = pyvarium_env_name

        logger.trace(f"{self.__class__.__name__} config: {self}")

    @classmethod
    def _pyproject(cls, env_path: Path) -> Box:
        if not env_path:
            raise RuntimeError("No pyvarium env_path set")

        return Box.from_toml(
            (env_path / "pyproject.toml").read_text(),
            frozen_box=True,
            default_box=False,
        )

    @abstractmethod
    def cmd(
        self,
        cmd: str,
        *,
        cwd: Optional[Path],
        prepend: Optional[str],
        environ: Optional[Union[Dict, os._Environ]],
    ) -> subprocess.CompletedProcess:
        pass

    @abstractclassmethod
    def setup(cls, prefix: Path, version: str) -> None:
        pass

    @abstractclassmethod
    def env_create(cls):
        pass

    @abstractclassmethod
    def env_load(cls, env_path: Path, protected: bool):
        pass

    @abstractmethod
    def add(self, packages: List[str]):
        pass

    @abstractmethod
    def install(self):
        pass

    @abstractproperty
    def version(self):
        pass
