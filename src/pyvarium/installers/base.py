import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Union

from loguru import logger
from rich.status import Status

from pyvarium.config import settings


class Program:
    executable: Path
    cwd: Path
    env: Union[Dict, os._Environ]

    def __init__(
        self,
        executable: Optional[Path] = None,
        post_init: bool = True,
        status: Optional[Status] = None,
    ):
        if status:
            original_text = status.status
            update_text = f"{original_text}: {{x}}"
            self.update_status = lambda x: status.update(update_text.format(x=x))
        else:
            self.update_status = lambda *_: None

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
        python_bin = str(Path(sys.executable).absolute().parent)
        self.persistent_path = f"{python_bin}:/usr/local/bin:/usr/bin:/bin"
        self.env["PATH"] = self.persistent_path

        if post_init:
            self.__post_init__()

    def __post_init__(self):
        ...

    def cmd(self, *args) -> subprocess.CompletedProcess:
        logger.debug(f"`{self.executable.name} {' '.join(args)}`")
        self.update_status(f"`{self.executable.name} {' '.join(args)}`")
        res = subprocess.run(
            [self.executable, *args],
            cwd=self.cwd,
            env=self.env,
            capture_output=True,
        )

        logger.debug(res)

        if res.returncode != 0:
            raise RuntimeError(f"Process return code is not 0: {res=}")

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
        self,
        path: Path,
        program: Optional[Program] = None,
        post_init: bool = True,
        status: Optional[Status] = None,
    ) -> None:
        self.path = Path(path)
        self.program = program or self.__annotations__["program"](
            post_init=post_init, status=status
        )

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
