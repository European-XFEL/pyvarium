import json
import os
import subprocess
from contextlib import contextmanager
from functools import partial
from multiprocessing import Pool, current_process
from pathlib import Path
from typing import Dict, List, Optional, Union

import pyaml
from box import Box
from fastcore.meta import delegates
from loguru import logger

from .base import Installer

sync_hook = """
import llnl.util.tty as tty


def on_install_success(spec):
    tty.info()
"""


class Spack(Installer):
    def __init__(
        self,
        action: str,
        prefix: Optional[Union[Path, str]] = None,
        executable: Optional[Union[Path, str]] = None,
        protected: Optional[bool] = None,
        pyvarium_env_path: Optional[Union[Path, str]] = None,
        pyvarium_env_name: Optional[str] = None,
    ) -> None:
        if not prefix and not executable:
            raise ValueError("Either prefix or executable must be specified")

        if prefix and executable and Path(executable).parent.parent != prefix:
            raise RuntimeError("Executable must be in the same directory as prefix")

        if prefix and not executable:
            executable = Path(prefix) / "bin" / "spack"

        if executable and not prefix:
            prefix = Path(executable).parent.parent

        super().__init__(
            action,
            prefix,  # type: ignore
            executable,  # type: ignore
            protected=protected,
            pyvarium_env_path=Path(pyvarium_env_path) if pyvarium_env_path else None,
            pyvarium_env_name=pyvarium_env_name,
        )

        if self.env_path:
            self.config_path = self.env_path / "spack.yaml"

    @classmethod
    def setup(
        cls,
        prefix: Path,
        version: str = "develop",
        e4s: bool = False,
    ) -> None:
        logger.info("Starting Spack setup")

        if e4s and "e4s" not in version:
            logger.info("Setting version to e4s-22.02")
            version = "e4s-22.02"

        cmd = (
            "git clone https://github.com/spack/spack.git --depth 1 --branch "
            f"{version} {prefix}"
        )
        logger.debug(f"Running {cmd}")

        process = subprocess.run(cmd, shell=True, check=True, capture_output=True)
        logger.debug(process)

        if e4s:
            cmd = f"{prefix}/bin/spack mirror add E4S https://cache.e4s.io/22.02"

        logger.info("Completed Spack setup")

    def cmd(
        self,
        cmd: str,
        *,
        cwd: Optional[Path] = None,
        prepend: Optional[str] = None,
        environ: Optional[Union[Dict, os._Environ]] = os.environ,
        no_env: bool = False,
    ) -> subprocess.CompletedProcess:
        """Execute a command with Spack

        Args:
            cmd (str): Command string to execute.
            env (Optional[Path], optional): Directory the environment is in, will be
                loaded with `spack -D {env}`. Defaults to None.
            cwd (Optional[Path], optional): Directory to execute the command in.
                Defaults to None.
            prepend (Optional[str], optional): String to prepend to the command.
                Defaults to None.
            environ (Optional[dict], optional): Set environment variables. Defaults to
                None (empty dict).

        Returns:
            subprocess.CompletedProcess: Returned process object.
        """
        e = f" -D {self.env_path} " if self.env_path else " "
        e = " " if no_env else e
        cmd = f"{self.installer_config.executable}{e}{cmd}"

        if prepend:
            cmd = f"{prepend} {cmd}"

        environ = environ or {}

        process = subprocess.run(
            cmd,
            env=environ,
            cwd=cwd,
            shell=True,
            check=False,
            capture_output=True,
            executable="/bin/bash",
        )

        logger.debug(f"{process=}")
        process.check_returncode()

        return process

    def cmd_mp(
        self,
        cmd: str,
        *,
        cwd: Optional[Path] = None,
        prepend: Optional[str] = None,
        environ: Optional[Union[Dict, os._Environ]] = os.environ,
        no_env: bool = False,
    ) -> subprocess.CompletedProcess:
        e = f" -D {self.env_path} " if self.env_path else " "
        e = " " if no_env else e
        cmd = f"{self.installer_config.executable}{e}{cmd}"

        if prepend:
            cmd = f"{prepend} {cmd}"

        environ = environ or {}

        process_id = int(current_process().name.split("-")[-1])

        log_level = f"SPACK-{process_id:02}"
        self.logger = logger.bind(id=process_id)
        self.logger.level(log_level, no=20, color="<green>")
        self.logger.log(log_level, cmd)

        process = subprocess.Popen(
            cmd,
            env=environ,
            cwd=cwd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            executable="/bin/bash",
        )

        self.logger.log(log_level, f"{process=}")

        while process.poll() is None:
            for line in iter(process.stdout.readline, b""):  # type: ignore
                line_str = line.decode().strip()
                if "[+]" not in line_str:
                    self.logger.log(log_level, line_str)

        res = subprocess.CompletedProcess(
            process.args,
            process.returncode,
            process.stdout.readlines(),  # type: ignore
            process.stderr.readlines(),  # type: ignore
        )

        self.logger.log(log_level, f"{res=}")

        return res

    @contextmanager
    def config(self):
        """Convenience function to handle loading and saving the spack configuration
        file in a context manager."""
        config = Box.from_yaml(self.config_path.read_text())
        try:
            yield config
        finally:
            pyaml.dump(config.to_dict(), self.config_path.open("w"))

    @property
    def _config(self) -> Box:
        """Returns a frozen Box object with the configuration of spack so that it is not
        edited accidentally, the `_spack_config` context manager should be used if the
        config will be modified"""
        return Box.from_yaml(self.config_path.read_text(), frozen_box=True)

    @classmethod
    @delegates(cmd)
    def env_create(
        cls,
        env_path: Path,
        prefix: Optional[Union[Path, str]] = None,
        executable: Optional[Union[Path, str]] = None,
        # force: bool = False,
        protected: bool = True,
        # no_env: bool = True,
        concretization: str = "together",
        **kwargs,
    ) -> "Spack":
        spack = cls("create", prefix, executable, protected, env_path)
        cmd = f"env create -d {env_path} --with-view {env_path / 'venv'}"

        spack.cmd(cmd, no_env=True, **kwargs)

        spack.cmd("config add 'packages:all:target:[x86_64]'")

        spack._set_concretization(concretization)

        return spack

    @classmethod
    def env_load(
        cls,
        env_path: Path,
        protected: bool = True,
    ) -> "Spack":
        pyproject = cls._pyproject(env_path)

        spack_executable = Path(pyproject.tool.pyvarium.spack.executable)

        if not spack_executable.exists():
            raise RuntimeError(f"Spack executable `{spack_executable}` not found")

        return cls("use", None, spack_executable, protected, env_path)

    def add(self, packages: List[str]):
        """Add packages to spack environment"""

        self.cmd(f"add {' '.join(packages)}")

    @delegates(cmd)
    def install(self, processes: int = 0, **kwargs):
        if processes <= 1:
            return self.cmd("install", **kwargs)

        logger.info(f"Running install with {processes} processes")
        with Pool(processes) as pool:
            logger.debug(f"Pool info: {pool}")
            res = [
                pool.apply_async(partial(self.cmd_mp, "install", **kwargs))
                for _ in range(processes)
            ]

            [logger.trace(r.get()) for r in res]

    @delegates(cmd)
    def concretize(self, **kwargs):
        """Concretize the spack environment"""

        self.cmd("concretize", **kwargs)

    def list_python_packages(self, cwd: Optional[Path] = None) -> list:
        """Lists the python packages present in the spack environment"""

        cmd = "PYTHONNOUSERSITE=True venv/bin/python -m pip list --format json"
        res = subprocess.run(
            cmd, shell=True, capture_output=True, cwd=cwd or self.env_path
        )

        return json.loads(res.stdout.decode().strip())

    def _set_concretization(self, concretization: str) -> None:
        """Set the concretization setting for the environment"""
        with self.config() as config:
            if concretization in {"together", "individual"}:
                config.spack.concretization = concretization  # type: ignore
            else:
                raise RuntimeError(
                    f"Invalid concretization: {concretization}, must be 'together' or "
                    "'individual'"
                )

    @property
    def version(self) -> str:
        """Return the version of the spack instance."""
        return self.cmd("--version", no_env=True).stdout.decode().strip()
