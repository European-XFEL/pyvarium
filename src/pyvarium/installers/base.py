import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Union

from loguru import logger

from pyvarium.config import settings


class Program:
    executable: Path
    cwd: Path
    env: Union[Dict, os._Environ]

    def __init__(self, executable: Optional[Path] = None, post_init: bool = True):
        if executable is None:
            executable = settings.__getattribute__(self.__class__.__name__.lower())

        if executable is None:
            raise ValueError(f"{self.__class__.__name__} executable not found")

        self.executable = Path(executable)

        self.cwd = Path.cwd()
        self.env = os.environ.copy()
        self.env.clear()
        # FIX: something somewhere in pipenv/python test PATH to `None`, which then
        # causes an exception in `subprocess.run`
        self.env["PATH"] = "/bin:/usr/bin"

        if post_init:
            self.__post_init__()

    def __post_init__(self):
        ...

    def cmd(self, *args) -> subprocess.CompletedProcess:
        res = subprocess.run(
            [self.executable, *args],
            cwd=self.cwd,
            env=self.env,
            capture_output=True,
        )
        logger.debug(res.stderr.decode())
        logger.debug(res.stdout.decode())
        return res

    def config(self):
        ...

    @property
    def version(self) -> str:
        out = self.cmd("--version").stdout

        if type(out) is bytes:
            return out.decode().strip()
        else:
            return out.strip()


class Environment:
    program: Program

    def __init__(
        self, path: Path, program: Optional[Program] = None, post_init: bool = True
    ) -> None:
        self.path = Path(path)
        self.program = program or self.__annotations__["program"]()

        if post_init:
            self.__post_init__()

    def __post_init__(self):
        ...

    def cmd(self, *args) -> subprocess.CompletedProcess:
        ...

    def new(self):
        ...

    def add(self, packages: list):
        ...

    def install(self):
        ...

    def get_config(self) -> dict:
        ...

    def set_config(self, config: dict):
        ...

    def sync(self):
        ...
