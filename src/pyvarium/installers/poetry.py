import os
import subprocess
import urllib.request
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Union

from fastcore.meta import delegates
from loguru import logger

from .base import Installer


class Poetry(Installer):
    """Poetry installer class, used to manage the poetry installation itself as well as
    poetry environments.
    """

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
            executable = Path(prefix) / "bin" / "poetry"

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
            self.config_path = self.env_path / "pyproject.toml"

    def cmd(
        self,
        cmd: str,
        *,
        cwd: Optional[Path] = None,
        prepend: Optional[str] = None,
        environ: Optional[Union[Dict, os._Environ]] = None,
    ) -> subprocess.CompletedProcess:
        """Executes a command with Poetry.

        Args:
            cmd (str): Command string to execute.
            env_path (Optional[Path], optional): Directory the environment is in, cwd is
                set to this path, if cwd and env are set **cwd takes precedence**.
                Defaults to None.
            cwd (Optional[Path], optional): Directory to execute command in - **should
                be the directory of the environment**. Defaults to None.
            prepend (Optional[str], optional): String to prepend to the command.
                Defaults to None.
            environ (Optional[dict], optional): Set environment variables. Defaults to
                None (empty dict).

        Returns:
            subprocess.CompletedProcess: Returned process object.
        """
        cmd = f"{self.installer_config.executable} {cmd}"

        if self.env_path and cwd:
            logger.warning("Both env and cwd are set, only cwd will be used.")

        if prepend:
            cmd = f"{prepend} {cmd}"

        environ = environ or {}

        process = subprocess.run(
            cmd,
            env=environ,
            cwd=cwd or self.env_path,
            shell=True,
            capture_output=True,
            executable="/bin/bash",
        )

        logger.debug(f"{process=}")
        process.check_returncode()

        return process

    @classmethod
    def setup(
        cls,
        prefix: Path,
        url: str = "https://install.python-poetry.org",
        preview_version: bool = False,
    ) -> subprocess.CompletedProcess:
        logger.info("Starting Poetry setup")
        script = NamedTemporaryFile()

        logger.debug(f"Downloading {url} to {script.name}")

        with urllib.request.urlopen(url) as response:
            script.write(response.read())

        preview_str = " --preview" if preview_version else ""

        cmd = f"POETRY_HOME={prefix.absolute()} python3 {script.name}{preview_str}"
        logger.debug(f"Running: {cmd}")

        process = subprocess.run(cmd, shell=True, capture_output=True)
        logger.debug(process)

        process.check_returncode()
        logger.info("Completed Poetry setup")

        return process

    @classmethod
    @delegates(cmd)
    def env_create(
        cls,
        env_path: Path,
        prefix: Optional[Union[Path, str]] = None,
        executable: Optional[Union[Path, str]] = None,
        force: bool = False,
        protected: bool = True,
        venv_create: bool = False,
        in_project: bool = True,
        **kwargs,
    ) -> "Poetry":
        """Create a new Poetry environment.

        Args:
            env_path (Path): Directory the environment is in, cwd is set to this path,
                if cwd and env are set **cwd takes precedence**. Defaults to None.
            executable (Path, optional): Path to the poetry executable to use. Defaults
                to settings.poetry_root/"bin"/"poetry".
            venv_create (bool, optional): Poetry flag to create venvs. Defaults to False.
            in_project (bool, optional): Poetry flag to create venv in project. Defaults
                to True.
            prepend (Optional[str], optional): String to prepend to the command.
                Defaults to None.
            environ (Optional[dict], optional): Set environment variables. Defaults to
                None (empty dict).

        Returns:
            installers.Poetry: Poetry object.
        """
        poetry = cls("use", prefix, executable, protected, env_path)

        if not env_path.is_dir():
            env_path.mkdir(parents=True)

        poetry.set_config("virtualenvs.create", str(venv_create).lower())
        poetry.set_config("virtualenvs.in-project", str(in_project).lower())
        poetry.set_config("cache-dir", str(poetry.installer_config.prefix / "cache"))

        poetry.cmd("init --no-interaction", **kwargs)

        return poetry

    @classmethod
    def env_load(
        cls,
        env_path: Path,
        protected: bool = True,
    ) -> "Poetry":
        pyproject = cls._pyproject(env_path)

        poetry_executable = Path(pyproject.tool.pyvarium.poetry.executable)

        if not poetry_executable.exists():
            raise RuntimeError(f"Spack executable `{poetry_executable}` not found")

        return cls("use", None, poetry_executable, protected, env_path)

    def add(
        self,
        packages: List[str],
        lock: bool = False,
        **kwargs,
    ) -> subprocess.CompletedProcess:
        """Add a package to the Poetry environment.

        Args:
            package (str): Package(s) to add to the environment.
            env_path (Path): Directory the environment is in, cwd is set to this path,
                if cwd and env are set **cwd takes precedence**.
            lock (bool, optional): Poetry lock flag. Defaults to False.
            cwd (Optional[Path], optional): Directory to execute command in - **should
                be the directory of the environment**. Defaults to None.
            prepend (Optional[str], optional): String to prepend to the command.
                Defaults to None.
            environ (Optional[dict], optional): Set environment variables. Defaults to
                None (empty dict).

        Returns:
            subprocess.CompletedProcess: Returned process object.
        """
        cmd = f"add {' '.join(packages)}{' --lock' if lock else ''}"

        return self.cmd(cmd, **kwargs)

    @delegates(cmd)
    def install(
        self,
        **kwargs,
    ) -> Dict[str, subprocess.CompletedProcess]:
        """Install a poetry environment.

        Args:
            env_path (Optional[Path], optional): Directory the environment is in, cwd is
                set to this path, if cwd and env are set **cwd takes precedence**.
                Defaults to None.
            prepend (Optional[str], optional): String to prepend to command. Defaults to None.
            cwd (Optional[Path], optional): Directory to execute command in - **should
                be the directory of the environment**. Defaults to None.
            prepend (Optional[str], optional): String to prepend to the command.
                Defaults to None.
            environ (Optional[dict], optional): Set environment variables. Defaults to
                None (empty dict).

        Returns:
            subprocess.CompletedProcess: Returned process object.
        """
        lock = self.cmd("lock --no-update", **kwargs)

        install = self.cmd(
            "install --no-root",
            **kwargs,
        )

        return {"lock": lock, "install": install}

    @delegates(cmd)
    def set_config(
        self,
        key: str,
        value: str,
        local: Optional[bool] = True,
        **kwargs,
    ):
        """Set a configuration, calls poetry `config ...` command.

        Args:
            key (str): Key to set.
            value (str): Value to set key to.
            local (Optional[bool], optional): Add local flag to config command call.
                Defaults to True.
            env_path (Optional[Path], optional): Directory the environment is in, cwd is
                set to this path, if cwd and env are set **cwd takes precedence**.
                Defaults to None.
            prepend (Optional[str], optional): String to prepend to command. Defaults to
                None.
            cwd (Optional[Path], optional): Directory to execute command in - **should
                be the directory of the environment**. Defaults to None.
            prepend (Optional[str], optional): String to prepend to the command.
                Defaults to None.
            environ (Optional[dict], optional): Set environment variables. Defaults to
                None (empty dict).

        Returns:
            subprocess.CompletedProcess: Returned process object.
        """
        return self.cmd(
            cmd=f"config {'--local ' if local else ' '}{key} {value}", **kwargs
        )

    @property
    def version(self) -> str:
        """Return the version of the spack instance."""
        return self.cmd("--version").stdout.decode().strip()
